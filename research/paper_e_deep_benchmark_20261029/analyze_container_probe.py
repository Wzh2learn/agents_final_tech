#!/usr/bin/env python3
"""Analyze recorded qualification/cases; deterministic regex, no judge."""
import hashlib,json,re,sys
from pathlib import Path
root=Path(sys.argv[1]); out={}
for case, filename in [('qualification','raw_agent_container_qualify.jsonl'),('current','raw_agent_container_current.jsonl'),('superseded','raw_agent_container_superseded.jsonl')]:
    path=root/filename; events=[json.loads(s) for s in path.read_text().splitlines()]
    texts=[r['part']['text'] for r in events if r.get('type')=='text']
    reads=[r['part'] for r in events if r.get('type')=='tool_use' and r.get('part',{}).get('tool')=='read']
    done=[r for r in reads if r.get('state',{}).get('status')=='completed']
    steps=[r['part']['tokens'] for r in events if r.get('type')=='step_finish' and 'tokens' in r.get('part',{})]
    status=re.findall(r'SourceStatus:\s*(CURRENT|SUPERSEDED)', '\n'.join(r['state'].get('output','') for r in done))
    final='\n'.join(texts)
    out[case]={'raw_sha256':hashlib.sha256(path.read_bytes()).hexdigest(),'completed_reads':len(done),'reported_statuses':status,'final_answer':final,'numeric_84':bool(re.search(r'\b84\b',final)),'steps':len(steps),'input_noncache':sum(t['input'] for t in steps),'cache_read':sum(t['cache']['read'] for t in steps),'output':sum(t['output'] for t in steps),'total':sum(t['total'] for t in steps)}
assert out['current']['reported_statuses']==['CURRENT']
assert out['superseded']['reported_statuses']==['SUPERSEDED']
assert out['current']['numeric_84'] and out['superseded']['numeric_84']
print(json.dumps(out,indent=2))
