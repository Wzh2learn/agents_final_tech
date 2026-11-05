"""Evidence controls must retain source semantics and reject altered provenance."""
from __future__ import annotations
import hashlib
import importlib.util
import json
from pathlib import Path
import pytest

FILE = Path(__file__).resolve().parents[1] / 'research/agent_frontier_portfolio_20261029/prepare_astropy_evidence_profiles_20261106.py'
spec = importlib.util.spec_from_file_location('evidence_profiles', FILE)
profiles = importlib.util.module_from_spec(spec)
spec.loader.exec_module(profiles)


def save(path, value):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value), encoding='utf8')


def source_fixture(root):
    source = root / 'source'
    directory = source / 'source_experience'
    directory.mkdir(parents=True)
    raw = source / 'source__none__seed7201/raw.jsonl'
    raw.parent.mkdir()
    raw.write_text('{"type":"step_finish"}\n', encoding='utf8')
    result = {'status':'EVALUATED'}
    for metric, count in [('focus', 1), ('regression', 3)]:
        log = raw.parent / 'post_run_evaluation_restored_tests' / (metric + '.log')
        log.parent.mkdir(exist_ok=True)
        log.write_text('passed\n', encoding='utf8')
        result[metric] = {'exit':0, 'nodes_requested':count, 'log_sha256':profiles.sha(log)}
    complete = source / 'source__none__seed7201.completed.json'
    save(complete, {'status':'COMPLETED', 'agent_exit':0, 'raw_sha256':profiles.sha(raw),
                    'post_run_evaluation':result})
    diff = '--- base\n+++ candidate\n@@ -1 +1 @@\n-unsafe()\n+safe()\n'
    history = {'source_task':'A source-only issue\n```python\nf(\"姹夊瓧\")\n```\n',
               'source_result':{'focus_exit':0, 'focus_count':1, 'regression_exit':0, 'regression_count':3},
               'changed_paths':['code.py'], 'source_artifact_diff_prefix':diff,
               'source_artifact_diff_chars':len(diff),
               'source_artifact_diff_sha256':hashlib.sha256(diff.encode()).hexdigest(),
               'source_artifact_diff_omitted_paths':[],
               'source_actions':[{'input_prefix':'read("code.py")', 'output_tail':'old\ncode\n'}]}
    (directory/'source_history.md').write_text('Source history\n'+json.dumps(history),encoding='utf8')
    (directory/'feedback_card.md').write_text('old result card\n',encoding='utf8')
    (directory/'generated_skill.md').write_text('source-only skill\n',encoding='utf8')
    save(directory/'skill_generation_ledger.json', {'status':'RECEIVED','finish_reason':'stop'})
    save(directory/'metadata.json', {'source_completion_sha256':profiles.sha(complete),
         'source_raw_sha256':profiles.sha(raw), 'artifacts':{'source_history.md':profiles.sha(directory/'source_history.md')}})
    save(directory/'target_input_freeze.json', {'source_completion_sha256':profiles.sha(complete),
         'skill_generation_ledger_sha256':profiles.sha(directory/'skill_generation_ledger.json'),
         'artifacts':{n:profiles.sha(directory/n) for n in ['source_history.md','feedback_card.md','generated_skill.md']}})
    return source, history


def test_history_roundtrip_retains_strings_and_structure():
    original = {'source_task':'Visible line\n'+('x' * 1200)+'\n灏綷n',
                'source_actions':[{'code':'a\\nb\n\t\"quoted\"'}], 'source_result':{'exit':0}}
    rendered = profiles.render_history(original)
    assert profiles.decode_history(rendered) == original
    assert profiles.canonical(profiles.decode_history(rendered)) == profiles.canonical(original)
    assert max(map(len,rendered.splitlines())) <= 1800


def test_history_never_truncates_an_oversized_remaining_field():
    with pytest.raises(ValueError, match='do not truncate'):
        profiles.render_history({'source_task':'short', 'unbounded': 'x' * 1900})


def test_prepare_preserves_skill_and_qualifies_full_diff(tmp_path):
    source, history = source_fixture(tmp_path)
    out = tmp_path/'new_profile'
    result = profiles.prepare(source, out)
    assert profiles.decode_history((out/'source_history.md').read_text(encoding='utf8')) == history
    assert (out/'generated_skill.md').read_bytes() == (source/'source_experience/generated_skill.md').read_bytes()
    assert history['source_artifact_diff_prefix'] in (out/'feedback_card.md').read_text(encoding='utf8')
    assert result['scope'].startswith('post-hoc development')
    assert result['source_object_canonical_sha256'] == result['rendered_round_trip_canonical_sha256']
    with pytest.raises(FileExistsError): profiles.prepare(source,out)


def test_modified_source_artifact_is_rejected_before_output(tmp_path):
    source, _ = source_fixture(tmp_path)
    (source/'source_experience/source_history.md').write_text('tampered\n{}', encoding='utf8')
    out = tmp_path/'new_profile'
    with pytest.raises(ValueError,match='provenance'): profiles.prepare(source,out)
    assert not out.exists()


def test_changed_feedback_log_is_rejected_before_output(tmp_path):
    source, _ = source_fixture(tmp_path)
    log=source/'source__none__seed7201/post_run_evaluation_restored_tests/focus.log'
    log.write_text('not the frozen outcome', encoding='utf8')
    out = tmp_path/'new_profile'
    with pytest.raises(ValueError,match='evaluation log'): profiles.prepare(source,out)
    assert not out.exists()

def test_profile_rejects_a_different_source_even_when_data_bytes_match(tmp_path):
    source, _ = source_fixture(tmp_path/'a')
    other, _ = source_fixture(tmp_path/'b')
    out = tmp_path/'profile'
    profiles.prepare(source,out)
    assert profiles.validate_profile(out, source) == profiles.sha(out/'input_profile_manifest.json')
    with pytest.raises(ValueError, match='declared original source'):
        profiles.validate_profile(out,other)


def test_profile_cannot_add_target_hints_by_refreshing_only_its_hash(tmp_path):
    source, _ = source_fixture(tmp_path)
    out = tmp_path/'profile'
    profiles.prepare(source,out)
    card=out/'feedback_card.md'
    card.write_text(card.read_text(encoding='utf8')+'new inferred target instruction\n',encoding='utf8')
    manifest=json.loads((out/'input_profile_manifest.json').read_text(encoding='utf8'))
    manifest['artifacts']['feedback_card.md']=profiles.sha(card)
    save(out/'input_profile_manifest.json',manifest)
    with pytest.raises(ValueError, match='declared original source'):
        profiles.validate_profile(out,source)


def test_legacy_inputs_cannot_be_relabelled_as_a_different_source(tmp_path):
    source, _ = source_fixture(tmp_path/'a')
    other, _ = source_fixture(tmp_path/'b')
    assert profiles.validate_profile(source/'source_experience', source) is None
    with pytest.raises(ValueError, match='source-bound profile'):
        profiles.validate_profile(other/'source_experience', source)
