#!/usr/bin/env python3
"""Privately qualify frozen Matplotlib issues with bounded Agg controls.

Python sources come from pinned upstream commits; only missing native extensions
and generated _version.py are supplied by matching-series released wheels.
"""
from __future__ import annotations
import hashlib,json,shutil,subprocess,sys,tarfile,time
from pathlib import Path,PurePosixPath
import pyarrow.parquet as pq
ROOT=Path('/home/testuser/wzh/research_evidence/agent_learning_20261030')
OUT=ROOT/'matplotlib_qualification_20261106_v2'; DATA=ROOT/'swe_contextbench_data_20261104'
LEGACY=Path('/home/testuser/miniconda3/envs/agent_sft')
IMAGE='sha256:648a1999badfe683239ec49e05b2a508e37f762213478122c58fa713f6c00f58'
MANIFEST='bfa76e90221cc82e2c33d24588ff3060756c57679d687f68b29e9e662d68b10c'
CASES={
 'source':('matplotlib__matplotlib-23562','SWEContextBench_Lite_Experience.parquet','29a86636a9c45ab5ac4d80ac76eaee497f460dce','49aa1eae5c0209f7021f45793c0ba18f4a2223373f3422c62b8c095750474a4e','3.6.3','lib/mpl_toolkits/tests/test_mplot3d.py'),
 'target':('matplotlib__matplotlib-27361','SWEContextBench_Related_Lite.parquet','5b5154ded5ee9c546e640b01f1a75ac041fd2fed','bb26a42226568d63b0feca3d9d36fa732177be7d5adafdfd88040542404cad4d','3.9.4','lib/mpl_toolkits/mplot3d/tests/test_axes3d.py')}

def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()

def extract(archive,base,rev):
 base.mkdir(parents=True);materialized={}
 with tarfile.open(archive,'r:gz') as tf:
  for it in tf:
   p=PurePosixPath(it.name)
   if not p.parts or p.parts[0]!='matplotlib-'+rev or p.is_absolute() or '..' in p.parts or not (it.isfile() or it.isdir() or it.issym()):raise ValueError('unsafe archive entry '+it.name)
   if len(p.parts)==1:continue
   d=base.joinpath(*p.parts[1:])
   if it.isdir():d.mkdir(parents=True,exist_ok=True)
   else:
    d.parent.mkdir(parents=True,exist_ok=True)
    if it.issym():
     target=PurePosixPath(it.linkname)
     if len(target.parts)!=1 or target.name in ('.','..'):raise ValueError('unsafe symlink')
     member=tf.getmember(str(p.parent/target))
     if not member.isfile():raise ValueError('symlink target is not regular')
     with tf.extractfile(member) as a,d.open('wb') as b:shutil.copyfileobj(a,b)
     materialized[str(PurePosixPath(*p.parts[1:]))]={'target':it.linkname,'sha256':sha(d)}
    else:
     with tf.extractfile(it) as a,d.open('wb') as b:shutil.copyfileobj(a,b)
 return materialized

def patch(work,text,path):
 path.write_text(text,encoding='utf8');out=[]
 for cmd in (['git','apply','--check',str(path)],['git','apply',str(path)]):
  p=subprocess.run(cmd,cwd=work,capture_output=True,text=True,timeout=30);out.append({'exit':p.returncode,'stderr':p.stderr[-2000:]})
  if p.returncode:break
 return {'sha256':sha(path),'steps':out}

def overlay(work,site):
 source=site/'matplotlib';result={}
 for f in [*source.rglob('*.so'),source/'_version.py']:
  if not f.is_file():raise FileNotFoundError(f)
  rel=f.relative_to(source);d=work/'lib/matplotlib'/rel
  if d.exists():raise ValueError('overlay would replace source '+str(rel))
  d.parent.mkdir(parents=True,exist_ok=True);shutil.copy2(f,d);result[str(rel)]=sha(d)
 return result

