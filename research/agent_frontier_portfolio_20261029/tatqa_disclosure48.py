"""Fresh TAT-QA contexts for a fixed-budget teacher disclosure comparison."""

import argparse
import copy
import getpass
import hashlib
import importlib.util
import json
from math import isfinite
import os
from pathlib import Path
import random
import shutil
import time
import traceback

import tatqa_transfer as transfer


task = transfer.task
m = transfer.m
ROOT = transfer.BASE / 'disclosure_paired48_v1'
CASES = 48
PRIMARY_K = 14
ARM_ORDER_SEED = 20261118
TOKEN_CAP = 1_000_000


def packet(arm, index):
    return transfer.packet_at(ROOT, arm, index)


def select_cases(source, excluded):
    """Use one arithmetic question per unseen table, ordered by public UID."""
    candidates = []
    for record in source:
        table_uid = record['table']['uid']
        if table_uid in excluded:
            continue
        for question in record['questions']:
            if question['answer_type'] == 'arithmetic':
                key = hashlib.sha256(('tatqa-disclosure-48-v1|' + question['uid']).encode()).hexdigest()
                candidates.append((key, table_uid, record, question))
    chosen = []
    seen = set(excluded)
    for _, table_uid, record, question in sorted(candidates, key=lambda row: row[0]):
        if table_uid not in seen:
            seen.add(table_uid)
            chosen.append((table_uid, record, question))
        if len(chosen) == CASES:
            return chosen
    raise ValueError('not enough unused arithmetic table contexts')


def prepare():
    if ROOT.exists():
        raise RuntimeError('fresh TAT-QA context panel already exists')
    prior = m.read(transfer.ORIGINAL / 'PLAN.json')
    source_path = Path(m.read(transfer.BASE / 'related_dev_v1/PREPARATION.json')['source_path'])
    excluded = set()
    for path in transfer.BASE.rglob('public.json'):
        public = m.read(path)
        report = str(public.get('report', ''))
        if report.startswith('TAT-QA/'):
            excluded.add(report.split('/', 1)[1])
    chosen = select_cases(m.read(source_path), excluded)
    template = transfer.packet_at(transfer.ORIGINAL, 'firstpass', prior['episodes'][0]['index']) / 'inputs'

    ROOT.mkdir(mode=0o700)
    episodes, labels = [], []
    for index, (table_uid, record, question) in enumerate(chosen):
        public = task.public_record(record, question)
        folder = packet('firstpass', index)
        inputs = folder / 'inputs'
        inputs.mkdir(parents=True)
        (folder / 'work').mkdir()
        (folder / 'dependencies').mkdir()
        (inputs / 'public.json').write_text(json.dumps(public, ensure_ascii=False))
        (inputs / 'task.txt').write_text(task.prompt(public, terminal_program=True))
        for name in ('finqa_tool.py', 'finqa_correction.py', 'executor.py', 'guest.py'):
            shutil.copyfile(template / name, inputs / name)
        episodes.append(dict(index=index, id=public['id'], report=public['report'], table_uid=table_uid))
        labels.append(dict(index=index, id=public['id'], report=public['report'], exe_ans=question))

    plan = copy.deepcopy(prior)
    plan.update(episodes=episodes, source_path=str(source_path), excluded_previous_tables=sorted(excluded),
                primary_K=PRIMARY_K, budgets=[0, PRIMARY_K], prospective_complete=True,
                selection='One arithmetic question per previously unused table, fixed public UID hash order.',
                scope='48 candidate contexts. Local settings inherited from the original TAT-QA transfer. '
                'The disclosure policy is frozen separately before new teacher execution.',
                stop='Keep completed and failed attempts. Local actor and physical teacher budget caps apply.')
    m.study.new(ROOT / 'LABELS_PRIVATE.json', labels)
    m.study.new(ROOT / 'PLAN.json', plan)
    print(json.dumps(dict(prepared=CASES, unique_tables=len({row['table_uid'] for row in episodes}),
                          excluded_previous_tables=len(excluded), primary_K=PRIMARY_K,
                          teacher_posts=0, local_inference=0, policy='UNSET')), flush=True)


def local():
    if not (ROOT / 'PLAN.json').is_file():
        raise RuntimeError('prepare the candidate contexts first')
    transfer.ROOT = ROOT
    transfer.local_run(strong_budget=PRIMARY_K, freeze=False)
    if m.read(ROOT / 'RUN_RESULT.json')['status'] != 'RETURNED':
        raise RuntimeError('local TAT-QA execution failed; inspect its result')


