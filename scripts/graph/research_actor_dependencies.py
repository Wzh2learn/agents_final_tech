#!/usr/bin/env python3
"""Build/verify read-only actor dependencies without project wheel sources.

Inputs are trusted local environments; the output must be a fresh private path.
No network, model endpoint, original environment mutation or package install.
"""
from __future__ import annotations
import hashlib,json,os,re,shutil
from pathlib import Path


def sha(path):return hashlib.sha256(path.read_bytes()).hexdigest()

def _blocked(name,packages):
 lower=name.casefold()
 for package in packages:
  key=package.casefold()
  if lower==key or (lower.startswith(key+'-') and (lower.endswith('.dist-info') or lower.endswith('.egg-info') or lower.endswith('.pth'))):return True
 return False

def _files(root):
 result={}
 for directory,dirs,files in os.walk(root,topdown=True,followlinks=False):
  dirs.sort();files.sort()
  for name in dirs+files:
   p=Path(directory)/name
   if p.is_symlink():raise ValueError('unexpected symlink in projection '+str(p))
   if p.is_file():result[p.relative_to(root).as_posix()]={'sha256':sha(p),'bytes':p.stat().st_size}
 return result

def _reject_links(root,*,ignored=()):
 for directory,dirs,files in os.walk(root,topdown=True,followlinks=False):
  dirs[:]=[d for d in dirs if d not in ignored]
  for name in dirs+files:
   p=Path(directory)/name
   if p.is_symlink():raise ValueError('input contains symlink '+str(p))

def prepare_projection(destination,python_prefix,sites,blocked_packages,*,python_version='3.10'):
 destination=Path(destination);python_prefix=Path(python_prefix)
 if not destination.is_absolute() or not python_prefix.is_absolute() or not sites or not blocked_packages:raise ValueError('absolute private paths and explicit policy required')
 if any(not re.fullmatch(r'[A-Za-z0-9_]+',x) for x in blocked_packages):raise ValueError('invalid blocked package')
 if any(not re.fullmatch(r'[A-Za-z0-9_-]+',name) for name in sites):raise ValueError('invalid site name')
 if python_version not in ('3.8','3.10'):raise ValueError('unsupported Python projection version')
 stdlib=python_prefix/('lib/python'+python_version);binary=python_prefix/('bin/python'+python_version)
 if not stdlib.is_dir() or not binary.is_file():raise ValueError('requested Python interpreter/stdlib unavailable')
 site_paths={name:Path(path) for name,path in sites.items()}
 if any(not path.is_absolute() or not path.is_dir() or path.is_symlink() for path in site_paths.values()):raise ValueError('invalid site path')
 _reject_links(stdlib,ignored=('site-packages','__pycache__'))
 for path in site_paths.values():_reject_links(path,ignored=('__pycache__',))
 destination.mkdir(parents=True,exist_ok=False)
 runtime=destination/'runtime';(runtime/'bin').mkdir(parents=True)
 for name in ('python','python3','python'+python_version):shutil.copy2(binary,runtime/'bin'/name)
 def runtime_ignore(directory,names):
  return {n for n in names if n in ('site-packages','__pycache__') or n.endswith(('.pyc','.pyo'))}
 shutil.copytree(stdlib,runtime/('lib/python'+python_version),ignore=runtime_ignore)
 lib=python_prefix/'lib'
 for path in sorted(lib.glob('*.so*')):
  if not path.is_file():continue
  resolved=path.resolve()
  if not resolved.is_relative_to(lib.resolve()):raise ValueError('shared library leaves Python prefix')
  shutil.copy2(resolved,runtime/'lib'/path.name)
 for name,path in site_paths.items():
  def site_ignore(directory,names):
   top=Path(directory)==path
   return {n for n in names if n=='__pycache__' or n.endswith(('.pyc','.pyo')) or (top and _blocked(n,blocked_packages))}
  shutil.copytree(path,destination/'deps'/name,ignore=site_ignore)
 manifest={'version':1,'python':python_version,'blocked_packages':list(blocked_packages),'site_names':sorted(site_paths),
           'source_interpreter_sha256':sha(binary),'source_site_paths':{k:str(v) for k,v in sorted(site_paths.items())},
           'files':_files(destination),'scope':'actor runtime and third-party packages only; no project wheel Python source or package metadata'}
 result=destination/'manifest.json'
 with result.open('x',encoding='utf8') as f:json.dump(manifest,f,indent=2,sort_keys=True);f.write('\n')
 return result

def verify_projection(destination,expected_manifest_sha256):
 destination=Path(destination)
 if not destination.is_absolute() or destination.is_symlink():raise ValueError('invalid projection root')
 path=destination/'manifest.json'
 if path.is_symlink() or sha(path)!=expected_manifest_sha256:raise ValueError('projection manifest hash changed')
 manifest=json.loads(path.read_text(encoding='utf8'))
 if manifest.get('version')!=1:raise ValueError('projection format mismatch')
 python_version=manifest.get('python')
 if python_version not in ('3.8','3.10'):raise ValueError('unsupported Python projection version')
 actual=_files(destination);actual.pop('manifest.json',None)
 if actual!=manifest['files']:raise ValueError('projection content changed')
 runtime=destination/'runtime';python=runtime/'bin/python'
 if (runtime/('lib/python'+python_version)/'site-packages').exists() or not python.is_file():raise ValueError('runtime site-packages exposed or interpreter missing')
 for name in manifest['site_names']:
  site=destination/'deps'/name
  if not site.is_dir() or any(_blocked(child.name,manifest['blocked_packages']) for child in site.iterdir()):raise ValueError('blocked package exposed')
 return {'manifest_sha256':expected_manifest_sha256,'runtime':str(runtime),
         'sites':{name:str(destination/'deps'/name) for name in manifest['site_names']},
         'blocked_packages':manifest['blocked_packages'],'file_count':len(actual)}