LAUNCHER=r"""
import json,sys,pytest
requested=json.loads(sys.argv[1]);testfile=sys.argv[2]
class Select:
 def pytest_collection_modifyitems(self,session,config,items):
  found={i.nodeid for i in items};resolved={};self.missing=[];ambiguous={}
  for node in requested:
   if node in found:candidates=[node]
   elif '[' in node and not node.endswith(']'):
    candidates=[n for n in found if n.startswith(node)]
   else:
    file,tail=node.split('::',1)
    candidates=[n for n in found if n.startswith(file+'::') and n.endswith('::'+tail)]
   if len(candidates)==1:resolved[node]=candidates[0]
   elif not candidates:self.missing.append(node)
   else:ambiguous[node]=sorted(candidates);self.missing.append(node)
  expected=set(resolved.values())
  if len(expected)!=len(requested):self.missing.append('duplicate-resolutions')
  keep=[i for i in items if i.nodeid in expected];dropped=[i for i in items if i.nodeid not in expected]
  items[:]=keep;config.hook.pytest_deselected(items=dropped)
  print('QUALIFICATION_NODES',json.dumps({'requested':len(requested),'selected':len(keep),'missing':self.missing,'ambiguous':ambiguous,'mapped':{k:v for k,v in resolved.items() if k!=v}}))
 def pytest_sessionfinish(self,session,exitstatus):
  if self.missing:session.exitstatus=4
sys.exit(pytest.main(['-q','-o','addopts=','-p','no:cacheprovider','/workspace/'+testfile],plugins=[Select()]))
"""
PROBE=r"""
import json,sys,traceback,io
import numpy as np,matplotlib
matplotlib.use('Agg',force=True)
import matplotlib.pyplot as plt
import matplotlib.patches as pat
import mpl_toolkits.mplot3d.art3d as art3d
result={'matplotlib_version':matplotlib.__version__,'matplotlib_file':matplotlib.__file__,'art3d_file':art3d.__file__,'numpy_version':np.__version__,'backend':matplotlib.get_backend(),'cases':{}}
def probe(name,fn):
 try:result['cases'][name]=dict(exception=None,**fn())
 except Exception as e:result['cases'][name]={'exception':{'type':type(e).__name__,'message':str(e),'traceback':traceback.format_exc()}}
if sys.argv[1]=='source':
 def source_probe():
  y,x=np.ogrid[1:10:100j,1:10:100j];z=np.cos(x)**3-np.sin(y)**2
  fig=plt.figure();ax=fig.add_subplot(111,projection='3d');p=ax.plot_surface(x,y,z,cmap='hot')
  pre=p.get_facecolors();colors=np.asarray(pre);fig.canvas.draw();post=np.asarray(p.get_facecolors())
  ok=bool(colors.ndim==2 and colors.shape[0]>0 and colors.shape[-1]==4 and np.isfinite(colors).all() and post.shape==colors.shape)
  plt.close(fig);return {'facecolors_shape':list(colors.shape),'finite_rgba_and_shape_stable':ok}
 probe('issue_get_facecolors_before_draw',source_probe)
else:
 def target_probe(fmt,dpi):
  fig,ax=plt.subplots(subplot_kw={'projection':'3d'},layout='tight')
  patch=pat.Rectangle((0,0),1.,1.);ax.add_patch(patch);art3d.pathpatch_2d_to_3d(patch)
  b=io.BytesIO();kw={'format':fmt}
  if dpi is not None:kw['dpi']=dpi
  fig.savefig(b,**kw);output=b.getvalue();fig.canvas.draw()
  bbox=patch.get_window_extent(fig.canvas.get_renderer());rgba=np.asarray(fig.canvas.buffer_rgba())
  x0=max(0,int(np.floor(bbox.x0)));x1=min(rgba.shape[1],int(np.ceil(bbox.x1)))
  y0=max(0,rgba.shape[0]-int(np.ceil(bbox.y1)));y1=min(rgba.shape[0],rgba.shape[0]-int(np.floor(bbox.y0)))
  pixels=rgba[y0:y1,x0:x1,:3];ink=int(np.any(pixels<245,axis=2).sum()) if pixels.size else 0
  header=output.startswith(b'%PDF-') if fmt=='pdf' else output.startswith(b'\x89PNG\r\n\x1a\n')
  face=np.rint(np.asarray(patch.get_facecolor()[:3])*255).astype(int)
  face_pixels=int(np.all(np.abs(pixels.astype(int)-face)<=25,axis=2).sum()) if pixels.size else 0
  ok=bool(header and len(output)>1000 and np.isfinite(bbox.bounds).all() and bbox.width>0 and bbox.height>0 and face_pixels>0)
  plt.close(fig);return {'output_format':fmt,'dpi':dpi,'output_bytes':len(output),'header_valid':header,'bbox':list(bbox.bounds),'ink_pixels_in_bbox':ink,'facecolor_pixels_in_bbox':face_pixels,'render_semantics_pass':ok}
 probe('issue_save_pdf',lambda:target_probe('pdf',None))
 probe('issue_save_png_300dpi',lambda:target_probe('png',300))
print(json.dumps(result))
"""

