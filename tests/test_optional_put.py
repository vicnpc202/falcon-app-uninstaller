import hashlib
import importlib.util
import json
import sqlite3
import tempfile
import unittest
from pathlib import Path
from types import SimpleNamespace

spec=importlib.util.spec_from_file_location('optional_put',Path(__file__).resolve().parents[1]/'gestor.py')
m=importlib.util.module_from_spec(spec)
spec.loader.exec_module(m)
BINDING={'id':'put-one','name':'BSTCleaner_native.exe','sha256':'a'*64}

class Fake:
    def __init__(self):
        self.calls=[]
        self.reply={'complete':True,'stdout':'GF_PUT_MISSING\n'}
        self.queued=True
        self.changed=False
        self.session_id='same-session'
    def verify(self, script): pass
    def verify_put(self, binding):
        if self.changed: raise ValueError('File changed')
        assert binding==BINDING
    def session(self, job): return {'session_id':self.session_id,'offline_queued':self.queued}
    def submit(self, job, session):
        self.calls.append((job['phase'],session,job['put_file']))
        return {'cloud_request_id':str(len(self.calls)),'queued_command_offline':self.queued}
    def status(self, job): return self.reply

class PutTests(unittest.TestCase):
    def setUp(self):
        temp_root=Path(__file__).resolve().parent/'test-temp'
        temp_root.mkdir(exist_ok=True)
        self.temp=tempfile.TemporaryDirectory(dir=temp_root)
        assert Path(self.temp.name).resolve().is_relative_to(temp_root.resolve())
        self.path=Path(self.temp.name)/'db.sqlite3'
        self.db=m.db_open(self.path)
        self.db.execute("INSERT INTO app(id,name,vendor,platform,script) VALUES(1,'BlueStacks','Demo','Windows','script')")
        self.db.execute("INSERT INTO inventory(app_id,host_key,aid,hostname,installed) VALUES(1,'host','host','PC',1)")
        self.db.commit()
        self.service=Fake()
    def tearDown(self):
        self.db.close()
        self.temp.cleanup()
    def plan(self,enabled=True):
        if enabled: m.save_put_binding(self.db,1,BINDING)
        self.ids=m.plan(self.db,1,['host'],True,'campaign')
    def job(self): return self.db.execute('SELECT * FROM job').fetchone()
    def dispatch(self): m.dispatch(self.db,self.service,self.ids,lambda _:None)
    def poll(self): m.poll(self.db,self.service,lambda _:None)
    def test_phases_order_hash_and_restart(self):
        self.plan()
        self.dispatch()
        self.assertEqual(self.job()['phase'],'put_probe')
        self.assertEqual(self.job()['status'],'En cola')
        self.db.close()
        self.db=m.db_open(self.path)
        self.service.reply={'complete':False,'stdout':''}
        self.poll()
        self.assertEqual(len(self.service.calls),1)
        self.service.reply={'complete':True,'stdout':'GF_PUT_MISSING\n'}
        self.poll()
        self.assertEqual(self.job()['phase'],'put_cd')
        self.service.reply={'complete':True,'stdout':'C:\\'}
        self.poll()
        self.assertEqual(self.job()['phase'],'put_copy')
        self.service.reply={'complete':True,'stdout':'Operation completed successfully.'}
        self.poll()
        self.assertEqual(self.job()['phase'],'put_check')
        self.assertEqual(self.job()['output'],'')
        self.service.reply={'complete':True,'stdout':'GF_PUT_OK:'+BINDING['sha256']+'\n'}
        self.poll()
        self.assertEqual(self.job()['phase'],'script')
        self.assertEqual(self.job()['seq'],0)
        self.service.reply={'complete':True,'stdout':'APP_ABSENT\n'}
        self.poll()
        self.assertEqual(self.job()['status'],'Ausencia confirmada por script')
        self.assertEqual([c[0] for c in self.service.calls],['put_probe','put_cd','put_copy','put_check','script'])
        self.assertEqual({c[1] for c in self.service.calls},{'same-session'})
    def test_copy_error_never_launches_script(self):
        self.plan(); self.dispatch(); self.poll(); self.poll()
        self.service.reply={'complete':True,'stdout':'','stderr':'File already exists'}
        self.poll()
        self.assertEqual(self.job()['status'],'Error')
        self.assertEqual(len(self.service.calls),3)
    def test_wrong_hash_or_absence_token_never_launches_script(self):
        self.plan(); self.dispatch(); self.poll(); self.poll(); self.poll()
        self.service.reply={'complete':True,'stdout':'APP_ABSENT\n'}
        self.poll()
        self.assertEqual(self.job()['status'],'Error')
        self.assertEqual(len(self.service.calls),4)
    def test_changed_file_blocked_before_any_command(self):
        self.plan(); self.service.changed=True; self.dispatch()
        self.assertEqual(self.job()['status'],'Error')
        self.assertFalse(self.service.calls)
    def test_changed_file_blocked_between_phases(self):
        self.plan(); self.dispatch(); self.service.changed=True; self.poll()
        self.assertEqual(self.job()['status'],'Error')
        self.assertEqual(len(self.service.calls),1)
    def test_ambiguous_submission_not_retried(self):
        self.plan(); self.dispatch()
        def timeout(*_): raise TimeoutError('Result unknown')
        self.service.submit=timeout
        self.poll()
        self.assertEqual(self.job()['status'],'Revisar en Falcon')
        self.poll()
        self.assertEqual(len(self.service.calls),1)
    def test_disabled_preserves_legacy_commands(self):
        self.plan(False); self.dispatch()
        self.assertEqual(self.service.calls,[('script','same-session','')])
        self.service.reply={'complete':True,'stdout':'APP_ABSENT\n'}
        self.poll()
        self.assertEqual(self.job()['status'],'Ausencia confirmada por script')
    def test_config_is_per_application_and_immutable_in_existing_jobs(self):
        self.plan()
        self.db.execute("INSERT INTO app(id,name,platform) VALUES(2,'Other','Windows')")
        self.db.commit()
        self.assertIsNone(m.get_put_binding(self.db,2))
        m.save_put_binding(self.db,1,None)
        self.assertIsNone(m.get_put_binding(self.db,1))
        self.assertEqual(m.job_put_binding(self.job()),BINDING)
        self.db.close(); self.db=m.db_open(self.path)
        self.assertEqual(self.job()['phase'],'put_probe')
    def test_active_policy_prevents_silent_attachment_change(self):
        self.db.execute("INSERT INTO policy VALUES(1,'script',1)")
        self.db.commit()
        with self.assertRaises(ValueError): m.save_put_binding(self.db,1,BINDING)
    def test_invalid_names_and_hashes(self):
        for name in ('../test.exe','C:\\test.exe','"file.exe"',"bad'file.exe",'a`b.exe','a\nb.exe'):
            with self.subTest(name=name), self.assertRaises(ValueError):
                m.put_file_binding(dict(BINDING,name=name))
        with self.assertRaises(ValueError): m.put_file_binding(dict(BINDING,sha256='bad'))
    def test_api_commands_and_remote_file_identity(self):
        calls=[]
        service=m.Falcon.__new__(m.Falcon)
        service.admin=SimpleNamespace(
            execute_admin_command=lambda **kw:(calls.append(kw) or {'status_code':201,'body':{'resources':[{}]}}),
            get_put_files=lambda **kw:{'status_code':200,'body':{'resources':[BINDING]}})
        service.verify_put(BINDING)
        self.plan()
        row=dict(self.job())
        for phase in ('put_probe','put_cd','put_copy','put_check','script'):
            row['phase']=phase
            service.submit(row,'same-session')
        self.assertIn('GF_PUT_MISSING',calls[0]['command_string'])
        self.assertEqual(calls[1]['command_string'],'cd C:\\')
        self.assertEqual(calls[2]['command_string'],'put "BSTCleaner_native.exe"')
        self.assertIn("C:\\BSTCleaner_native.exe",calls[3]['command_string'])
        self.assertIn('GF_PUT_OK:'+BINDING['sha256'],calls[3]['command_string'])
        self.assertEqual(calls[4]['command_string'],'runscript -CloudFile="script" -Timeout=180')
        self.assertTrue(all(c['persist'] for c in calls))
        with self.assertRaises(ValueError): service.verify_put(dict(BINDING,sha256='b'*64))
    def test_library_pages_and_repeat_detection(self):
        requested=[]
        service=m.Falcon.__new__(m.Falcon)
        def page(**kw):
            requested.append(kw['offset'])
            return {'status_code':200,'body':{'resources':['one'] if kw['offset']=='0' else ['two'],
                    'meta':{'pagination':{'total':2,'limit':1,'offset':kw['offset']}}}}
        service.admin=SimpleNamespace(list_put_files=page,get_put_files=lambda **kw:{'status_code':200,'body':{'resources':[dict(BINDING,id=kw['ids'][0])]}})
        self.assertEqual(len(service.library_put_files()),2)
        self.assertEqual(requested,['0','1'])
        service.admin.list_put_files=lambda **kw:{'status_code':200,'body':{'resources':['one'],'meta':{'pagination':{'total':2,'limit':1}}}}
        with self.assertRaises(ValueError): service.library_put_files()
    def test_old_database_migration_retains_jobs(self):
        self.db.close()
        legacy=Path(self.temp.name)/'legacy.sqlite3'
        conn=sqlite3.connect(legacy)
        conn.execute("CREATE TABLE job(id INTEGER PRIMARY KEY,campaign TEXT,app_id INTEGER,aid TEXT,hostname TEXT,script TEXT,offline INTEGER,status TEXT,session TEXT DEFAULT '',request TEXT DEFAULT '',seq INTEGER DEFAULT 0,output TEXT DEFAULT '',detail TEXT DEFAULT '',updated TEXT)")
        conn.execute("INSERT INTO job(id,status,script) VALUES(1,'En cola','old-script')")
        conn.commit();conn.close()
        self.db=m.db_open(legacy)
        self.assertEqual(self.job()['phase'],'script')
        self.assertEqual(self.job()['status'],'En cola')
        self.assertEqual(self.job()['put_file'],'')

    def test_matching_file_skips_copy_but_not_verification(self):
        self.plan();self.dispatch()
        self.service.reply={'complete':True,'stdout':'GF_PUT_OK:'+BINDING['sha256']+'\n'}
        self.poll()
        self.assertEqual([c[0] for c in self.service.calls],['put_probe','script'])

    def test_unrecognized_probe_never_starts_transfer_or_script(self):
        self.plan();self.dispatch()
        self.service.reply={'complete':True,'stdout':'APP_ABSENT\n'}
        self.poll()
        self.assertEqual(self.job()['status'],'Error')
        self.assertEqual(len(self.service.calls),1)

    def test_expired_session_repeats_cd_before_copying(self):
        self.plan();self.dispatch();self.poll()
        self.assertEqual(self.job()['phase'],'put_cd')
        self.service.session_id='new-session'
        self.poll()
        self.assertEqual(self.job()['phase'],'put_cd')
        self.assertEqual(self.service.calls[-1][1],'new-session')
        self.poll()
        self.assertEqual(self.job()['phase'],'put_copy')
        self.assertEqual(self.service.calls[-1][1],'new-session')

if __name__=='__main__': unittest.main(verbosity=2)
