"""Pure last-complete-tool-round projection of an OpenAI chat payload.

Anchor roles are never removed or rewritten. IDs are local to each tool batch;
function argument semantics are preserved, not interpreted. No relay integration.
"""
from __future__ import annotations

import copy
import hashlib
import json


def _canonical_hash(payload):
    try:
        raw=json.dumps(payload,ensure_ascii=False,sort_keys=True,
                       separators=(',',':'),allow_nan=False).encode('utf8')
    except (ValueError,TypeError,UnicodeError) as exc:
        raise ValueError('payload must be finite, serializable JSON') from exc
    return hashlib.sha256(raw).hexdigest()


def project_last_tool_rounds(payload,k=3):
    """Return a deep copy and structural proof, without adding observations.

    A round is one assistant tool-call batch followed by exactly one tool reply
    per local ID, before another role may appear. Reply order may differ from
    call order; IDs may be reused by later complete rounds. If pruning is needed,
    cutoff is the oldest kept batch's assistant, or after the last batch for k=0.
    Ordinary assistant content at/after cutoff stays, and all anchor roles stay.
    At most k complete rounds means every message remains byte-equivalent JSON.
    """
    if type(payload) is not dict or type(payload.get('messages')) is not list:
        raise ValueError('payload requires a messages list')
    if type(k) is not int or k<0:
        raise ValueError('k must be a nonnegative integer')
    original_hash=_canonical_hash(payload)
    messages=payload['messages'];rounds=[];pending=None;start=None
    anchors={'system','developer','user'}
    for index,message in enumerate(messages):
        if type(message) is not dict or type(message.get('role')) is not str or message['role'] not in anchors|{'assistant','tool'}:
            raise ValueError(f'message {index}: unsupported message role')
        role=message['role']
        if role=='tool':
            reply=message.get('tool_call_id')
            if (pending is None or type(reply) is not str or reply not in pending):
                raise ValueError(f'message {index}: dangling, duplicate or unmatched tool reply')
            pending.remove(reply)
            if not pending:
                rounds.append((start,index));pending=None
            continue
        if pending is not None:
            raise ValueError(f'message {index}: incomplete tool round before next role')
        calls=message.get('tool_calls')
        if role!='assistant':
            if calls is not None:
                raise ValueError(f'message {index}: tool calls require assistant role')
            continue
        if calls is None or calls==[]:
            continue
        if type(calls) is not list:
            raise ValueError(f'message {index}: tool calls must be a list')
        ids=[]
        for call in calls:
            if type(call) is not dict or type(call.get('id')) is not str or not call['id'].strip():
                raise ValueError(f'message {index}: missing local tool-call ID')
            ids.append(call['id'])
        if len(set(ids))!=len(ids):
            raise ValueError(f'message {index}: duplicate tool-call ID in one batch')
        pending=set(ids);start=index
    if pending is not None:
        raise ValueError('payload ends with an incomplete tool round')
    count=len(rounds)
    cutoff=0 if count<=k else rounds[-k][0] if k else rounds[-1][1]+1
    kept=[i for i,message in enumerate(messages)
          if i>=cutoff or message['role'] in anchors]
    kept_set=set(kept);removed=[i for i in range(len(messages)) if i not in kept_set]
    projected=copy.deepcopy(payload)
    projected['messages']=[projected['messages'][i] for i in kept]
    retained=min(count,k)
    proof={'original_sha256':original_hash,'projected_sha256':_canonical_hash(projected),
           'kept_indices':kept,'removed_indices':removed,
           'original_round_count':count,'kept_round_count':retained,
           'removed_round_count':count-retained}
    return projected,proof