def load_scores(path, episodes, field='score'):
    rows = m.read(path)['decisions']
    by_index = {row['index']: row for row in rows}
    if len(rows) != len(episodes) or set(by_index) != {row['index'] for row in episodes}:
        raise ValueError('score panel does not match context indices')
    if any(by_index[row['index']]['id'] != row['id'] for row in episodes):
        raise ValueError('score panel does not match context IDs')

    def value(row):
        for component in field.split('.'):
            row = row[component]
        return row

    values = {index: value(row) for index, row in by_index.items()}
    if any(not isfinite(score) for score in values.values()):
        raise ValueError('all frozen scores must be finite')
    return values


def route_modes(selected, scores, t1_count, direction):
    """Assign prior-ranked seats inside the selected pool with a stable index tie break."""
    if not 0 <= t1_count <= len(selected) or direction not in ('highest', 'lowest'):
        raise ValueError('T1 seat count must be within K and direction must be highest or lowest')
    sign = -1 if direction == 'highest' else 1
    t1 = set(sorted(selected, key=lambda i: (sign * scores[i], i))[:t1_count])
    return {index: 'T1' if index in t1 else 'T0' for index in selected}


def comparison_prompt(public, initial, current=None):
    common = task.review_prompt(public, initial)
    common += ('\n\nIf a later local state is supplied below, treat it as an unverified candidate. '
               'Assess any supplied state against the same question, report and execution. '
               'You are using the original workspace and the same final-program and final-scale contract.\n'
               'Later local state:\n')
    return common + json.dumps(current, ensure_ascii=False)


def freeze(scores_path, score_field, t1_count, direction):
    if (ROOT / 'POLICIES.json').exists():
        raise RuntimeError('disclosure policy already frozen')
    run = m.read(ROOT / 'RUN_RESULT.json')
    if run['status'] != 'RETURNED' or run['phase'] != 'AWAITING_POLICY_FREEZE':
        raise RuntimeError('local actor and score panel must finish before freeze')
    episodes = m.read(ROOT / 'PLAN.json')['episodes']
    value = load_scores(ROOT / 'value_PREDICTIONS.json', episodes)
    scores = load_scores(scores_path or ROOT / 'risk_PREDICTIONS.json', episodes, field=score_field)
    selected = sorted(value, key=lambda i: (-value[i], i))[:PRIMARY_K]
    mixed = route_modes(selected, scores, t1_count, direction)

    rng = random.Random(ARM_ORDER_SEED)
    schedule = []
    visit = list(selected)
    rng.shuffle(visit)
    for index in visit:
        source = packet('firstpass', index)
        public = m.read(source / 'inputs/public.json')
        initial = task.saved_state(public, source / 'work')
        current = task.saved_state(public, packet('paired', index) / 'work')
        arms = ['T0', 'T1']
        if rng.randrange(2):
            arms.reverse()
        for arm in arms:
            target = packet(arm, index)
            for name in ('inputs', 'work', 'dependencies'):
                shutil.copytree(source / name, target / name)
            states = dict(T0=None, T1=current)
            (target / 'inputs/task.txt').write_text(comparison_prompt(public, initial, states[arm]))
            schedule.append(dict(index=index, arm=arm))

    m.study.new(ROOT / 'POLICIES.json', dict(primary_K=PRIMARY_K, selected=selected, mixed=mixed,
                direction=direction, score_field=score_field, disclosure_scores={i: scores[i] for i in selected},
                score_source=str(scores_path or ROOT / 'risk_PREDICTIONS.json'), t1_count=t1_count,
                arm_order_seed=ARM_ORDER_SEED, schedule=schedule,
                scope='All compared disclosure policies share the same frozen value-selected K. '
                'Each selected context receives a newly executed, interleaved T0/T1 pair.'))
    print(json.dumps(dict(primary_K=PRIMARY_K, T1=t1_count, T0=PRIMARY_K - t1_count,
                          planned_teacher_episodes=len(schedule))), flush=True)


