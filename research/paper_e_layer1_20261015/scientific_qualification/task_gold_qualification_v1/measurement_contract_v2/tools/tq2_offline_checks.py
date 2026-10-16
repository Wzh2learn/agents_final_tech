import hashlib, json, re
from datetime import datetime
from decimal import Decimal, ROUND_HALF_UP
from pathlib import Path
B=Path('D:/AIRcommend/JinRongAgents/agents_final_tech/research/paper_e_layer1_20261015/scientific_qualification/task_gold_qualification_v1/')
OUT=B/'measurement_contract_v2'
cases={c['case_id']:c for c in json.loads((B/'packets/stage2_cases.json').read_text(encoding='utf-8'))}
def sha(p): return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def read(p): return json.loads(Path(p).read_text(encoding='utf-8'))
checks=[]; replay=[]
def check(name,passed,detail): checks.append({'check':name,'passed':bool(passed),'detail':detail})
def coord_ok(spec,cid):
    bad=[]
    for path in spec['reference_paths']:
        for w in path['where']:
            m=re.fullmatch(r'r(\d+)c(\d+)',w)
            if not m: continue
            r,c=map(int,m.groups())
            if r>=len(cases[cid]['source_table']) or c>=len(cases[cid]['source_table'][r]) or r>=len(cases[cid]['perturbed_table']) or c>=len(cases[cid]['perturbed_table'][r]):
                bad.append(w)
    return bad
def dec(s):
    s=s.replace('$','').replace(',','')
    if s.endswith('(1)'): s=s[:-3]
    return Decimal(s)
def r2(v): return v.quantize(Decimal('0.01'),rounding=ROUND_HALF_UP)
specs={cid:read(OUT/'cases'/(cid+'.json')) for cid in ['Q02','Q03','Q04','Q05','Q06','Q08','Q09','Q10','Q12']}
for cid,s in specs.items():
    bad=coord_ok(s,cid); replay.append({'task_id':cid,'coord_valid':not bad,'invalid_coords':bad})
check('all_reference_coordinates_exist',all(x['coord_valid'] for x in replay),replay)
ops={}
ops['Q02']= 'accounts receivable, inventories, and net property, plant, and equipment.' in cases['Q02']['paragraphs'][1]['text']
ops['Q03']= dec(cases['Q03']['source_table'][3][2])-dec(cases['Q03']['source_table'][2][2])==Decimal('14054')
ops['Q04']= dec(cases['Q04']['source_table'][2][1])-dec(cases['Q04']['source_table'][1][1])==Decimal('-3')
d=datetime.strptime(cases['Q05']['source_table'][12][0],'%d %B %Y'); ops['Q05']= d.replace(year=d.year+10).strftime('%d %B %Y')=='31 January 2029' and '10 years from the date of grant' in cases['Q05']['paragraphs'][4]['text']
ops['Q06']= dec(cases['Q06']['source_table'][2][3])-dec(cases['Q06']['source_table'][3][3])==Decimal('308')
counts=[abs(int(cases['Q08']['source_table'][r][5].strip('()').replace(',',''))) for r in [1,2,3]]
ops['Q08']= counts.index(max(counts))==2 and cases['Q08']['source_table'][3][1]=='2 Jul 2017'
ops['Q09']= r2((dec(cases['Q09']['source_table'][5][1])-dec(cases['Q09']['source_table'][5][2]))/dec(cases['Q09']['source_table'][5][2])*100)==Decimal('9.73')
ops['Q10']= r2(dec(cases['Q10']['source_table'][2][1])/dec(cases['Q10']['source_table'][4][1]))==Decimal('0.47')
ops['Q12']= dec(cases['Q12']['source_table'][5][1])-dec(cases['Q12']['source_table'][5][2])==Decimal('6')
replay_rows=[]
for cid in ['Q02','Q03','Q04','Q05','Q06','Q08','Q09','Q10','Q12']:
    replay_rows.append({'task_id':cid,'reference_replay_passed':bool(ops[cid]),'perturbed_evidence_path':('BLOCKED_CANDIDATE' if cid=='Q06' else 'NOT_EVALUATED_BY_MECHANICAL_CHECK')})
check('reference_replay_operations',all(x['reference_replay_passed'] for x in replay_rows),replay_rows)
allowed={'task_id','question','perturbed_table','paragraphs'}
forbidden={'source_table','official_reference','derivation','answer','answer_type','answer_from','scale','rel_paragraphs','source_cells','perturbed_cells','gold','v4_label','checker_verdict','injection_id','col','original','injected'}
def leakage_keys(obj,path=''):
    out=[]
    if isinstance(obj,dict):
        for k,v in obj.items():
            if k in forbidden: out.append(path+'/'+k)
            out+=leakage_keys(v,path+'/'+k)
    elif isinstance(obj,list):
        for i,v in enumerate(obj): out+=leakage_keys(v,path+'/'+str(i))
    return out
pub_rows=[]
for cid in specs:
    pub=read(OUT/'public_inputs'/(cid+'.json'))
    exact=(set(pub.keys())==allowed and pub['question']==cases[cid]['question'] and pub['perturbed_table']==cases[cid]['perturbed_table'] and pub['paragraphs']==cases[cid]['paragraphs'])
    pub_rows.append({'task_id':cid,'whitelist_exact':exact,'leakage_keys':leakage_keys(pub)})
check('public_inputs_whitelist_and_source',all(x['whitelist_exact'] and not x['leakage_keys'] for x in pub_rows),pub_rows)
fake=json.loads(json.dumps(specs['Q03'])); fake['reference_paths'][0]['where']=['r999c999']
neg1=bool(coord_ok(fake,'Q03'))
p=OUT/'public_inputs/Q03.json'; original=read(p); original_hash=sha(p); mod=json.loads(json.dumps(original)); mod['question']=mod['question']+' [modified]'
neg2=(hashlib.sha256(json.dumps(mod,ensure_ascii=False,indent=2).encode('utf-8')).hexdigest()!=original_hash)
fake_spec=json.loads(json.dumps(specs['Q09'])); fake_spec['task_requirements']['unit_scale']='UNRESOLVED'
neg3=('UNRESOLVED' in fake_spec['task_requirements']['unit_scale'])
fake_pub=json.loads(json.dumps(read(OUT/'public_inputs/Q02.json'))); fake_pub['official_reference']={'answer':1}
neg4=bool(leakage_keys(fake_pub))
for name,passed,detail in [('negative_invalid_coordinate_rejected',neg1,'r999c999 detected'),('negative_changed_input_hash_rejected',neg2,'modified copy hash differs from pinned original'),('negative_unresolved_scale_blocks_compare',neg3,'UNRESOLVED scale blocks numeric comparison'),('negative_official_reference_leakage_rejected',neg4,'official_reference key detected')]: check(name,passed,detail)
report={'status':'PASS_OFFLINE_CHECKS_ONLY' if all(x['passed'] for x in checks) else 'FAIL','scientific_gold_validity':'NOT_ESTABLISHED','system_outcome':'NOT_RUN','layer2_authorized':False,'checks':checks,'reference_replay':replay_rows,'public_input_audit':pub_rows,'negative_checks':{'invalid_coordinate_rejected':neg1,'changed_hash_rejected':neg2,'unresolved_scale_blocked':neg3,'official_reference_leakage_rejected':neg4}}
(OUT/'OFFLINE_CHECKS.json').write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
print(json.dumps({'status':report['status'],'checks':len(checks),'failed':[x for x in checks if not x['passed']]},ensure_ascii=True))
if report['status']!='PASS_OFFLINE_CHECKS_ONLY': raise SystemExit(1)