def run(work,site,args,path,name):
 name='mpl-qual-'+name+'-'+str(time.monotonic_ns())
 cmd=['docker','run','--name',name,'--rm','--pull','never','--network','none','--read-only','--cpus','2','--memory','4g','--pids-limit','256','--cap-drop','ALL','--security-opt','no-new-privileges','--tmpfs','/tmp:rw,nosuid,size=512m','-e','HOME=/tmp','-e','MPLBACKEND=Agg','-e','MPLCONFIGDIR=/tmp/mpl','-e','PYTHONPATH=/workspace/lib:/deps','-e','PYTHONDONTWRITEBYTECODE=1','-e','PYTEST_DISABLE_PLUGIN_AUTOLOAD=1','--mount',f'type=bind,src={work},dst=/workspace,readonly','--mount',f'type=bind,src={LEGACY},dst=/extra,readonly','--mount',f'type=bind,src={site},dst=/deps,readonly','--workdir','/tmp','--entrypoint','/extra/bin/python',IMAGE,*args]
 start=time.monotonic()
 try:p=subprocess.run(cmd,capture_output=True,timeout=900);code,out=p.returncode,p.stdout+p.stderr
 except subprocess.TimeoutExpired as e:
  code,out=124,(e.stdout or b'')+(e.stderr or b'');subprocess.run(['docker','kill',name],capture_output=True,timeout=10)
 path.write_bytes(out)
 return {'exit':code,'seconds':round(time.monotonic()-start,3),'log_sha256':sha(path),'log_tail':out.decode('utf8',errors='replace').splitlines()[-12:]}

