"""Synthetic CPU engineering controls; fake models/scorers are not research evidence."""
import copy
import importlib.util
import json
from pathlib import Path
from types import SimpleNamespace
from contextlib import contextmanager
from unittest import mock
import pytest
from test_alfworld_native_actor import a as native, core, FakeSocket

HERE = Path(__file__).resolve().parents[1] / 'research/agent_frontier_portfolio_20261029'
spec = importlib.util.spec_from_file_location('cpu_teacher_patch', HERE / 'contextbench_teacher_patch.py')
t = importlib.util.module_from_spec(spec); spec.loader.exec_module(t)
REAL_TOKEN_COUNTER = t.token_counter
spec = importlib.util.spec_from_file_location('cpu_source_patch_helper', HERE / 'run_contextbench_source.py')
source = importlib.util.module_from_spec(spec); spec.loader.exec_module(source)
spec = importlib.util.spec_from_file_location('cpu_git_apply_helper', HERE / 'qualify_swe_contextbench_sympy_20261104.py')
patch_helper = importlib.util.module_from_spec(spec); spec.loader.exec_module(patch_helper)
DIFF = ('diff --git a/' + t.CODE + ' b/' + t.CODE + '\n--- a/' + t.CODE + '\n+++ b/' + t.CODE +
        '\n@@ -1,2 +1,2 @@\n def f():\n-    return 1\n+    return 2\n')


def ref(path, value=None, binary=None):
    path.parent.mkdir(parents=True, exist_ok=True)
    if value is not None: path.write_bytes(t.encoded(value))
    if binary is not None: path.write_bytes(binary)
    return dict(path=str(path), sha256=t.sha(path.read_bytes()))


def sse(content=DIFF, finish='stop', usage=True, reasoning='CPU reasoning', reasoning_key='reasoning_content'):
    rows = [dict(choices=[dict(index=0, delta={reasoning_key: reasoning}, finish_reason=None)]),
            dict(choices=[dict(index=0, delta=dict(content=content), finish_reason=None)]),
            dict(choices=[dict(index=0, delta={}, finish_reason=finish)])]
    if usage: rows.append(dict(choices=[], usage=dict(prompt_tokens=11, completion_tokens=7, total_tokens=18)))
    return b''.join(b'data: ' + t.encoded(row) + b'\n\n' for row in rows) + b'data: [DONE]\n\n'


def scoring(labels, state='passed'):
    return dict(status='EVALUATED', passed=state == 'passed', suites={suite: dict(exit=0,
        coverage=dict(complete=True, labels=dict.fromkeys(nodes, state), reported_tests=len(nodes), extra_ids=[])) for suite, nodes in labels.items()})


