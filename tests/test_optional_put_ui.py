import importlib.util
import tempfile
import time
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import patch

HERE=Path(__file__).resolve().parents[1]
spec=importlib.util.spec_from_file_location('put_ui',HERE/'gestor.py')
m=importlib.util.module_from_spec(spec)
spec.loader.exec_module(m)

def widgets(parent):
    for child in parent.winfo_children():
        yield child
        yield from widgets(child)

def button(parent,text):
    return next(w for w in widgets(parent) if isinstance(w,m.ttk.Button) and w.cget('text')==text)

def spin(root,condition):
    end=time.monotonic()+5
    while not condition() and time.monotonic()<end:
        root.update()
        time.sleep(.02)
    assert condition(),'UI callback timeout'


import unittest

class OptionalPutUITests(unittest.TestCase):
    def test_file_picker_and_application_configuration(self):
        (HERE/'test-temp').mkdir(exist_ok=True)
        with tempfile.TemporaryDirectory(dir=HERE/'test-temp') as temp:
            assert Path(temp).resolve().is_relative_to(HERE/'test-temp')
            folder=Path(temp)/'datos'
            folder.mkdir()
            db=m.db_open(folder/'demo.sqlite3')
            for key in (1,2):
                db.execute("INSERT INTO app(id,name,vendor,platform,category,draft,script) VALUES(?,?,?,'Windows','Utilidades','Write-Output 1','script')",(key,'Programa '+str(key),'Ejemplo'))
                db.execute("INSERT INTO inventory(app_id,host_key,aid,hostname,installed) VALUES(?,?,?,?,1)",(key,'demo-'+str(key),'demo-'+str(key),'PC-EJEMPLO'))
            db.execute("INSERT INTO meta VALUES('applications_scope','application')")
            db.execute("INSERT INTO meta VALUES('sync',?)",(m.now(),))
            db.commit();db.close()
            root=m.create_root()
            root.withdraw()
            errors=[]
            root.report_callback_exception=lambda *args:errors.append(str(args[1]))
            panel=m.Panel(root,folder/'demo.sqlite3',m.Demo())
            for timer in root.tk.call('after','info'):
                command=root.tk.call('after','info',timer)[0]
                if command in root._tclCommands:root.after_cancel(timer)
            record=dict(id='put-one',name='BSTCleaner_native.exe',sha256='a'*64,size=9438104)
            panel.demo=False
            panel.service=SimpleNamespace(script_bindings={},library_put_files=lambda:[record,dict(record,id='two',name='Otra herramienta.exe')])
            with patch.object(m.messagebox,'showinfo',side_effect=lambda *a,**k:errors.append(str(a))),patch.object(m.messagebox,'showerror',side_effect=lambda *a,**k:errors.append(str(a))):
                panel.select_group(1)
                notebook=next(w for w in widgets(panel.detail) if isinstance(w,m.ttk.Notebook))
                notebook.select(next(tab for tab in notebook.tabs() if notebook.tab(tab,'text')=='Desinstalador'))
                root.attributes('-alpha',0.0)
                root.deiconify()
                for width,height in ((1280,800),(1024,768)):
                    root.geometry(f'{width}x{height}')
                    root.update()
                    pick=button(root,'Elegir archivo de Falcon…')
                    publish=button(root,'Publicar en Falcon')
                    for control in (pick,publish):
                        assert control.winfo_rootx()+control.winfo_width()<=root.winfo_rootx()+root.winfo_width(), 'Boton fuera del ancho'
                        assert control.winfo_rooty()+control.winfo_height()<=root.winfo_rooty()+root.winfo_height(), 'Boton fuera del alto'
                    editor=next(w for w in widgets(panel.detail) if isinstance(w,m.tk.Text) and w.winfo_name()=='editor')
                    if editor.winfo_height()<40:
                        print('LAYOUT',[(w.winfo_class(),w.winfo_geometry(),w.winfo_reqheight(),w.grid_info().get('row')) for w in editor.master.winfo_children()])
                    assert editor.winfo_height()>=40, ('Editor sin espacio',width,height,root.winfo_geometry(),notebook.select(),editor.winfo_geometry(),editor.winfo_ismapped(),errors)
                root.withdraw()
                check=next(w for w in widgets(root) if isinstance(w,m.ttk.Checkbutton) and w.cget('text')=='Usar archivo previo (put)')
                picker=button(root,'Elegir archivo de Falcon…')
                assert picker.instate(['disabled'])
                check.invoke();root.update()
                assert not picker.instate(['disabled'])
                picker.invoke()
                dialog=next(w for w in root.winfo_children() if isinstance(w,m.tk.Toplevel))
                dialog.withdraw()
                tree=next(w for w in widgets(dialog) if isinstance(w,m.ttk.Treeview))
                spin(root,lambda:len(tree.get_children())==2)
                search=next(w for w in widgets(dialog) if isinstance(w,m.ttk.Entry))
                search.insert(0,'BSTCleaner');root.update()
                assert len(tree.get_children())==1
                tree.selection_set(tree.get_children()[0]);root.update()
                use=button(dialog,'Usar archivo seleccionado')
                assert not use.instate(['disabled'])
                use.invoke();root.update()
                assert not dialog.winfo_exists()
                assert m.get_put_binding(panel.db,1)['id']=='put-one'
                assert panel.db.execute('SELECT COUNT(*) FROM job').fetchone()[0]==0
                panel.select_group(2)
                assert m.get_put_binding(panel.db,2) is None
                assert button(root,'Elegir archivo de Falcon…').instate(['disabled'])
                panel.select_group(1)
                assert not button(root,'Elegir archivo de Falcon…').instate(['disabled'])
                check=next(w for w in widgets(root) if isinstance(w,m.ttk.Checkbutton) and w.cget('text')=='Usar archivo previo (put)')
                check.invoke();root.update()
                assert m.get_put_binding(panel.db,1) is None
                assert not errors,errors
            panel.db.close();root.destroy()
        print('OK: opción desactivada/activada, búsqueda, selección, persistencia por aplicación y cero órdenes remotas.')

