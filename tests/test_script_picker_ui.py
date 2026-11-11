import hashlib
import importlib.util
import tempfile
import time
import sys
import unittest
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location('geometry_app', ROOT/'gestor.py')
m = importlib.util.module_from_spec(spec)
spec.loader.exec_module(m)

def widgets(parent):
    for child in parent.winfo_children():
        yield child
        yield from widgets(child)

class GeometryTests(unittest.TestCase):
    def test_picker_actions_remain_visible_and_can_link_at_different_scales(self):
        for scale in (1.333, 1.667, 2.0):
            with self.subTest(scale=scale), tempfile.TemporaryDirectory() as temp:
                folder = Path(temp)/'datos'
                folder.mkdir()
                db = m.db_open(folder/'test.sqlite3')
                db.execute("INSERT INTO app(id,name,vendor,platform,category) VALUES(1,'Wireshark 4.2.4','Wireshark','Windows','Utilidades')")
                db.execute("INSERT INTO inventory(app_id,host_key,aid,hostname,installed) VALUES(1,'test','test','PC-DEMO',1)")
                db.execute('INSERT INTO meta VALUES(?,?)', ('sync',m.now()))
                db.execute('INSERT INTO meta VALUES(?,?)', ('applications_scope','application'))
                db.commit()
                db.close()
                root = m.create_root()
                root.withdraw()
                root.tk.call('tk','scaling',scale)
                panel = None
                errors = []
                root.report_callback_exception = lambda *args: errors.append(str(args[1]))
                try:
                    panel = m.Panel(root,folder/'test.sqlite3',m.Demo())
                    for timer in root.tk.call('after','info'):
                        if root.tk.call('after','info',timer)[0] in root._tclCommands:
                            root.after_cancel(timer)
                    source = 'Write-Output "APP_ABSENT"'
                    record = dict(id='test-script', name='Desinstalar Wireshark',platform=['windows'],
                                  content=source,sha256=hashlib.sha256(source.encode()).hexdigest())
                    panel.demo = False
                    panel.service = SimpleNamespace(script_bindings={},library_scripts=lambda:[record])
                    root.attributes('-alpha',0)
                    root.deiconify()
                    root.update()
                    choose = next(w for w in widgets(root) if isinstance(w,m.ttk.Button) and w.cget('text')=='Elegir script de Falcon…')
                    choose.invoke()
                    dialog = next(w for w in root.winfo_children() if isinstance(w,m.tk.Toplevel))
                    dialog.attributes('-alpha',0)
                    tree = next(w for w in widgets(dialog) if isinstance(w,m.ttk.Treeview))
                    end = time.monotonic()+5
                    while not tree.get_children() and time.monotonic()<end:
                        root.update()
                        time.sleep(.02)
                    self.assertTrue(tree.get_children())
                    tree.selection_set(tree.get_children()[0])
                    root.update()
                    for size in ('900x540','680x400'):
                        dialog.geometry(size)
                        root.update()
                        for text in ('Vincular seleccionado','Cancelar','Actualizar lista'):
                            control = next(w for w in widgets(dialog) if isinstance(w,m.ttk.Button) and w.cget('text')==text)
                            self.assertTrue(control.winfo_ismapped(), (scale,size,text,'oculto'))
                            self.assertGreater(control.winfo_height(),10)
                            self.assertGreaterEqual(control.winfo_rootx(),dialog.winfo_rootx())
                            self.assertLessEqual(control.winfo_rootx()+control.winfo_width(),dialog.winfo_rootx()+dialog.winfo_width())
                            self.assertLessEqual(control.winfo_rooty()+control.winfo_height(),dialog.winfo_rooty()+dialog.winfo_height())
                    use = next(w for w in widgets(dialog) if isinstance(w,m.ttk.Button) and w.cget('text')=='Vincular seleccionado')
                    self.assertNotIn('disabled',use.state())
                    with patch.object(m.messagebox,'askyesno',return_value=True), \
                         patch.object(m.messagebox,'showinfo',side_effect=lambda *a,**k:errors.append(str(a))), \
                         patch.object(m.messagebox,'showerror',side_effect=lambda *a,**k:errors.append(str(a))):
                        use.invoke()
                        root.update()
                    self.assertFalse(dialog.winfo_exists())
                    self.assertEqual(panel.db.execute('SELECT script FROM app').fetchone()[0],record['name'])
                    self.assertEqual(panel.db.execute('SELECT count(*) FROM job').fetchone()[0],0)
                    self.assertFalse(errors,errors)
                finally:
                    if panel is not None: panel.db.close()
                    root.destroy()

if __name__=='__main__':
    unittest.main()