@pytest.fixture
def synthetic(tmp_path, monkeypatch):
    old = tmp_path / 'old_closed_source'; old.mkdir()
    for name in ('baseline', 'work'):
        path = old / name / t.CODE; path.parent.mkdir(parents=True); path.write_bytes(b'def f():\n    return 1\n')
    public = ref(old / 'inputs/source_task.txt', binary='CPU_PUBLIC_PROBLEM_VERBATIM\n\u03bc\n'.encode())
    ref(old / 'scoring/test.patch', binary=b'CPU_PRIVATE_TEST_PATCH_NEVER_IN_MESSAGES')
    profile_ref = dict(path=str(tmp_path / 'outside_ST/profile.json'), sha256=t.PROFILE_SHA)
    profile = dict(model_id='CPU_TEACHER', host='CPU_NO_ENDPOINT', port=1, model_root='CPU_NO_WEIGHTS')
    labels = dict(f2p=['public_node'], ptp=['public_ptp_' + str(i) for i in range(13)])
    m = dict(source=t.SOURCE, repo='sympy/sympy', profile=profile_ref, baseline=source.tree(old / 'baseline'),
             public_task_sha256=public['sha256'], labels=labels)
    manifest_ref = ref(old / 'manifest.json', m)
    raw = t.encoded(dict(type='tool_use', part=dict(tool='bash', callID='cpu_last_call', state=dict(status='completed',
        input=dict(command='python -c "public_reproduction()"'), output='CPU_ACTUAL_UNSIMPLIFIED_OUTPUT\n',
        metadata=dict(output='CPU_ACTUAL_UNSIMPLIFIED_OUTPUT\n', exit=0, truncated=False))))) + b'\n'
    raw_ref = ref(old / 'raw.jsonl', binary=raw)
    receipt = dict(source=t.SOURCE, manifest_sha256=manifest_ref['sha256'], raw_sha256=raw_ref['sha256'],
        source_success=False, changed_artifacts=[], status='GENERATION_FAULT',
        accounting=dict(actual_forwarded_posts=48, integrity_passed=True, provider_total_tokens_known=120,
                        unknown_usage_requests=[], uncertain_partial_sends=0))
    receipt_ref = ref(old / 'receipt.json', receipt)
    closure = dict(source_id=t.SOURCE, status='EXPLAINED_BUDGET_CLOSED_UNREPAIRED',
        manifest_sha256=manifest_ref['sha256'], receipt_sha256=receipt_ref['sha256'], actual_forwarded_POST=48,
        unknown_usage_requests=0, source_success=False, changed_artifacts=[],
        provider_usage=dict(prompt_tokens=100, completion_tokens=20, total_tokens=120))
    closure_ref = ref(tmp_path / 'D_CLOSURE.json', closure)
    p = dict(schema='CONTEXTBENCH_TEACHER_PATCH_V1', source_manifest=manifest_ref, source_receipt=receipt_ref,
        source_raw=raw_ref, source_closure=closure_ref, profile=profile_ref,
        source_runner=ref(HERE / 'run_contextbench_source.py'), transport=ref(HERE / 'alfworld_native_actor.py'),
        reproduction_call_id='cpu_last_call', code_paths=[t.CODE], output_root=str(tmp_path / 'fresh_patch'),
        caps=dict(posts=1, seconds=600, combined_wire_bytes=8 * 1024**2))
    protocol_path = tmp_path / 'protocol.json'; protocol_ref = ref(protocol_path, p)
    events = []; checked = []
    @contextmanager
    def lock():
        events.append('lock_acquired')
        try: yield
        finally: events.append('lock_released')
    h = SimpleNamespace(actor=core, pool=SimpleNamespace(helpers=lambda: (patch_helper, None)),
        teacher=SimpleNamespace(validate_vllm_model_profile=lambda *a, **k: events.append(('metadata', k)),
                                verify_vllm_backend=lambda p: events.append('FAKE_BACKEND') or {}))
    def verify(root, digest, *, initial):
        assert initial is False  # The failed source is already executed; never label it an unrun root.
        assert t.read_ref(dict(path=str(root / 'manifest.json'), sha256=digest)) == m
        return m, h, None, profile
    fake_source = SimpleNamespace(verify=verify, tree=source.tree, resource_lock=lock,
        candidate_diff=source.candidate_diff, score=lambda *a: events.append('FAKE_SCORE_CONTAINER') or scoring(labels))
    monkeypatch.setattr(t, 'PRIVATE', tmp_path)
    monkeypatch.setattr(t, 'module', lambda ref, name: fake_source if name == 'run_contextbench_source.py' else native)
    def counter(profile):
        def count(payload):
            checked.append(copy.deepcopy(payload)); mode = payload['chat_template_kwargs']['enable_thinking']
            return dict(template_input_tokens=10 + int(mode), reserved_output_tokens=8192, context=32768,
                fits_with_margin=True, safety_margin_tokens=512, enable_thinking=mode, payload_sha256=t.sha(t.wire_body(payload)))
        return count, dict(CPU_SYNTHETIC_TOKENIZER=True)
    monkeypatch.setattr(t, 'token_counter', counter)
    return SimpleNamespace(p=p, path=protocol_path, digest=protocol_ref['sha256'], old=old, labels=labels, m=m,
        root=tmp_path / 'fresh_patch', events=events, checked=checked, source=fake_source, h=h, raw=raw)


