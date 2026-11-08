"""Synthetic CPU contract controls; none of these are experiment results."""
import copy
from dataclasses import replace
import hashlib
from pathlib import Path
import sys

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'research/agent_frontier_portfolio_20261029'))
from feedback_context_policy import Fragment, NativeOutcome, Usage, public_input_hashes, reference_candidates, summarize_factorial


def sha(raw):
    return hashlib.sha256(raw).hexdigest()


def fragments_for(pieces):
    parts = []
    start = 0
    for index, text in enumerate(pieces):
        raw = text.encode('utf8')
        parts.append(Fragment(str(index), start, start + len(raw), sha(raw)))
        start += len(raw)
    return parts


def test_utf8_boundary_must_not_split_a_character():
    raw = '学a'.encode('utf8')
    parts = [Fragment('a', 0, 1, sha(raw[:1])), Fragment('b', 1, len(raw), sha(raw[1:]))]
    with pytest.raises(ValueError, match='UTF-8'):
        reference_candidates(raw, sha(raw), parts, goal={}, observation={}, progress={})


@pytest.mark.parametrize('kind', ['gap', 'overlap', 'missing_tail', 'wrong_hash', 'duplicate_id', 'too_many'])
def test_fragments_must_be_disjoint_complete_and_bound(kind):
    raw = b'abcdefg'
    if kind == 'gap':
        parts = [Fragment('a', 0, 2, sha(raw[:2])), Fragment('b', 3, 7, sha(raw[3:]))]
    elif kind == 'overlap':
        parts = [Fragment('a', 0, 4, sha(raw[:4])), Fragment('b', 3, 7, sha(raw[3:]))]
    elif kind == 'missing_tail':
        parts = [Fragment('a', 0, 6, sha(raw[:6]))]
    elif kind == 'wrong_hash':
        parts = [Fragment('a', 0, 7, '0' * 64)]
    elif kind == 'duplicate_id':
        parts = [Fragment('a', 0, 3, sha(raw[:3])), Fragment('a', 3, 7, sha(raw[3:]))]
    else:
        parts = [Fragment(str(i), i, i + 1, sha(raw[i:i+1])) for i in range(7)]
    with pytest.raises(ValueError):
        reference_candidates(raw, sha(raw), parts, goal={}, observation={}, progress={})


def test_masks_are_verbatim_and_public_objects_remain_unchanged():
    pieces = ['烤苹果\n', '拿起🧺\n', '放到桌面']
    raw = ''.join(pieces).encode('utf8')
    goal = {'instruction': '完成任务'}
    observation = {'visible': ['苹果', '桌面'], 'done': False}
    progress = {'accepted_actions': ['look'], 'budget': {'remaining': 7}}
    original = copy.deepcopy((goal, observation, progress))
    result = reference_candidates(raw, sha(raw), fragments_for(pieces),
                                  goal=goal, observation=observation, progress=progress)
    candidates = {row['mask']: row for row in result['candidates']}
    assert len(candidates) == 8
    assert candidates['000']['reference_text'] == ''
    assert candidates['111']['reference_text'].encode('utf8') == raw
    assert candidates['101']['reference_text'] == pieces[0] + pieces[2]
    assert [p['fragment_id'] for p in candidates['101']['fragments']] == ['0', '2']
    assert candidates['101']['reference_sha256'] == sha((pieces[0] + pieces[2]).encode('utf8'))
    assert (goal, observation, progress) == original
    assert result['public_hashes_before'] == result['public_hashes_after'] == public_input_hashes(
        goal=goal, observation=observation, progress=progress)


def test_six_fragments_produce_at_most_sixty_four_masks():
    pieces = ['甲', '乙', '丙', '丁', '戊', '己']
    raw = ''.join(pieces).encode('utf8')
    candidates = reference_candidates(raw, sha(raw), fragments_for(pieces), goal='', observation={}, progress=[])
    assert len(candidates['candidates']) == 64
    assert candidates['candidates'][-1]['reference_text'].encode('utf8') == raw


def test_deleted_middle_does_not_join_words_into_new_text():
    pieces = ['甲', '中间', '乙']
    raw = ''.join(pieces).encode('utf8')
    rows = reference_candidates(raw, sha(raw), fragments_for(pieces), goal='', observation={}, progress=[])
    selected = next(row for row in rows['candidates'] if row['mask'] == '101')
    assert selected['reference_text'] == '甲\n乙'
    assert selected['inserted_newline_separators'] == 1


def outcomes(task, layout, actor, prefix, seed, wins, usage=None):
    return [NativeOutcome(task, layout, actor, prefix, seed, mask,
                          f'{task}:{layout}:{actor}:{seed}:{mask}',
                          sha(f'{task}:{layout}:{actor}:{seed}:{mask}'.encode()), done=True, won=bool(wins[mask]),
                          outcome_verified=True, finish_reason='native_terminal', interface_ok=True,
                          usage=usage or Usage(posts=1, input_tokens=10, cached_input_tokens=4, output_tokens=2, wall_seconds=1.0))
            for mask in ('00', '10', '01', '11')]


@pytest.mark.parametrize(('wins', 'expected'), [
    ({'00': 0, '10': 0, '01': 0, '11': 1}, 1.0),
    ({'00': 0, '10': 1, '01': 1, '11': 1}, -1.0),
    ({'00': 0, '10': 1, '01': 0, '11': 1}, 0.0),
])
def test_interaction_for_synergy_redundancy_and_additive_controls(wins, expected):
    result = summarize_factorial(outcomes('task', 'layout', 'actor', 'a' * 64, 17, wins))
    assert result['tasks'][0]['interaction'] == expected
    assert result['layout_groups'][0]['interaction_mean'] == expected
    assert result['layout_groups'][0]['task_count'] == 1
    assert result['formation_and_training_costs'] is None