def main():
 if sha(DATA/'manifest.json')!=MANIFEST:raise ValueError('dataset manifest changed')
 for ent in json.loads((DATA/'manifest.json').read_text())['files']:
  if sha(DATA/ent['name'])!=ent['sha256']:raise ValueError('dataset file mismatch')
 receipt={'status':'IN_PROGRESS','model_calls':0,'training':0,'dataset_manifest':MANIFEST,'script_sha256':sha(Path(__file__)),'python_sha256':sha(LEGACY/'bin/python3.10'),'image':IMAGE,'cases':{}}
 for label,(identity,filename,rev,archive_sha,version,testfile) in CASES.items():
  archive=OUT/(label+'.tar.gz'); env=OUT/'source_env' if label=='source' else ROOT/'matplotlib_qualification_20261106/target_env';site=env/'lib/python3.10/site-packages'
  if sha(archive)!=archive_sha or not site.is_dir():raise ValueError('archive or private env mismatch')
  wheel=list((OUT/'wheelhouse').glob('matplotlib-'+version+'-*.whl'))
  if len(wheel)!=1:raise ValueError('missing frozen wheel')
  deps=subprocess.run([str(env/'bin/python'),'-m','pip','freeze'],capture_output=True,text=True,check=True,timeout=60).stdout
  (OUT/(label+'_dependencies.txt')).write_text(deps,encoding='utf8')
  cols=['instance_id','base_commit','patch','test_patch','FAIL_TO_PASS','PASS_TO_PASS','problem_statement','hints_text']
  matches=[r for r in pq.read_table(DATA/filename,columns=cols).to_pylist() if r['instance_id']==identity]
  if len(matches)!=1 or matches[0]['base_commit']!=rev:raise ValueError('dataset identity mismatch')
  row=matches[0];case=OUT/label;clean=case/'clean_base';materialized=extract(archive,clean,rev)
  (case/'materialized_links.json').write_text(json.dumps(materialized,indent=2,sort_keys=True)+'\n')
  (case/'task.txt').write_text(row['problem_statement'].replace('\r\n','\n').rstrip()+'\n',encoding='utf8')
  for n,col in (('focus','FAIL_TO_PASS'),('regression','PASS_TO_PASS')):(case/(n+'_nodes.json')).write_text(json.dumps(json.loads(row[col]),indent=2)+'\n')
  c={'id':identity,'base_commit':rev,'archive_sha256':archive_sha,'materialized_links_sha256':sha(case/'materialized_links.json'),'materialized_links_count':len(materialized),'wheel_name':wheel[0].name,'wheel_sha256':sha(wheel[0]),'dependency_sha256':sha(OUT/(label+'_dependencies.txt')),'task_sha256':sha(case/'task.txt'),'hints_sha256':hashlib.sha256((row['hints_text'] or '').encode()).hexdigest(),'focus_nodes_sha256':sha(case/'focus_nodes.json'),'regression_nodes_sha256':sha(case/'regression_nodes.json'),'node_resolution_scope':'exact first; truncated parameter prefixes or missing class names resolve only if unique; mappings shown in test logs','overlay_scope':'native extensions and absent generated _version.py only; wheel build differs from frozen source; no Python behavior replaced','arms':{}}
  receipt['cases'][label]=c
  for arm in ('base','gold'):
   work=case/arm;shutil.copytree(clean,work);ov=overlay(work,site);(case/(arm+'_overlay.json')).write_text(json.dumps(ov,indent=2,sort_keys=True)+'\n')
   detail={'overlay_sha256':sha(case/(arm+'_overlay.json')),'source_art3d_sha256':sha(work/'lib/mpl_toolkits/mplot3d/art3d.py')};c['arms'][arm]=detail
   tp=patch(work,row['test_patch'],case/(arm+'_test.patch'));detail['test_patch']=tp
   if len(tp['steps'])==2 and all(z['exit']==0 for z in tp['steps']):
    gp=patch(work,row['patch'],case/'gold_reference.patch') if arm=='gold' else None
    if gp:detail['reference_patch']=gp
    if not gp or (len(gp['steps'])==2 and all(z['exit']==0 for z in gp['steps'])):
     detail['issue_probe']=run(work,site,['-c',PROBE,label],case/(arm+'_issue_probe.log'),label+arm+'i')
     for metric,col in (('focus','FAIL_TO_PASS'),('regression','PASS_TO_PASS')):
      nodes=json.loads(row[col]);detail[metric]=run(work,site,['-c',LAUNCHER,json.dumps(nodes),testfile],case/(arm+'_'+metric+'.log'),label+arm+metric);detail[metric]['nodes_requested']=len(nodes)
   (OUT/'receipt.json').write_text(json.dumps(receipt,indent=2)+'\n')
 receipt['status']='COMPLETED_CONTROLS_NOT_ADJUDICATED'
 (OUT/'receipt.json').write_text(json.dumps(receipt,indent=2)+'\n');print(json.dumps({'status':receipt['status'],'receipt':str(OUT/'receipt.json'),'sha256':sha(OUT/'receipt.json')}))
if __name__=='__main__':main()