def test_prepare_is_cpu_only_identical_messages_post_execution_source_and_no_private_input(synthetic):
    f = synthetic; before = source.tree(f.old)
    prepared = t.prepare(f.path, f.digest)
    assert prepared['models_called'] == 0 and prepared['status'] == 'CPU_PREPARED'
    assert source.tree(f.old) == before and not (f.root / 'false').exists()
    assert f.events == [('metadata', dict(full=False))]
    false = t.decode((f.root / 'payload_false.json').read_bytes()); true = t.decode((f.root / 'payload_true.json').read_bytes())
    assert t.encoded(false['messages']) == t.encoded(true['messages'])
    true['chat_template_kwargs']['enable_thinking'] = False; assert true == false
    text = str(false['messages'])
    assert 'CPU_PUBLIC_PROBLEM_VERBATIM\n' in false['messages'][1]['content']
    assert 'CPU_ACTUAL_UNSIMPLIFIED_OUTPUT' in text and 'CPU_PRIVATE_TEST_PATCH' not in text
    assert str(f.old) not in text and 'public_ptp_' not in text and '9384' not in text
    assert [x['chat_template_kwargs']['enable_thinking'] for x in f.checked] == [False, True]
    with pytest.raises(FileExistsError): t.prepare(f.path, f.digest)


def test_default_cli_is_cpu_check_only_and_creates_no_output(synthetic, monkeypatch, capsys):
    f = synthetic
    monkeypatch.setattr(t.sys, 'argv', ['teacher_patch', '--protocol', str(f.path), '--protocol-sha', f.digest])
    assert t.main() == 0
    assert json.loads(capsys.readouterr().out)['models_called'] == 0
    assert not f.root.exists() and f.events == [('metadata', dict(full=False))]


@pytest.mark.parametrize('change', ['target', 'code_path', 'posts', 'seconds', 'raw_hash', 'closure_hash', 'call', 'work'])
def test_source_hash_path_caps_and_feedback_injection_rejected(synthetic, change):
    f = synthetic
    if change == 'target':
        f.m['source'] = 'sympy__sympy-9384'; f.p['source_manifest'] = ref(f.old / 'manifest.json', f.m)
    elif change == 'code_path': f.p['code_paths'] = ['sympy/assumptions/tests/test_refine.py']
    elif change == 'posts': f.p['caps']['posts'] = 2
    elif change == 'seconds': f.p['caps']['seconds'] = 1201
    elif change == 'raw_hash': f.p['source_raw']['sha256'] = '0' * 64
    elif change == 'closure_hash': f.p['source_closure']['sha256'] = '0' * 64
    elif change == 'call': f.p['reproduction_call_id'] = 'not_the_completed_call'
    elif change == 'work': (f.old / 'work' / t.CODE).write_text('CPU_CANDIDATE_FROM_OTHER_ARM')
    digest = ref(f.path, f.p)['sha256']
    with pytest.raises(ValueError): t.load_inputs(f.path, digest)
    assert not f.root.exists() and 'FAKE_BACKEND' not in f.events


def test_tokenizer_receives_actual_kwargs_and_true_has_its_own_count(tmp_path):
    template = tmp_path / 'template.jinja'; template.write_text('CPU_TEMPLATE')
    for name in ('tokenizer.json', 'tokenizer_config.json'): (tmp_path / name).write_text('{}')
    calls = []
    class Tokenizer:
        def apply_chat_template(self, messages, **kwargs):
            calls.append(kwargs); return [1] * (4 if kwargs['enable_thinking'] else 2)
    import transformers
    with mock.patch.object(transformers.AutoTokenizer, 'from_pretrained', return_value=Tokenizer()) as load:
        count, binding = t.token_counter(dict(model_root=str(tmp_path), template_path=str(template), template_sha256=t.sha(template.read_bytes())))
        proofs = [count(t.payload_for([dict(role='user', content='CPU')], dict(model_id='CPU'), mode)) for mode in (False, True)]
    assert [p['template_input_tokens'] for p in proofs] == [2, 4]
    assert [c['enable_thinking'] for c in calls] == [False, True]
    assert all(c['return_dict'] is False for c in calls)
    assert all(p['token_return_type'] == 'builtins.list' for p in proofs)
    assert load.call_args.kwargs == dict(local_files_only=True, trust_remote_code=False, use_fast=True)
    assert binding['template_sha256'] == t.sha(template.read_bytes())


