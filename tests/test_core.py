import importlib.util
import json
import tempfile
import unittest
import zipfile
from pathlib import Path
from types import SimpleNamespace

ROOT = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location('gestor', ROOT/'gestor.py')
app = importlib.util.module_from_spec(spec)
spec.loader.exec_module(app)


class CoreTests(unittest.TestCase):
    def test_empty_profile_does_not_seed_an_inventory(self):
        with tempfile.TemporaryDirectory() as tmp:
            db = app.db_open(Path(tmp)/'empty.sqlite3')
            try:
                for table in ('app', 'inventory', 'job', 'removal'):
                    self.assertEqual(db.execute('SELECT COUNT(*) FROM '+table).fetchone()[0], 0)
            finally:
                db.close()

    def test_sensor_unknown_is_not_offline_or_online(self):
        falcon = app.Falcon.__new__(app.Falcon)
        falcon.hosts = SimpleNamespace(get_online_state=lambda **kw: {
            'status_code':200, 'body':{'resources':[
                {'id':'one','state':' online '}, {'id':'two','state':'offline'},
                {'id':'three','state':'unknown'}, {'id':'four','state':'new-state'}]}})
        self.assertEqual(falcon.online_states(['one','two','three','four']), {
            'one':'En línea', 'two':'Desconectado', 'three':'Desconocido', 'four':'Desconocido'})

    def test_history_keeps_raw_error_and_requires_later_absence(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp)/'profile.sqlite3'
            db = app.db_open(path)
            db.execute("INSERT INTO app(id,name,vendor,platform,category) VALUES(1,'App Demo','Demo','Windows','Utilidades')")
            db.execute("INSERT INTO job(id,app_id,aid,status,updated) VALUES(1,1,'host-demo','Finalizado con errores','2026-01-02T10:00:00Z')")
            db.execute("INSERT INTO removal(app_id,host_key,stamp) VALUES(1,'host-demo','2026-01-01T10:00:00Z')")
            self.assertEqual(app.job_result(db,1), 'Finalizado con errores')
            db.execute("INSERT INTO removal(app_id,host_key,stamp) VALUES(1,'host-demo','2026-01-03T10:00:00Z')")
            self.assertEqual(app.job_result(db,1), 'Ya no figura instalado')
            self.assertEqual(db.execute('SELECT status FROM job WHERE id=1').fetchone()[0], 'Finalizado con errores')
            db.execute("INSERT INTO inventory(app_id,host_key,aid,installed) VALUES(1,'host-demo','host-demo',1)")
            self.assertEqual(app.job_result(db,1), 'Finalizado con errores')
            db.commit()
            db.close()
            reopened = app.db_open(path)
            self.assertEqual(reopened.execute('SELECT status FROM job WHERE id=1').fetchone()[0], 'Finalizado con errores')
            reopened.close()

    def test_queue_persists_and_duplicate_active_job_is_not_created(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp)/'queue.sqlite3'
            db = app.db_open(path)
            db.execute("INSERT INTO app(id,name,vendor,platform,category,script) VALUES(1,'App Demo','Demo','Windows','Utilidades','Demo-script')")
            db.execute("INSERT INTO inventory(app_id,host_key,aid,hostname,installed) VALUES(1,'demo-host','demo-host','PC-DEMO',1)")
            db.commit()
            ids = app.plan(db,1,['demo-host'],True,'demo-campaign')
            app.set_state(db,ids[0],'En cola',request='demo-request')
            db.close()
            db = app.db_open(path)
            try:
                self.assertEqual(db.execute('SELECT status FROM job').fetchone()[0], 'En cola')
                self.assertEqual(app.plan(db,1,['demo-host'],True,'second'), [])
            finally:
                db.close()

    def test_bundled_assets_reject_path_traversal_before_writing(self):
        with tempfile.TemporaryDirectory() as tmp:
            folder = Path(tmp)/'iconos'
            folder.mkdir()
            with zipfile.ZipFile(folder/'recursos.zip','w') as bundle:
                bundle.writestr('familias/valid.png', b'fake')
                bundle.writestr('../outside.txt', b'unsafe')
            with self.assertRaises(ValueError):
                app.ensure_icon_assets(folder)
            self.assertFalse((Path(tmp)/'outside.txt').exists())
            self.assertFalse((folder/'familias/valid.png').exists())

    def test_own_inventory_generates_vendor_and_category_fallbacks(self):
        # No Tk display or account required: exercise the catalog logic directly.
        library = app.IconLibrary.__new__(app.IconLibrary)
        library.catalog = {}
        library.cache = {}
        library.available = False
        library.dirty = False
        library.brand_rules = []
        library.exact_brand_rules = {}
        library.vendor_rules = [{'alias':'demo publisher','archivo':'familias/demo-vendor.png'}]
        library.category_icons = {'Utilidades':'familias/demo-tools.png', 'Sin clasificar':'familias/demo-generic.png'}
        library.register_apps([('Unlisted app','Demo Publisher Ltd.','Utilidades','Windows'),
                               ('Another app','Other publisher','Utilidades','Windows')])
        self.assertEqual(library.catalog['Unlisted app']['logo_tipo'],'fabricante')
        self.assertEqual(library.catalog['Another app']['logo_tipo'],'categoría')
        library.register_apps([('Unlisted app','Another vendor','Utilidades','Windows')])
        self.assertEqual(library.catalog['Unlisted app']['logo'],'familias/demo-tools.png')
        library.brand_rules = [{'alias':'known product','archivo':'familias/product.png'}]
        library.register_apps([('Known product 2','Another vendor','Utilidades','Windows')])
        self.assertEqual(library.catalog['Known product 2']['logo_tipo'],'producto')

    def test_entrypoints_and_generic_rules(self):
        self.assertEqual((ROOT/'gestor.py').read_bytes(),(ROOT/'GestorFalcon.pyw').read_bytes())
        rules = json.loads((ROOT/'iconos/reglas.json').read_text(encoding='utf-8'))
        self.assertTrue(rules)
        self.assertFalse(any(r.get('modo') == 'exacto' for r in rules))
        with zipfile.ZipFile(ROOT/'iconos/recursos.zip') as bundle:
            names = set(bundle.namelist())
            for rule in rules:
                self.assertIn(rule['archivo'], names)


if __name__ == '__main__':
    unittest.main()
