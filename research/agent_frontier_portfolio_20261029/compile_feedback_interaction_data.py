"""Compile the already-graded two-state source without any generation."""
from pathlib import Path
import ast,hashlib,importlib.util,json
BASE=Path('/home/testuser/wzh/research_evidence/agent_learning_20261030')
PHASE=BASE/'fccl_condition_learning_v1'
OUT=PHASE/'policy_v1'
REPO=Path('/home/testuser/wzh/projects/agents_final_tech')
CODE=REPO/'research/agent_frontier_portfolio_20261029'
MODEL=Path('/home/testuser/wzh/models/hf/Qwen3-8B')
ST=BASE/'alfworld_text_qualification_20261106/context_study_v1'
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def save(p,j):
    with p.open('x') as f:json.dump(j,f,indent=2);f.write('\n')
def module(p):
    spec=importlib.util.spec_from_file_location(p.stem,p);m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m);return m
if OUT.exists():raise RuntimeError('attempt exists')
OUT.mkdir()
tokens=module(CODE/'alfworld_supervision_tokens.py')
tok=tokens.load_tokenizer(MODEL)
source=json.loads((PHASE/'astropy_pair_v1/PLAN.json').read_text())
close=json.loads((PHASE/'astropy_pair_v1/CLOSEOUT.json').read_text())
assert close['native_success_matrix']==[[1,0],[0,1]]
assert sha(PHASE/'astropy_pair_v1/CLOSEOUT.json')=='dc3ec87c3e5cb87962dc8b5fee2c5ceba274c0ce3e3a9b0dd7b0408d42f9301e'
rel='astropy/nddata/mixins/ndarithmetic.py'
ops=source['operators']
old,new=ops['mask']['before'],ops['mask']['after']
mask_code="from pathlib import Path\np=Path("+repr(rel)+")\ns=p.read_text()\nold="+repr(old)+"\nnew="+repr(new)+"\nif old in s:\n    assert s.count(old)==1\n    s=s.replace(old,new)\nelse:\n    assert new in s\np.write_text(s)\n"
unit_code="from pathlib import Path\np=Path("+repr(rel)+")\ns=p.read_text()\na=s.index('        # Do the calculation with or without units\\n')\na=s.index('        if self.unit is None:\\n',a)\nb=s.index('        elif hasattr(operand, \"unit\"):\\n',a)\ns=s[:a]+"+repr(ops['unit']['replacement'])+"+s[b:]\np.write_text(s)\n"
scripts=[mask_code,unit_code]
commands=["python - <<'PY'\n"+s+"PY" for s in scripts]
for script in scripts:ast.parse(script)
tools=[{'type':'function','function':{'name':'bash','description':'Run commands, read and edit files inside the isolated /workspace.','parameters':{'type':'object','properties':{'command':{'type':'string'},'description':{'type':'string'}},'required':['command','description']}}}]
rows=[];requests=[];source_bindings={}
for i,site in enumerate(['A4','A5']):
    snapshot=BASE/'fcdr_recovery_pilot_v1/snapshots'/site/'files'/rel
    assert sha(snapshot)==source['sources'][str(snapshot)]
    text=snapshot.read_text()
    tree=ast.parse(text);lines=text.splitlines()
    spans=[n for n in ast.walk(tree) if isinstance(n,ast.FunctionDef) and n.name in ['_arithmetic_data','_arithmetic_mask']]
    assert len(spans)==2
    excerpt='\n\n'.join('\n'.join(lines[n.lineno-1:n.end_lineno]) for n in sorted(spans,key=lambda n:n.lineno))
    probe=PHASE/'astropy_pair_v1'/('probe_'+site)/'public_probe.log'
    feedback=probe.read_text()
    assert 'AttributeError' in feedback and 'NoneType' in feedback
    request={'messages':[{'role':'system','content':'Repair the current Python code using the bash tool. Use only the public code and execution feedback. Return one executable edit tool call; do not modify tests.'},{'role':'user','content':'Goal: repair NDDataArray reduction with optional masks and units.\nFile: '+rel+'\nCurrent production code:\n'+excerpt+'\nExecuted public probe:\n'+source['probe']+'\nObserved result:\n'+feedback}], 'tools':tools}
    requests.append(request)
    source_bindings[str(snapshot)]=sha(snapshot);source_bindings[str(probe)]=sha(probe)
    for j,name in enumerate(['mask','unit']):
        assistant={'role':'assistant','content':'','tool_calls':[{'id':'reference_edit','type':'function','function':{'name':'bash','arguments':json.dumps({'command':commands[j],'description':'Repair optional '+name+' handling'},separators=(',',':'))}}]}
        encoded=tokens.encode_completion(request,assistant,tok,8192)
        rows.append(dict(**encoded,cell=[i,j],origin='D-extracted existing native-graded edit; not a newly generated model completion',assistant=assistant))
data={'schema':'native_corrective_interaction_training_v1','rows':rows,'requests':requests,'utilities':close['native_success_matrix'],'tokenizer':tokens.tokenizer_binding(MODEL,tok),'source_bindings':source_bindings,'native_closeout':{'path':str(PHASE/'astropy_pair_v1/CLOSEOUT.json'),'sha256':sha(PHASE/'astropy_pair_v1/CLOSEOUT.json')},'scope':'one exposed issue and two real code states; no heldout outcome or new independent task'}
save(OUT/'DATA.json',data)
components={str(CODE/x):sha(CODE/x) for x in ['train_feedback_interaction.py','feedback_interaction_learning.py','alfworld_supervision_learning.py','alfworld_supervision_tokens.py']}
plan={'schema':'finite_native_interaction_lora_comparison_v1','model_path':str(MODEL),'model_binding':{'path':str(ST/'learning_comparison_v1/HF8B_MODEL_BINDING_V1.json'),'sha256':'b8d5af477c1f6be67981583a4a60df9561ea53872e0676535aa9745fce011dc1'},'components':components,'data':{'path':str(OUT/'DATA.json'),'sha256':sha(OUT/'DATA.json')},'seed':17,'arm_order':['bc','row','coupled','dpo'],'updates_per_arm':24,'learning_rate':2e-5,'beta':.1,'arm_wall_seconds':1200,'max_wall_seconds':6000,'resource_lock':str(ST/'model_resource.lock'),'matched':'same four sequences, fresh q/v rank8 alpha16 dropout0 BF16 initialization, update count and initial preference-gradient norm. BC anchor common. No outcome-selected parameters.','continuation':'each edit is native-graded against full declared issue/regression contract; no first-action outcome label','next':'source loss is diagnostic only; actual OpenCode on other tasks still required','new_http_model_requests':0}
save(OUT/'PLAN.json',plan)
print(json.dumps({'plan_sha256':sha(OUT/'PLAN.json'),'rows':[dict(cell=r['cell'],sequence=r['sequence_length'],supervised=r['supervised_tokens']) for r in rows],'max_attempted_train_sequence_tokens':sum(len(r['input_ids']) for r in rows)*24*4,'source_only':True}))