@pytest.mark.parametrize('shape', ['mapping', 'BatchEncoding', 'nested', 'bool', 'string', 'tuple', 'empty', 'negative'])
def test_tokenizer_never_treats_mapping_fields_or_nonflat_ids_as_tokens(tmp_path, shape):
    from transformers import AutoTokenizer, BatchEncoding
    template = tmp_path / 'template.jinja'; template.write_text('CPU_TEMPLATE')
    for name in ('tokenizer.json', 'tokenizer_config.json'): (tmp_path / name).write_text('{}')
    values = dict(mapping={'input_ids': [1, 2, 3], 'attention_mask': [1, 1, 1]},
        BatchEncoding=BatchEncoding({'input_ids': [1, 2, 3], 'attention_mask': [1, 1, 1]}),
        nested=[[1, 2, 3]], bool=[True], string=['1'], tuple=(1, 2), empty=[], negative=[-1])
    tokenizer = SimpleNamespace(apply_chat_template=mock.Mock(return_value=values[shape]))
    with mock.patch.object(AutoTokenizer, 'from_pretrained', return_value=tokenizer):
        count, _ = t.token_counter(dict(model_root=str(tmp_path), template_path=str(template), template_sha256=t.sha(template.read_bytes())))
        with pytest.raises(ValueError, match='list of integer token IDs'):
            count(t.payload_for([dict(role='user', content='CPU')], dict(model_id='CPU'), False))
    assert tokenizer.apply_chat_template.call_args.kwargs['return_dict'] is False


def test_actual_token_counter_marks_overlong_sequence_and_load_rejects(synthetic, monkeypatch, tmp_path):
    # Exercise the real counter against a fake tokenizer, not a mocked token-count proof.
    from transformers import AutoTokenizer
    template = tmp_path / 'template.jinja'; template.write_text('CPU_TEMPLATE')
    for name in ('tokenizer.json', 'tokenizer_config.json'): (tmp_path / name).write_text('{}')
    profile = dict(model_id='CPU', model_root=str(tmp_path), template_path=str(template), template_sha256=t.sha(template.read_bytes()))
    tokenizer = SimpleNamespace(apply_chat_template=mock.Mock(return_value=[1] * (32768 - 8192 - 512 + 1)))
    with mock.patch.object(AutoTokenizer, 'from_pretrained', return_value=tokenizer):
        count, binding = REAL_TOKEN_COUNTER(profile)
        proof = count(t.payload_for([dict(role='user', content='CPU')], profile, False))
    assert proof['template_input_tokens'] == 24065 and proof['fits_with_margin'] is False
    monkeypatch.setattr(t, 'token_counter', lambda profile: (count, binding))
    with pytest.raises(ValueError, match='exceeds context reserve'): t.load_inputs(synthetic.path, synthetic.digest)
    assert not synthetic.root.exists()


@pytest.mark.parametrize('change', ['prose', 'two_fences', 'test', 'traversal', 'delete', 'rename', 'binary', 'mode', 'no_final_lf'])
def test_diff_is_single_allowed_existing_source_without_automatic_repair(change):
    value = DIFF
    if change == 'prose': value = 'Here is the fix\n' + value
    elif change == 'two_fences': value = '```diff\n' + value + '```\n```diff\n' + value + '```'
    elif change == 'test': value = value.replace(t.CODE, 'sympy/assumptions/tests/test_refine.py')
    elif change == 'traversal': value = value.replace(t.CODE, '../refine.py')
    elif change == 'delete': value = value.replace('+++ b/' + t.CODE, '+++ /dev/null')
    elif change == 'rename': value = value.replace('--- a/', 'rename from another.py\n--- a/')
    elif change == 'binary': value += 'GIT binary patch\n'
    elif change == 'mode': value = value.replace('--- a/', 'new file mode 120000\n--- a/')
    elif change == 'no_final_lf': value = value[:-1]
    with pytest.raises(ValueError): t.strict_diff(value)


def test_only_complete_outer_fence_is_adapted_and_git_apply_really_checks(tmp_path):
    diff, adaptation = t.strict_diff('```diff\n' + DIFF + '```\n')
    assert diff == DIFF and adaptation == 'one complete outer diff fence removed'
    path = tmp_path / t.CODE; path.parent.mkdir(parents=True); path.write_text('def f():\n    return 1\n')
    assert patch_helper.apply_patch(tmp_path, diff) == dict(check_exit=0, apply_exit=0, diagnostic='')
    assert path.read_text() == 'def f():\n    return 2\n'
    bad = patch_helper.apply_patch(tmp_path, diff)
    assert bad['check_exit'] != 0 and bad['apply_exit'] is None


