"""Research candidate: select probes by repair-action value, not label entropy.

The decision-theoretic quantities are standard; this code does not establish
novelty or trust a model's counterfactual predictions as observed evidence.
"""
from __future__ import annotations

import ast
from collections import defaultdict
import json
import math
import re


def _unique(pairs):
    result = {}
    for key, value in pairs:
        if key in result:
            raise ValueError('duplicate JSON key')
        result[key] = value
    return result


def parse_plan(text, state_sha256):
    if not isinstance(text, str) or len(text.encode('utf-8')) > 32768:
        raise ValueError('bounded whole JSON required')
    plan = json.loads(text, object_pairs_hook=_unique)
    if set(plan) != {'state_sha256', 'actions', 'hypotheses', 'probes'}:
        raise ValueError('exact plan fields required')
    if plan['state_sha256'] != state_sha256 or not re.fullmatch('[0-9a-f]{64}', state_sha256):
        raise ValueError('plan belongs to a different state')
    if not (1 <= len(plan['actions']) <= 4 and 2 <= len(plan['hypotheses']) <= 6
            and 1 <= len(plan['probes']) <= 4):
        raise ValueError('bounded action/hypothesis/probe sets required')
    groups = (plan['actions'], plan['hypotheses'], plan['probes'])
    for group in groups:
        ids = [item['id'] for item in group]
        if len(set(ids)) != len(ids) or any(not re.fullmatch('[A-Za-z][A-Za-z0-9_]{0,31}', x) for x in ids):
            raise ValueError('unique bounded identifiers required')
    action_ids = {x['id'] for x in plan['actions']}
    hypothesis_ids = {x['id'] for x in plan['hypotheses']}
    for item in plan['actions']:
        if set(item) != {'id', 'change'} or not isinstance(item['change'], str) or not 1 <= len(item['change']) <= 1200:
            raise ValueError('concrete action description required')
    for item in plan['hypotheses']:
        if set(item) != {'id', 'premise', 'action_id', 'weight'} or item['action_id'] not in action_ids:
            raise ValueError('hypothesis needs an admitted repair action')
        if not isinstance(item['premise'], str) or not 1 <= len(item['premise']) <= 1200:
            raise ValueError('bounded premise required')
        if type(item['weight']) not in (int, float) or not math.isfinite(item['weight']) or item['weight'] <= 0:
            raise ValueError('finite positive hypothesis weights required')
    for item in plan['probes']:
        if set(item) != {'id', 'role', 'python', 'predictions', 'cost'}:
            raise ValueError('exact probe fields required')
        if item['role'] not in ('public_reproduction', 'api_shape', 'related_behavior'):
            raise ValueError('public probe role required')
        if type(item['cost']) not in (int, float) or not math.isfinite(item['cost']) or item['cost'] <= 0:
            raise ValueError('finite positive nominal cost required')
        if not isinstance(item['python'], str) or not 1 <= len(item['python']) <= 6000:
            raise ValueError('bounded Python probe required')
        ast.parse(item['python'])  # Syntax only, not an execution permission or safety proof.
        if set(item['predictions']) != hypothesis_ids or any(
            not isinstance(x, str) or not 1 <= len(x) <= 80 for x in item['predictions'].values()
        ):
            raise ValueError('one predicted outcome per hypothesis required')
    total = sum(x['weight'] for x in plan['hypotheses'])
    if not math.isfinite(total) or total <= 0:
        raise ValueError('finite positive total weight required')
    for item in plan['hypotheses']:
        item['weight'] /= total
    return plan


def uncertainty(hypotheses, objective):
    if objective == 'hypothesis_entropy':
        return -sum(x['weight'] * math.log(x['weight']) for x in hypotheses)
    if objective != 'repair_action':
        raise ValueError('unknown objective')
    weights = defaultdict(float)
    for item in hypotheses:
        weights[item['action_id']] += item['weight']
    return 1.0 - max(weights.values())


def probe_value(plan, probe, objective='repair_action'):
    groups = defaultdict(list)
    for hypothesis in plan['hypotheses']:
        groups[probe['predictions'][hypothesis['id']]].append(hypothesis)
    remaining = 0.0
    for group in groups.values():
        mass = sum(x['weight'] for x in group)
        posterior = [{**x, 'weight': x['weight'] / mass} for x in group]
        remaining += mass * uncertainty(posterior, objective)
    gain = max(0.0, uncertainty(plan['hypotheses'], objective) - remaining)
    return {'id': probe['id'], 'gain': gain, 'nominal_cost': probe['cost'],
            'value_per_cost': gain / probe['cost']}


def select_probe(plan, objective='repair_action'):
    values = [probe_value(plan, probe, objective) for probe in plan['probes']]
    best = sorted(values, key=lambda x: (-x['value_per_cost'], x['nominal_cost'], x['id']))[0]
    return {'selected': best['id'] if best['gain'] > 1e-12 else None,
            'objective': objective, 'values': values}


def update_from_observation(plan, probe_id, outcome):
    probe = next(x for x in plan['probes'] if x['id'] == probe_id)
    kept = [x for x in plan['hypotheses'] if probe['predictions'][x['id']] == outcome]
    if not kept:
        return {'status': 'UNPREDICTED_OBSERVATION', 'hypotheses': plan['hypotheses']}
    total = sum(x['weight'] for x in kept)
    return {'status': 'CONDITIONAL_ON_MODEL_PREDICTIONS',
            'hypotheses': [{**x, 'weight': x['weight'] / total} for x in kept]}