def summary(local, grades, policy, resource):
    chosen = policy['selected']
    arms = {(row['index'], row['arm']): row for row in resource['episodes']}
    if set(arms) != {(index, arm) for index in chosen for arm in ('T0', 'T1')}:
        raise ValueError('fixed paired schedule is incomplete')
    workloads = {
        'T0': {index: 'T0' for index in chosen},
        'T1': {index: 'T1' for index in chosen},
        'mixed': {index: policy['mixed'][str(index)] for index in chosen},
    }
    results = dict(local={arm: sum(r['success'] for r in local[arm]) for arm in local},
                   primary={}, primary_K=PRIMARY_K, cases=CASES)
    baseline = results['local']['paired']

    def case_metrics(rows):
        return dict(
            correct_after=sum(r['after'] for r in rows),
            recovered=sum(not r['before'] and r['after'] for r in rows),
            damaged=sum(r['before'] and not r['after'] for r in rows),
            initially_wrong=sum(not r['before'] for r in rows), initially_correct=sum(r['before'] for r in rows),
            teacher_tasks=len(rows), teacher_posts=sum(r['posts'] for r in rows),
            teacher_tokens=sum(r['tokens'] for r in rows), teacher_unknown=sum(r['unknown'] for r in rows),
            teacher_actor_seconds=sum(r['seconds'] for r in rows))

    def paired_disagreements(indices):
        wins = sum(arms[i, 'T1']['after'] and not arms[i, 'T0']['after'] for i in indices)
        losses = sum(arms[i, 'T0']['after'] and not arms[i, 'T1']['after'] for i in indices)
        return dict(T1_wins=wins, T0_wins=losses, T1_minus_T0=wins-losses)

    for policy_name, workload in workloads.items():
        metrics = case_metrics([arms[index, arm] for index, arm in workload.items()])
        metrics['success'] = baseline + metrics['recovered'] - metrics['damaged']
        results['primary'][policy_name] = metrics
    results['paired_disagreements'] = paired_disagreements(chosen)
    results['within_K_by_mixed_mode'] = {}
    for mixed_mode in ('T0', 'T1'):
        indices = [index for index, mode in workloads['mixed'].items() if mode == mixed_mode]
        results['within_K_by_mixed_mode'][mixed_mode] = dict(
            T0=case_metrics([arms[i, 'T0'] for i in indices]), T1=case_metrics([arms[i, 'T1'] for i in indices]),
            paired=paired_disagreements(indices))

    # Reuse the original manuscript operator if its local file is available.
    scale_path = transfer.BASE / 'TATQA_MANUSCRIPT_FOLLOWUP.py'
    if scale_path.is_file():
        spec = importlib.util.spec_from_file_location('_tatqa_manuscript_scale', scale_path)
        scale = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(scale)

        def count(rows):
            successes = 0
            for index, submission, normal in rows:
                public, grade = grades[index]
                updated = scale.predicted_scale(submission, public['question'], 'structured')
                successes += bool(normal and grade(updated))
            return successes

        results['structured_scale_secondary'] = dict(local={name: count((r['index'], r['submission'], r['normal']) for r in rows)
                                                             for name, rows in local.items()}, primary={})
        for policy_name, workload in workloads.items():
            substitutions = {index: arms[index, arm] for index, arm in workload.items()}
            selected = []
            for row in local['paired']:
                index = row['index']
                if index in substitutions:
                    replacement = substitutions[index]
                    selected.append((index, replacement['selected'], replacement['selected_normal']))
                else:
                    selected.append((index, row['submission'], row['normal']))
            results['structured_scale_secondary']['primary'][policy_name] = count(selected)
    return results