@pytest.mark.parametrize('key', ['reasoning', 'reasoning_content'])
def test_response_preserves_reasoning_content_and_length_without_stripping(key):
    reply = t.response_channels(sse(content='<think>literal model text</think>\n' + DIFF, finish='length', reasoning_key=key))
    assert reply[key] == 'CPU reasoning' and reply['finish_reason'] == 'length'
    assert reply['content'].startswith('<think>literal')
    with pytest.raises(ValueError): t.strict_diff(reply['content'])


def test_malformed_or_tool_response_not_turned_into_a_patch():
    with pytest.raises(ValueError): t.response_channels(sse().replace(b'data: [DONE]\n\n', b''))
    bad = b'data: {"choices":[{"index":0,"delta":{"tool_calls":[]},"finish_reason":"stop"}]}\n\ndata: [DONE]\n\n'
    with pytest.raises(ValueError): t.response_channels(bad)


def prepared_release(f, arm):
    prepared = t.prepare(f.path, f.digest); b = t.load_inputs(f.path, f.digest)
    release = dict(schema='CONTEXTBENCH_TEACHER_PATCH_RELEASE_V1', protocol=b['manifest']['protocol'],
        prepared_manifest_sha256=prepared['manifest_sha256'], module_sha256=b['manifest']['module_sha256'], arm=arm,
        output_root=str(f.root / arm), caps=f.p['caps'], authorization='ONE_REAL_MODEL_POST')
    return prepared['manifest_sha256'], ref(f.root.parent / ('release_' + arm + '.json'), release)


@pytest.mark.parametrize('kind', ['good', 'length', 'unknown_usage', 'http400', 'partial_send'])
def test_one_actual_fake_wire_post_accounting_patch_and_cleanup(synthetic, kind):
    f = synthetic; prepared_sha, release = prepared_release(f, 'false'); before = source.tree(f.old)
    upstream = FakeSocket(body=sse(finish='length' if kind == 'length' else 'stop', usage=kind != 'unknown_usage'),
                          status=400 if kind == 'http400' else 200, partial_send=kind == 'partial_send')
    with mock.patch.object(native.socket, 'create_connection', return_value=upstream) as connect:
        outcome = t.execute(f.path, f.digest, prepared_sha, 'false', release)
    assert connect.call_count == 1 and len(upstream.sent) == 1 and upstream.closed
    assert source.tree(f.old) == before and f.events[-1] == 'lock_released'
    root = f.root / 'false'; bill = t.decode((root / 'receipt.json').read_bytes())['accounting']
    actual = upstream.sent[0].split(b'\r\n\r\n', 1)[1]
    assert actual == (root / 'requests/00001.body').read_bytes()
    assert t.sha(actual) == t.decode((root / 'ledger/00001.json').read_bytes())['request_body_sha256']
    prepared_manifest = t.decode((f.root / 'manifest.json').read_bytes())
    assert t.sha(actual) == prepared_manifest['payload_sha256']['false']
    assert b'\\u03bc' in actual  # Same Unicode escaping as the reused transport, not dict-only proof.
    assert bill['reserved_posts'] == 1 and bill['request_body_bytes_reserved'] == len(actual)
    if kind == 'good':
        assert outcome['source_success'] and (root / 'work' / t.CODE).read_text().endswith('return 2\n')
        assert bill['provider_usage']['total_tokens'] == 18 and bill['cached_input_tokens'] is None
    else:
        assert outcome['status'] == 'GENERATION_FAULT' and 'FAKE_SCORE_CONTAINER' not in f.events
        assert not (root / 'adapted.diff').exists()
    if kind in ('unknown_usage', 'partial_send'):
        assert bill['provider_usage']['total_tokens'] is None and bill['unknown_usage_attempts'] == 1
    if kind == 'partial_send': assert bill['actual_forwarded_posts'] is None
    with pytest.raises(FileExistsError): t.execute(f.path, f.digest, prepared_sha, 'false', release)
    assert connect.call_count == 1


