import hashlib
import importlib.util
import json
import tempfile
import unittest
from pathlib import Path
from types import SimpleNamespace

ROOT = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location('picker_app', ROOT/'gestor.py')
app = importlib.util.module_from_spec(spec)
spec.loader.exec_module(app)


class ScriptPickerTests(unittest.TestCase):
    def record(self, **changes):
        content = 'Write-Output "APP_ABSENT"\r\n'
        result = dict(id='script-one', name='Desinstalar Wireshark', platform=['windows'],
                      content=content, sha256=hashlib.sha256(content.encode()).hexdigest())
        result.update(changes)
        return result

    def test_remote_content_platform_and_hash_are_checked(self):
        record = self.record()
        source, binding = app.rtr_script_binding(record, 'Windows')
        self.assertEqual(source, record['content'])
        self.assertEqual(binding['id'], 'script-one')
        for changes in (dict(platform=['linux']), dict(platform=[]), dict(content='changed'),
                        dict(sha256=''), dict(id=''), dict(name='Bad" -Raw=command')):
            with self.subTest(changes=changes), self.assertRaises(ValueError):
                app.rtr_script_binding(self.record(**changes), 'Windows')

    def test_two_versions_reuse_one_remote_script_after_reopening(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp)/'test.sqlite3'
            db = app.db_open(path)
            service = SimpleNamespace(script_bindings={})
            source, binding = app.rtr_script_binding(self.record(), 'Windows')
            for key, name in ((1, 'Wireshark 4.0'), (2, 'Wireshark 4.6')):
                db.execute("INSERT INTO app(id,name,vendor,platform) VALUES(?,?,?,?)",
                           (key, name, 'Wireshark', 'Windows'))
                row = db.execute('SELECT * FROM app WHERE id=?', (key,)).fetchone()
                self.assertEqual(app.save_uninstaller(db, service, row, source, binding), binding['name'])
            self.assertEqual(db.execute('SELECT COUNT(*) FROM job').fetchone()[0], 0)
            db.close()
            db = app.db_open(path)
            self.assertEqual([r[0] for r in db.execute('SELECT script FROM app ORDER BY id')], [binding['name']]*2)
            self.assertEqual([json.loads(r[0]) for r in db.execute("SELECT value FROM meta WHERE key LIKE 'rtr_binding:%'")],
                             [binding]*2)
            db.close()

    def test_editing_remote_content_detaches_binding_and_policy_blocks_replacement(self):
        with tempfile.TemporaryDirectory() as tmp:
            db = app.db_open(Path(tmp)/'test.sqlite3')
            db.execute("INSERT INTO app(id,name,vendor,platform) VALUES(1,'Wireshark','Wireshark','Windows')")
            row = db.execute('SELECT * FROM app WHERE id=1').fetchone()
            service = SimpleNamespace(script_bindings={})
            source, binding = app.rtr_script_binding(self.record(), 'Windows')
            app.save_uninstaller(db, service, row, source, binding)
            db.execute('INSERT INTO policy VALUES(?,?,?)', (1, binding['name'], 0))
            db.commit()
            with self.assertRaises(ValueError):
                app.save_uninstaller(db, service, row, source+'# changed', binding)
            self.assertEqual(db.execute('SELECT script FROM app').fetchone()[0], binding['name'])
            db.execute('DELETE FROM policy')
            app.save_uninstaller(db, service, row, source+'# changed', binding)
            self.assertNotEqual(db.execute('SELECT script FROM app').fetchone()[0], binding['name'])
            self.assertIsNone(db.execute("SELECT value FROM meta WHERE key='rtr_binding:1'").fetchone())
            db.close()

    def test_linked_script_verification_uses_remote_id_and_rejects_changes(self):
        service = app.Falcon.__new__(app.Falcon)
        record = self.record()
        _, binding = app.rtr_script_binding(record, 'Windows')
        service.script_bindings = {binding['name']:binding}
        calls = []
        def get_scripts_v2(**kwargs):
            calls.append(kwargs)
            return {'status_code':200, 'body':{'resources':[record]}}
        service.admin = SimpleNamespace(get_scripts_v2=get_scripts_v2)
        service.verify(binding['name'])
        self.assertEqual(calls, [{'ids':['script-one']}])
        record['sha256'] = '0'*64
        with self.assertRaises(ValueError):
            service.verify(binding['name'])


if __name__ == '__main__':
    unittest.main()
