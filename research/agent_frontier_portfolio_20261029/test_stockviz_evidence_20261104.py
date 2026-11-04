import hashlib
import json

import pytest

from build_stockviz_experience_20261104 import make_readable_controls
from summarize_stockviz_20261104 import episode


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def test_readable_controls_preserve_history_and_add_only_real_source_feedback(tmp_path):
    source, original, out = (tmp_path / name for name in ('source', 'original', 'out'))
    source.mkdir()
    original.mkdir()
    (source / 'raw.jsonl').write_text('{}\n', encoding='utf-8')
    (source / 'receipt.json').write_text(json.dumps({'task': 'stock-data-visualization-1',
                                                      'raw_sha256': digest(source / 'raw.jsonl')}))
    (source / 'verifier.txt').write_text('E AssertionError: indiv-stock/ directory must exist\n'
                                         'GETTER "GET /output/data/stock-descriptions.csv HTTP/1.1" 404 -\n')
    history = {'source_instruction': 'a' * 3000, 'source_feedback': {'verifier_output_tail': 'old tail'}}
    history_path = original / 'source_history.json'
    history_path.write_text(json.dumps(history), encoding='utf-8')
    (original / 'config.json').write_text(json.dumps({'source_history_sha256': digest(history_path),
                                                      'source_trace_sha256': digest(source / 'raw.jsonl')}))
    make_readable_controls(source, original, out)
    decoded = []
    for arm in ('readable_tail', 'readable_diagnostic'):
        lines = (out / arm / 'source_history_readable.txt').read_text(encoding='utf-8').splitlines()
        assert max(map(len, lines)) <= 1000
        decoded.append(json.loads(''.join(line.split('|', 1)[1] for line in lines[1:])))
    assert decoded[0] == history
    assert len(decoded[1]['source_feedback'].pop('post_hoc_source_log_excerpts')) == 2
    assert decoded[1] == history
    assert (out / 'readable_tail/source_history.json').read_bytes() == history_path.read_bytes()


def test_history_read_does_not_confuse_old_nested_marker_with_new_truncation(tmp_path):
    experience = tmp_path / 'source_experience'
    experience.mkdir()
    mounted = experience / 'source_history.json'
    content = ['{', 'old: line truncated to 2000 chars is recorded', 'payload: ' + 'x' * 2100, '}']
    mounted.write_text('\n'.join(content) + '\n', encoding='utf-8')
    case = tmp_path / 'stock-data-visualization-2__raw_history__1'
    case.mkdir()
    shown = content[:2] + [content[2][:100] + '... (line truncated to 2000 chars)'] + content[3:]
    output = '<content>\n' + ''.join(f'{i}: {line}\n' for i, line in enumerate(shown, 1)) + '(End of file - total 4 lines)\n</content>'
    event = {'type': 'tool_use', 'part': {'tool': 'read', 'state': {'status': 'completed',
             'input': {'filePath': '/root/source_history.json'}, 'output': output}}}
    raw = case / 'raw.jsonl'
    raw.write_text(json.dumps(event) + '\n', encoding='utf-8')
    (case / 'receipt.json').write_text(json.dumps({'task': 'stock-data-visualization-2', 'arm': 'raw_history',
        'raw_sha256': digest(raw), 'agent_exit': 0, 'verifier_exit': 1, 'model_http_requests': ['POST /v1/chat/completions'],
        'step_finish_tokens': [{'total': 10, 'cache': {'read': 3}}], 'elapsed_seconds': 1.0}))
    (case / 'intervention.json').write_text(json.dumps({'source_experience_sha256': {'/root/source_history.json': digest(mounted)}}))
    (case / 'verifier.txt').write_text('1 failed, 2 passed in 1s\n')
    result = episode(tmp_path, 2, 'raw_history')
    assert result['tests']['passed'] == 2 and result['tests']['failed'] == 1
    assert result['history_reads'][0]['truncated_lines'] == 1
    assert not result['history_reads'][0]['visible_lines_exactly_match_mounted_file']
    mounted.write_text('tampered', encoding='utf-8')
    with pytest.raises(ValueError, match='mounted source history changed'):
        episode(tmp_path, 2, 'raw_history')