def test_false_candidate_never_enters_true_and_both_use_same_messages(synthetic):
    f = synthetic; prepared_sha, false_release = prepared_release(f, 'false')
    b = t.load_inputs(f.path, f.digest)
    true_release = t.read_ref(false_release); true_release.update(arm='true', output_root=str(f.root / 'true'))
    true_release = ref(f.root.parent / 'release_true.json', true_release)
    sockets = [FakeSocket(body=sse()), FakeSocket(body=sse())]
    with mock.patch.object(native.socket, 'create_connection', side_effect=sockets):
        assert t.execute(f.path, f.digest, prepared_sha, 'false', false_release)['source_success']
        assert t.execute(f.path, f.digest, prepared_sha, 'true', true_release)['source_success']
    requests = [t.decode(sock.sent[0].split(b'\r\n\r\n', 1)[1]) for sock in sockets]
    requests[1]['chat_template_kwargs']['enable_thinking'] = False
    assert requests[0] == requests[1]
    assert (f.root / 'true/baseline' / t.CODE).read_text().endswith('return 1\n')


def test_tampered_prepared_and_wrong_release_refused_before_lock_or_request(synthetic):
    f = synthetic; prepared_sha, release = prepared_release(f, 'true')
    payload = t.decode((f.root / 'payload_true.json').read_bytes()); payload['messages'][1]['content'] += 'CPU_INJECTION'
    (f.root / 'payload_true.json').write_bytes(t.encoded(payload))
    with pytest.raises(ValueError): t.execute(f.path, f.digest, prepared_sha, 'true', release)
    assert 'lock_acquired' not in f.events
    value = t.read_ref(release); value['arm'] = 'false'; bad = ref(f.root.parent / 'bad_release.json', value)
    with pytest.raises(ValueError): t.check_release(bad, t.load_inputs(f.path, f.digest), 'true', prepared_sha)


@pytest.mark.parametrize('mutation', ['skip', 'missing', 'extra', 'cleanup', 'incomplete', 'extra_count'])
def test_score_requires_all_exact_one_f2p_thirteen_ptp_not_merely_pass_flag(synthetic, mutation):
    labels = synthetic.labels; result = scoring(labels)
    if mutation == 'skip': result['suites']['ptp']['coverage']['labels'][labels['ptp'][0]] = 'skipped'
    elif mutation == 'missing': del result['suites']['ptp']['coverage']['labels'][labels['ptp'][0]]
    elif mutation == 'extra': result['suites']['ptp']['coverage']['labels']['EXTRA'] = 'passed'
    elif mutation == 'cleanup': result['suites']['ptp']['cleanup_error'] = 'CPU cleanup failure'
    elif mutation == 'incomplete': result['suites']['ptp']['coverage']['complete'] = False
    elif mutation == 'extra_count': result['suites']['ptp']['coverage']['reported_tests'] = 14
    assert not t.complete_score(result, labels)


def test_one_post_budget_is_real_and_context_or_byte_cap_is_not_a_free_retry(tmp_path):
    budget = core.Budget(max_posts=1, max_bytes=1000000, seconds=30); attempts = []
    payload = t.payload_for([dict(role='user', content='CPU')], dict(model_id='CPU'), False)
    qualify = lambda p: dict(template_input_tokens=10, reserved_output_tokens=8192, context=32768)
    with mock.patch.object(native.socket, 'create_connection', return_value=FakeSocket(body=sse())) as connect:
        native.exchange(core, tmp_path, payload, budget, qualify, ('CPU_FAKE', 1), attempts)
        with pytest.raises(native.CapClosed): native.exchange(core, tmp_path, payload, budget, qualify, ('CPU_FAKE', 1), attempts)
    assert connect.call_count == 1 and native.accounting(attempts, budget)['reserved_posts'] == 1


@pytest.mark.parametrize('cap', ['context', 'bytes'])
def test_context_and_byte_rejection_happen_before_send_and_budget_reserve(tmp_path, cap):
    budget = core.Budget(max_posts=1, max_bytes=1 if cap == 'bytes' else 1000000, seconds=30); attempts = []
    payload = t.payload_for([dict(role='user', content='CPU')], dict(model_id='CPU'), False)
    qualify = lambda p: dict(template_input_tokens=32768 if cap == 'context' else 10, reserved_output_tokens=8192, context=32768)
    with mock.patch.object(native.socket, 'create_connection') as connect:
        with pytest.raises(native.CapClosed): native.exchange(core, tmp_path, payload, budget, qualify, ('CPU_FAKE', 1), attempts)
    assert not connect.called and budget.posts == 0 and len(attempts) == 1 and attempts[0]['reserved'] is False