def teacher(key):
    from scripts.graph.research_school_gateway import (
        BASE_URL, MODEL, REQUEST_TOKEN_CEILING, BatchBudget, SchoolBackend,
    )

    if (ROOT / 'TEACHER_LIVE.json').exists():
        raise RuntimeError('teacher attempt exists; inspect it before running this panel again')
    plan = m.read(ROOT / 'PLAN.json')
    policy = m.read(ROOT / 'POLICIES.json')
    local_run = m.read(ROOT / 'LOCAL_RESULT.json')
    if local_run['status'] != 'RETURNED' or any(len(rows) != CASES for rows in local_run['arms'].values()):
        raise ValueError('local TAT-QA panel is incomplete')
    labels = {row['index']: row for row in m.read(ROOT / 'LABELS_PRIVATE.json')}
    chosen = set(policy['selected'])
    scheduled = {(row['index'], row['arm']) for row in policy['schedule']}
    if (len(chosen) != PRIMARY_K or len(policy['schedule']) != 2 * PRIMARY_K
            or scheduled != {(i, arm) for i in chosen for arm in ('T0', 'T1')}):
        raise ValueError('frozen teacher schedule does not cover each selected context twice')

    def grade(candidate, public, label):
        return task.grade(candidate, public, label['exe_ans'], metric_dir=plan['metric_dir'])

    def make_grader(public, label):
        return lambda candidate: grade(candidate, public, label)['execution_correct']

    grades = {}
    for index, label in labels.items():
        public = m.read(packet('firstpass', index) / 'inputs/public.json')
        if public['id'] != label['id']:
            raise ValueError('host-only label does not match public question')
        grades[index] = public, make_grader(public, label)
    locals_by_index = {row['index']: row for row in local_run['arms']['paired']}
    started = time.monotonic()
    state = dict(status='RUNNING', pid=os.getpid(), episodes=[], physical_campus={})
    m.study.new(ROOT / 'TEACHER_LIVE.json', state)
    budget = BatchBudget(ROOT / 'teacher_budget', posts=2 * PRIMARY_K * plan['caps']['posts'], tokens=TOKEN_CAP)

    def persist():
        charged = [r for r in budget.rows if r['state'] != 'not_sent']
        known = sum(r.get('usage', {}).get('total_tokens', 0) for r in charged)
        unknown = sum('usage' not in r for r in charged)
        state['physical_campus'].update(posts=len(charged), known_tokens=known, unknown_requests=unknown,
                                        unknown_reserve=unknown * REQUEST_TOKEN_CEILING,
                                        token_cap=TOKEN_CAP, seconds=time.monotonic() - started)
        m.study.publish(ROOT / 'TEACHER_LIVE.json', state)

    try:
        backend = SchoolBackend(key, budget, m.study.core)
        profile = dict(provider='bupt_chat_v1', base_url=BASE_URL, model_id=MODEL, context=262144, output=8192)
        backend.verify(profile)
        with m.study.core.resource_lock():
            h = m.study.core.helpers()
            checked = h.deps.verify_projection(h.actor.RUNTIME_ROOT, h.actor.RUNTIME_SHA)
            m.study.CAPS.clear()
            m.study.CAPS.update(plan['caps'])
            for item in policy['schedule']:
                if time.monotonic() - started > 5400:
                    raise TimeoutError('teacher disclosure wall cap')
                index, arm = item['index'], item['arm']
                folder = packet(arm, index)
                episode = dict(plan['episodes'][index], folder=str(folder))
                raw = m.study.episode(episode, h, checked, profile, private_labels=ROOT / 'LABELS_PRIVATE.json',
                                      relay_factory=backend.make_relay, submission_grader=grade)
                path = folder / 'work/candidate.json'
                proposal = m.read(path) if path.exists() else None
                fallback = locals_by_index[index]
                candidate = fallback['submission']
                keep = not raw['agent_completed'] or not raw['program_valid']
                if isinstance(candidate, dict) and isinstance(proposal, dict) and candidate['scale'] == proposal['scale']:
                    keep = keep or transfer.av.percent_scale_only(candidate['program'], proposal['program'])
                chosen_program = candidate if keep else proposal
                normal = fallback['normal'] if keep else raw['agent_completed']
                _, score = grades[index]
                counts = raw['accounting']
                state['episodes'].append(dict(index=index, arm=arm, before=fallback['success'],
                    after=bool(normal and score(chosen_program)), teacher_success=raw['native_success'],
                    guard_keep=keep, selected=chosen_program, selected_normal=normal, proposal=proposal,
                    posts=counts['actual_forwarded_posts'], tokens=counts['provider_total_tokens_known'],
                    unknown=len(counts['unknown_usage_requests']), seconds=raw['actor']['seconds']))
                persist()
                print(json.dumps(dict(done=len(state['episodes']), index=index, arm=arm,
                                      known_tokens=state['physical_campus']['known_tokens'])), flush=True)
                if not counts['integrity_passed']:
                    raise RuntimeError('teacher transport failure or cap reached; partial evidence retained')
        state['comparison'] = summary(local_run['arms'], grades, policy, state)
        state['status'] = 'RETURNED'
    except BaseException:
        state.update(status='FAILED', error=traceback.format_exc())
        raise
    finally:
        if budget.pending is not None:
            budget.finish()
        persist()
        budget.close()
        m.study.new(ROOT / 'TEACHER_RESULT.json', state)
    print(json.dumps(dict(comparison=state['comparison'], physical_campus=state['physical_campus'])), flush=True)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    commands = parser.add_subparsers(dest='command', required=True)
    for name in ('prepare', 'local', 'teacher'):
        commands.add_parser(name)
    setup = commands.add_parser('freeze')
    setup.add_argument('--scores', type=Path)
    setup.add_argument('--score-field', default='score')
    setup.add_argument('--t1-count', required=True, type=int)
    setup.add_argument('--direction', required=True, choices=('highest', 'lowest'))
    args = parser.parse_args()
    if args.command == 'freeze':
        freeze(args.scores, args.score_field, args.t1_count, args.direction)
    elif args.command == 'teacher':
        teacher(os.environ.get('BUPT_API_KEY') or getpass.getpass('Campus credential (hidden): '))
    else:
        {'prepare': prepare, 'local': local}[args.command]()


if __name__ == '__main__':
    main()
