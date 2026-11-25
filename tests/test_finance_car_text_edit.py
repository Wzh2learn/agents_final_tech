import json
from pathlib import Path

import pytest


@pytest.fixture
def edit(monkeypatch):
    monkeypatch.syspath_prepend(str(Path(__file__).resolve().parents[1] / 'research' / 'finance_frontier_pilot'))
    from car_text_edit import apply_text_edits
    return apply_text_edits


def tokens(value):
    return len(value.split())


def payload(*edits):
    return json.dumps({'edits': list(edits)})


def replacement(target, new, passage='p1'):
    return {'type': 'replace', 'target_span': target, 'new_text': new, 'passage_id': passage}


def addition(text, passage='p1'):
    return {'type': 'append', 'target_span': '', 'new_text': text, 'passage_id': passage}


def test_exact_and_canonical_replacement_preserves_surroundings(edit):
    draft = 'one two three four five six seven eight nine “old” eleven twelve thirteen fourteen fifteen'
    merged, count = edit(draft, payload(replacement('"old"', 'new')), {'p1'}, 'replace', tokens)
    assert count == 1 and merged == draft.replace('“old”', 'new')
    draft = 'one two three four five six seven eight nine **old** eleven twelve thirteen fourteen fifteen'
    merged, count = edit(draft, payload(replacement('old', 'new')), {'p1'}, 'replace', tokens)
    assert count == 1 and merged == draft.replace('old', 'new')


def test_ambiguous_overlapping_and_token_budget(edit):
    draft = 'one two three four five six seven eight nine ten repeated repeated end'
    assert edit(draft, payload(replacement('repeated', 'x')), {'p1'}, 'replace', tokens) == (draft, 0)
    result, count = edit(draft, payload(replacement('one two', 'x'), replacement('two three', 'y'),
                                        replacement('four', 'z')), {'p1'}, 'replace', tokens)
    assert (result, count) == (draft.replace('one two', 'x'), 1)  # 3 tokens exceeds the 20% budget.
    result, count = edit(draft, payload(replacement('one', 'x'), replacement('four', 'z'),
                                        replacement('five', 'q')), {'p1'}, 'replace', tokens)
    assert (result, count) == (draft.replace('one', 'x').replace('four', 'z'), 2)


def test_unknown_evidence_or_malformed_json_rejects_whole_response(edit):
    draft = 'one two three four five six seven eight nine ten'
    outputs = [payload(replacement('one', 'x'), replacement('two', 'y', 'unknown')),
               '{"edits":[],"edits":[]}', '{"edits":[}',
               payload({'type': 'replace', 'target_span': 'one', 'new_text': 'x'}),
               payload(addition('text'))]
    assert all(edit(draft, output, {'p1'}, 'replace', tokens) == (draft, 0) for output in outputs)


def test_append_cap_and_invalid_tokenizer(edit):
    text80 = ' '.join(['word'] * 80)
    result, count = edit('draft', payload(addition(text80), addition('extra')), {'p1'}, 'append', tokens)
    assert (result, count) == ('draft ' + text80, 1)
    assert edit('draft', payload(addition(text80 + ' extra')), {'p1'}, 'append', tokens) == ('draft', 0)
    with pytest.raises(ValueError, match='count_tokens'):
        edit('draft', payload(addition('x')), {'p1'}, 'append', lambda _: True)


def test_canonical_whitespace_and_overlap_resolve_original_offsets(edit):
    draft = 'one two three four five six seven eight nine final\n  value eleven twelve thirteen fourteen fifteen'
    result, count = edit(draft, payload(replacement('final value', 'revised'),
                                        replacement('value eleven', 'bad')), {'p1'}, 'replace', tokens)
    assert (result, count) == (draft.replace('final\n  value', 'revised'), 1)


def test_arithmetic_operators_remain_literal_during_fallback(edit):
    draft = 'one two three four five six seven eight nine 4 * 5 and foo_bar thirteen fourteen fifteen'
    assert edit(draft, payload(replacement('4 5', 'wrong')), {'p1'}, 'replace', tokens) == (draft, 0)
    assert edit(draft, payload(replacement('foo bar', 'wrong')), {'p1'}, 'replace', tokens) == (draft, 0)
    draft = 'one two three four five six seven eight nine **gross income** twelve thirteen fourteen fifteen'
    result, count = edit(draft, payload(replacement('gross   income', 'net income')), {'p1'}, 'replace', tokens)
    assert (result, count) == (draft.replace('gross income', 'net income'), 1)
