import json, re

def last_user(obs):
    for m in reversed(obs.get('messages', [])):
        if m.get('role') == 'user':
            return m.get('content', '')
    return ''

def last_assistant_say(obs):
    for m in reversed(obs.get('messages', [])):
        if m.get('role') == 'assistant' and 'content' in m:
            return m.get('content', '')
    return ''

def extract_phone(text):
    m = re.search('(\\d{3}[-.]?\\d{3}[-.]?\\d{4})', text)
    return m.group(1) if m else ''

def extract_gb(text):
    m = re.search('(\\d+(?:\\.\\d+)?)\\s*GB', text, re.I)
    return min(float(m.group(1)), 2.0) if m else 2.0

def tool_results(obs):
    out = []
    for m in obs.get('messages', []):
        if m.get('role') == 'tool':
            try:
                out.append(json.loads(m.get('content', '')))
            except Exception:
                pass
    return out

def assistant_calls(obs):
    calls = []
    for m in obs.get('messages', []):
        if m.get('role') == 'assistant' and m.get('tool_calls'):
            for tc in m['tool_calls']:
                calls.append(tc)
    return calls

def history_candidate_step(observation, memory):
    if observation.get('done'):
        return {'kind': 'stop', 'memory': memory}
    msgs = observation.get('messages', [])
    user_text = last_user(observation)
    user = user_text.lower()
    last_say = last_assistant_say(observation).lower()
    results = tool_results(observation)
    calls = assistant_calls(observation)
    cust = None
    for r in results:
        if 'customer_id' in r and 'line_ids' in r:
            cust = r
            break
    if not cust:
        return {'kind': 'yield', 'memory': memory, 'reason': 'Customer not identified.'}
    phone = extract_phone(' '.join((m.get('content', '') for m in msgs if m.get('role') == 'user')))
    line = None
    for r in results:
        if 'line_id' in r and r.get('phone_number') == phone:
            line = r
            break
    if not line:
        return {'kind': 'yield', 'memory': memory, 'reason': 'Line not identified.'}
    customer_id = cust['customer_id']
    line_id = line['line_id']
    roaming_enabled = line.get('roaming_enabled', False)
    enabled_roaming = any((c.get('name') == 'enable_roaming' for c in calls))
    full_user = ' '.join((m.get('content', '') for m in msgs if m.get('role') == 'user')).lower()
    traveling = any((k in full_user for k in ['abroad', 'travel', 'france', 'outside', 'roaming']))
    proposed = observation.get('proposed_operation')
    if proposed is not None and proposed.get('name') == 'refuel_data':
        refueled = 0.0
        for r in results:
            if 'data_used_gb' in r and 'data_limit_gb' in r:
                refueled = float(r.get('data_refueling_gb', 0))
        if refueled > 0 and (not roaming_enabled) and (not enabled_roaming) and traveling:
            return {'kind': 'act', 'name': 'enable_roaming', 'arguments': {'customer_id': customer_id, 'line_id': line_id}, 'memory': memory}
    if proposed is not None:
        return {'kind': 'yield', 'memory': memory, 'reason': 'Actor proposal pending.'}
    if not roaming_enabled and (not enabled_roaming):
        if 'roaming' in user and any((k in user for k in ['no connection', 'failed', 'not working', 'no internet', 'still fails'])):
            return {'kind': 'act', 'name': 'enable_roaming', 'arguments': {'customer_id': customer_id, 'line_id': line_id}, 'memory': memory}
    usage = None
    for r in results:
        if 'data_used_gb' in r and 'data_limit_gb' in r:
            usage = r
    if usage:
        used = float(usage.get('data_used_gb', 0))
        limit = float(usage.get('data_limit_gb', 0))
        refueled = float(usage.get('data_refueling_gb', 0))
        already = any((c.get('name') == 'refuel_data' for c in calls))
        if used > limit and refueled == 0 and (not already):
            if 'shall i proceed' in last_say or 'cost' in last_say:
                if any((k in user for k in ['yes', 'proceed', 'go ahead', 'confirm'])):
                    gb = extract_gb(user_text)
                    return {'kind': 'act', 'name': 'refuel_data', 'arguments': {'customer_id': customer_id, 'line_id': line_id, 'gb_amount': gb}, 'memory': memory}
    return {'kind': 'yield', 'memory': memory, 'reason': 'No supported correction.'}

def step(observation, memory):
    for message in observation.get('messages', []):
        if message.get('content') is None:
            message.pop('content', None)
    decision = history_candidate_step(observation, {})
    decision['memory'] = {}
    return decision
