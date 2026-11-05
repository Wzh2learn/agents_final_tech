"""Actor projections remove project wheels and are fixed by content hashes."""
import importlib.util
from pathlib import Path
import tempfile
import unittest

SCRIPT=Path(__file__).resolve().parents[1]/'scripts/graph/research_actor_dependencies.py'
spec=importlib.util.spec_from_file_location('actor_dependencies',SCRIPT)
module=importlib.util.module_from_spec(spec);spec.loader.exec_module(module)

class ProjectionTests(unittest.TestCase):
 def test_python38_keeps_legacy_runtime_without_its_site_packages(self):
  with tempfile.TemporaryDirectory() as tmp:
   root=Path(tmp);prefix=root/'python';(prefix/'bin').mkdir(parents=True)
   (prefix/'bin/python3.8').write_bytes(b'legacy-python')
   std=prefix/'lib/python3.8';(std/'site-packages/django').mkdir(parents=True)
   (std/'site-packages/django/future.py').write_text('future')
   (std/'os.py').write_text('stdlib');site=root/'site';site.mkdir()
   (site/'django').mkdir();(site/'django/future.py').write_text('future')
   (site/'asgiref').mkdir();(site/'asgiref/__init__.py').write_text('dependency')
   dst=root/'projection'
   manifest=module.prepare_projection(dst,prefix,{'default':site},('django',),python_version='3.8')
   module.verify_projection(dst,module.sha(manifest))
   self.assertEqual((dst/'runtime/bin/python').read_bytes(),b'legacy-python')
   self.assertTrue((dst/'runtime/bin/python3.8').is_file())
   self.assertFalse((dst/'runtime/lib/python3.8/site-packages').exists())
   self.assertFalse((dst/'deps/default/django').exists())
   self.assertTrue((dst/'deps/default/asgiref/__init__.py').is_file())
   (dst/'runtime/lib/python3.8/site-packages').mkdir()
   with self.assertRaises(ValueError):module.verify_projection(dst,module.sha(manifest))

 def test_project_packages_absent_unrelated_astropy_data_retained_and_tamper_rejected(self):
  with tempfile.TemporaryDirectory() as tmp:
   root=Path(tmp);prefix=root/'python';(prefix/'bin').mkdir(parents=True);(prefix/'bin/python3.10').write_bytes(b'python')
   std=prefix/'lib/python3.10';(std/'site-packages/astropy').mkdir(parents=True);(std/'site-packages/astropy/gold.py').write_text('private')
   (std/'os.py').write_text('stdlib');site=root/'site';site.mkdir()
   for folder in ('astropy','astropy-5.3.2.dist-info','astropy_iers_data','numpy'):(site/folder).mkdir()
   (site/'astropy/gold.py').write_text('private');(site/'astropy_iers_data/__init__.py').write_text('data');(site/'numpy/__init__.py').write_text('numpy')
   (site/'astropy-5.3.2-py3.10-nspkg.pth').write_text('private')
   dst=root/'projection';manifest=module.prepare_projection(dst,prefix,{'default':site},('astropy',));digest=module.sha(manifest)
   r=module.verify_projection(dst,digest)
   self.assertEqual(r['blocked_packages'],['astropy'])
   self.assertEqual((dst/'runtime/bin/python').read_bytes(), (dst/'runtime/bin/python3').read_bytes())
   self.assertEqual((dst/'runtime/bin/python').read_bytes(), (dst/'runtime/bin/python3.10').read_bytes())
   self.assertFalse((dst/'runtime/lib/python3.10/site-packages').exists())
   self.assertFalse((dst/'deps/default/astropy').exists())
   self.assertFalse((dst/'deps/default/astropy-5.3.2.dist-info').exists())
   self.assertFalse((dst/'deps/default/astropy-5.3.2-py3.10-nspkg.pth').exists())
   self.assertTrue((dst/'deps/default/astropy_iers_data/__init__.py').is_file())
   (dst/'deps/default/numpy/__init__.py').write_text('tampered')
   with self.assertRaises(ValueError):module.verify_projection(dst,digest)
   with self.assertRaises(FileExistsError):module.prepare_projection(dst,prefix,{'default':site},('astropy',))

if __name__=='__main__':unittest.main()
