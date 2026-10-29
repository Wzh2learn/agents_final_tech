#!/usr/bin/env python3
"""Recompute from frozen reference and raw OpenCode events, no model calls."""
import hashlib,json,re,sys
from pathlib import Path
root=Path(sys.argv[1]); refs=json.loads((root/'reference_hidden.json').read_text()); out={}
for case in ('migration_base','migration_prose','scifact_1','scifact_2'):
    raw=root/f'raw_agent_container_{case}.jsonl'; data=[json.loads(x) for x in raw.read_text().splitlines()]
    last='\n'.join(r['part']['text'] for r in data if r.get('type')=='text')
    reads=[r['part'] for r in data if r.get('type')=='tool_use' and r.get('part',{}).get('tool')=='read']
    paths=[r.get('state',{}).get('input',{}).get('filePath') for r in reads if r.get('state',{}).get('status')=='completed']
    usage=[r['part']['tokens'] for r in data if r.get('type')=='step_finish' and 'tokens' in r.get('part',{})]
    pat=r'VERDICT\s*:\s*(INVALID|VALID)\b' if case.startswith('migration') else r'CHOICE\s*:\s*([AB])\b'
    found=re.findall(pat,last,re.I); chosen=found[-1].upper() if len(found)==1 else None
    receipt=json.loads((root/f'container_{case}_receipt.json').read_text()); ref=refs[case]
    row={'agent_output':last,'parsed':chosen,'completed_read_paths':paths,'read_count':len(paths),'raw_sha256':hashlib.sha256(raw.read_bytes()).hexdigest(),'http_count':sum(x=='POST /v1/chat/completions' for x in receipt['allowed_model_http_requests']),'elapsed_seconds':receipt['elapsed_seconds'],'usage':{'input_noncache':sum(t['input'] for t in usage),'cache_read':sum(t['cache']['read'] for t in usage),'output':sum(t['output'] for t in usage),'total':sum(t['total'] for t in usage)}}
    if case.startswith('migration'):
        row.update({'reference_contract':ref['oracle'],'agent_contract_match':None if chosen is None else chosen==ref['oracle'],'historical_test_only':'VALID (7/7 historical tests)', 'required_evidence_seen':any(str(p).endswith('/module.py') for p in paths)})
    else:
        # Historical frozen reference predates qrel_status; use explicit IDs only.
        if chosen is None: label=None
        elif 'qrel_status' in ref: label=ref['qrel_status'][chosen]
        elif ref[chosen]==ref['positive_doc']: label='QRELS_POSITIVE'
        elif ref[chosen]==ref['unjudged_doc']: label='UNJUDGED'
        else: label='REFERENCE_INCOMPLETE'
        row.update({'agent_judgment':label,'bm25_choice':ref['bm25_baseline'],'bm25_judgment':'UNJUDGED','qid':ref['qid'],'required_evidence_seen':all(any(str(p).endswith('/'+f) for p in paths) for f in ['query.txt','A.txt','B.txt'])})
    out[case]=row
print(json.dumps(out,indent=2,ensure_ascii=False))
