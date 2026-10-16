import hashlib, json
from datetime import datetime, timezone
from pathlib import Path
B=Path('D:/AIRcommend/JinRongAgents/agents_final_tech/research/paper_e_layer1_20261015/scientific_qualification/task_gold_qualification_v1/')
OUT=B/'measurement_contract_v2'
def sha(p): return hashlib.sha256(Path(p).read_bytes()).hexdigest()
files=[]
for p in sorted(OUT.rglob('*')):
    if p.is_file() and p.name!='MANIFEST.json':
        files.append({'path':str(p.relative_to(OUT)).replace('\\','/'),'sha256':sha(p),'bytes':p.stat().st_size})
inputs={
 'stage2_cases':{'path':'packets/stage2_cases.json','sha256':sha(B/'packets/stage2_cases.json')},
 'case_provenance':{'path':'coordinator/case_provenance.json','sha256':sha(B/'coordinator/case_provenance.json')},
 'ai_annotations':{'path':'ai_assisted_review_v1/AI_ANNOTATIONS_v1.json','sha256':sha(B/'ai_assisted_review_v1/AI_ANNOTATIONS_v1.json')},
 'loop_d_review':{'path':'ai_assisted_review_v1/loop_d_review_v1/LOOP_D_CASE_REVIEW.json','sha256':sha(B/'ai_assisted_review_v1/loop_d_review_v1/LOOP_D_CASE_REVIEW.json')},
 'r3_card':{'path':'ai_assisted_review_v1/R3_NEXT_STEP_20261016.md','sha256':sha(B/'ai_assisted_review_v1/R3_NEXT_STEP_20261016.md')}
}
manifest={'schema':'tq2_measurement_contract_manifest_v1','generated_at_utc':datetime.now(timezone.utc).strftime('%Y-%m-%dT%H:%M:%SZ'),'status':'OFFLINE_CHECKS_PASS_TASK_GOLD_NOT_ESTABLISHED','actor_kind':'AI','human':False,'system_outcome':'NOT_RUN','scientific_gold_validity':'NOT_ESTABLISHED','layer2_authorized':False,'counts':{'reference_specs':9,'quarantine_cards':3,'public_inputs':9,'reference_replay_ready':6,'partial_reference_replay':3,'spec_blocked':0},'inputs':inputs,'files':files,'manifest_self_excluded':True}
(OUT/'MANIFEST.json').write_text(json.dumps(manifest,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
print(json.dumps({'manifest_files':len(files)},ensure_ascii=True))