@pytest.mark.parametrize('bad', ['unknown_finish', 'still_running', 'false_native_terminal',
                                 'interface_fault', 'unverified_outcome', 'unverified_stopped',
                                 'faulted_stopped', 'missing_finish'])
def test_unknown_or_faulted_results_are_not_failures(bad):
    rows = outcomes('task', 'layout', 'actor', 'b' * 64, 17, {'00': 0, '10': 0, '01': 0, '11': 1})
    changes = {'unknown_finish': {'done': False, 'won': False, 'finish_reason': 'unknown'},
               'still_running': {'done': False, 'won': False, 'finish_reason': 'running'},
               'false_native_terminal': {'done': False, 'won': False, 'finish_reason': 'native_terminal'},
               'interface_fault': {'interface_ok': False}, 'unverified_outcome': {'outcome_verified': False},
               'unverified_stopped': {'done': False, 'won': False, 'finish_reason': 'controller_stop',
                                      'outcome_verified': False},
               'faulted_stopped': {'done': False, 'won': False, 'finish_reason': 'budget_exhausted',
                                   'interface_ok': False},
               'missing_finish': {'done': False, 'won': False, 'finish_reason': None}}
    rows[0] = replace(rows[0], **changes[bad])
    with pytest.raises(ValueError, match='verified completed native outcomes'):
        summarize_factorial(rows)


@pytest.mark.parametrize('finish_reason', ['controller_stop', 'actor_stop', 'budget_exhausted'])
def test_verified_controller_stop_counts_as_native_failure(finish_reason):
    rows = outcomes('task', 'layout', 'actor', 'b' * 64, 17, {'00': 0, '10': 0, '01': 0, '11': 1})
    rows[0] = replace(rows[0], done=False, won=False, outcome_verified=True, finish_reason=finish_reason)
    result = summarize_factorial(rows)
    assert result['tasks'][0]['rates']['00'] == 0.0
    assert result['tasks'][0]['interaction'] == 1.0


def test_seeds_are_paired_within_task_and_costs_remain_separate():
    synergy = {'00': 0, '10': 0, '01': 0, '11': 1}
    additive = {'00': 0, '10': 1, '01': 0, '11': 1}
    rows = (outcomes('a', 'layout', 'actor', 'a' * 64, 17, synergy) +
            outcomes('a', 'layout', 'actor', 'a' * 64, 29, synergy) +
            outcomes('b', 'layout', 'actor', 'b' * 64, 17, additive))
    rows[0] = replace(rows[0], usage=Usage(input_tokens=None, cached_input_tokens=None))
    result = summarize_factorial(rows)
    group = result['layout_groups'][0]
    assert result['sampling_unit'] == 'task_with_paired_seeds'
    assert group['task_count'] == 2 and group['interaction_mean'] == 0.5
    assert group['costs_by_mask']['00']['input_tokens'] == {'known_sum': 20, 'unknown_count': 1, 'total': None}
    assert group['costs_by_mask']['00']['cached_input_tokens'] == {'known_sum': 8, 'unknown_count': 1, 'total': None}
    assert group['costs_by_mask']['00']['posts'] == {'known_sum': 2, 'unknown_count': 1, 'total': None}


def test_unknown_cost_is_not_a_zero_total():
    rows = outcomes('task', 'layout', 'actor', 'b' * 64, 17,
                    {'00': 0, '10': 0, '01': 0, '11': 1}, usage=Usage())
    costs = summarize_factorial(rows)['tasks'][0]['costs_by_mask']
    assert costs['00']['input_tokens'] == {'known_sum': None, 'unknown_count': 1, 'total': None}


def test_duplicate_physical_or_mask_cell_is_rejected():
    rows = outcomes('task', 'layout', 'actor', 'c' * 64, 17, {'00': 0, '10': 0, '01': 0, '11': 1})
    with pytest.raises(ValueError, match='duplicate physical'):
        summarize_factorial(rows + [rows[0]])
    with pytest.raises(ValueError, match='duplicate physical receipt'):
        summarize_factorial(rows + [replace(rows[0], physical_run_id='another-run')])
    with pytest.raises(ValueError, match='duplicate task'):
        summarize_factorial(rows + [replace(rows[0], physical_run_id='third-run', receipt_sha256='f' * 64)])
    with pytest.raises(ValueError, match='four masks'):
        summarize_factorial(rows[:-1])


def test_layout_and_prefix_cannot_mix_and_actors_are_separate():
    wins = {'00': 0, '10': 0, '01': 0, '11': 1}
    first = outcomes('task', 'layout', 'actor-a', 'a' * 64, 17, wins)
    other = outcomes('task', 'layout', 'actor-b', 'b' * 64, 17, wins)
    result = summarize_factorial(first + other)
    assert {row['actor_id'] for row in result['layout_groups']} == {'actor-a', 'actor-b'}
    bad_layout = first.copy(); bad_layout[1] = replace(bad_layout[1], layout_group='other')
    with pytest.raises(ValueError, match='layout groups'):
        summarize_factorial(bad_layout)
    bad_prefix = first.copy(); bad_prefix[1] = replace(bad_prefix[1], prefix_sha256='d' * 64)
    with pytest.raises(ValueError, match='prefixes'):
        summarize_factorial(bad_prefix)
