"""Matched BF16 base/LoRA OpenCode execution from one exposed failure state.

This qualifies the serving/harness integration, not learning or heldout gains.
The program never starts or stops a model server. D owns that resource window.
"""
from __future__ import annotations
import argparse
import hashlib
import importlib.util
import json
import os
from pathlib import Path
import re
import subprocess
import time

REPO = Path(__file__).resolve().parents[2]
QUAL = Path('/home/testuser/wzh/research_evidence/agent_learning_20261030/alfworld_text_qualification_20261106')
RECOVERY_PATH = Path(__file__).with_name('run_alfworld_recovery_20261106.py')
RECOVERY_SHA = 'cad06ec2b6f9e144fea29c17061b9527d07b7df13ecbf5784fb0870d9a0ce8ca'
BASE_BINDING_SHA = 'e74513f1fe22a2cb9198714738bb86b2f78c05eb0474b25e3759394b8a709823'
TRAIN_RECEIPT_SHA = '1df59e5c5870b40105ad5ac62f01dd00530433aaa47d2081d222c2637b5f78fe'
MODEL_IDS = {'base': 'qwen3-4b-bf16', 'trained': 'alfworld4b-correction-v1', 'zero': 'alfworld4b-zero-v1'}
CLIENT_ID = 'alf4b-shared-client'
_RECOVERY = None


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def recovery():
    global _RECOVERY
    if sha(RECOVERY_PATH) != RECOVERY_SHA:
        raise ValueError('frozen recovery primitives changed')
    if _RECOVERY is None:
        spec = importlib.util.spec_from_file_location('alf_adapter_recovery', RECOVERY_PATH)
        _RECOVERY = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(_RECOVERY)
    return _RECOVERY


def components():
    return {**recovery().components(), str(Path(__file__).resolve()): sha(__file__)}


def profile(path, digest, *, verify_container=True):
    path = Path(path)
    if path.is_symlink() or sha(path) != digest:
        raise ValueError('serving profile changed')
    value = json.loads(path.read_text())
    if (value['host'], value['port'], value['context'], value['output'], value['dtype']) != (
            '127.0.0.1', 18106, 16384, 4096, 'bfloat16'):
        raise ValueError('unqualified endpoint/context/precision')
    if (value['model_ids'] != MODEL_IDS or value['base_binding_sha256'] != BASE_BINDING_SHA or
            value['training_receipt_sha256'] != TRAIN_RECEIPT_SHA or
            value['lora_dtype'] != 'bfloat16' or value['tool_parser'] != 'hermes' or
            value['native_thinking'] is not False or not value['container_name'].startswith('alf4b-adapter-owned-')):
        raise ValueError('unqualified base/adapter/native serving identity')
    training = QUAL / 'learning_qualification_v1/attempt_v1/receipt.json'
    base_binding = QUAL / 'learning_qualification_v1/HF4B_MODEL_BINDING_V1.json'
    if sha(base_binding) != BASE_BINDING_SHA:
        raise ValueError('qualified base binding changed')
    if sha(training) != TRAIN_RECEIPT_SHA:
        raise ValueError('training receipt changed')
    saved = json.loads(training.read_text())
    adapter = QUAL / 'learning_qualification_v1/attempt_v1/adapter'
    if value['adapter_files'] != saved['adapter_files']:
        raise ValueError('serving adapter is not the qualified checkpoint')
    for name, expected in value['adapter_files'].items():
        if Path(name).name != name or sha(adapter / name) != expected:
            raise ValueError('adapter bytes changed')
    if verify_container:
        actual = subprocess.check_output(['docker', 'inspect', '--format', '{{.Id}} {{.Image}} {{.State.Running}}',
                                         value['container_name']], text=True).strip()
        if actual != value['container_id'] + ' ' + value['image_id'] + ' true':
            raise ValueError('owned serving container identity changed')
    return value


def serving(value, arm):
    if arm not in {'base', 'trained'}:
        raise ValueError('world qualification compares base and trained only')
    return {key: value[key] for key in ['host', 'port', 'context', 'output']} | {'model_id': value['model_ids'][arm]}


def client_config(server):
    # Both arms use the same SDK/client model name. Only relay dispatch selects LoRA.
    return recovery().actor().config(dict(server, model_id=CLIENT_ID), 17)


def check_root(root, arm):
    if arm not in {'base', 'trained'}:
        raise ValueError('unsupported qualification arm')
    root = Path(root).absolute()
    if root != root.resolve():
        raise ValueError('episode path must not traverse symlinks or aliases')
    expected = QUAL / 'adapter_qualification_v1/episodes' / arm
    if root.parent != expected or not re.fullmatch(r'attempt_v[1-9][0-9]*', root.name):
        raise ValueError('use canonical adapter_qualification_v1/episodes/arm/attempt_vN')
    return root


def tokenizer_qualifier():
    from transformers import AutoTokenizer
    model = Path('/home/testuser/wzh/models/hf/Qwen3-4B')
    tokenizer = AutoTokenizer.from_pretrained(model, local_files_only=True, trust_remote_code=False)
    binding = {name: sha(model / name) for name in ['tokenizer.json', 'tokenizer_config.json']}
    def qualify(payload):
        # Same vLLM argument projection as the verified frozen serving-template helper.
        messages = recovery().template_messages(payload, 'teacher27b')
        ids = tokenizer.apply_chat_template(messages, tools=payload.get('tools') or None, tokenize=True,
                    return_dict=False, add_generation_prompt=True, enable_thinking=False)
        count = len(recovery().input_ids(ids))
        return {'input_tokens': count, 'reserved_output': 4096, 'context': 16384,
                'fits': count + 4096 <= 16384,
                'payload_sha256': hashlib.sha256(json.dumps(payload, separators=(',', ':')).encode()).hexdigest()}
    return binding, qualify


def prepare(root, arm, profile_path, profile_sha):
    root = check_root(root, arm)
    root.mkdir(parents=True, exist_ok=True)
    if any(root.iterdir()):
        raise FileExistsError('fresh empty episode root required')
    rec, core = recovery(), recovery().actor()
    bound = profile(profile_path, profile_sha)
    server = serving(bound, arm)
    data = rec.source('heat2_history_v1')
    world = None
    try:
        m = data['manifest']
        world, initial, _ = core.start_world(root, m['game_id'], m['seed'], 'preflight', m['caps'],
                                           m['pool_binding']['path'], m['pool_binding']['sha256'])
        current, replay = rec.replay(data, initial, lambda action: rec.bridge().client_step(world[1] / 's', action),
                                    root / 'preflight_replay.jsonl')
    finally:
        if world:
            core.stop_world(world)
    (root / 'task.txt').write_bytes(rec.recovery_prompt(data, current).encode())
    core.write_new(root / 'handoff_public.json', current)
    core.write_new(root / 'opencode_config.json', client_config(server))
    token_binding, _ = tokenizer_qualifier()
    image = subprocess.check_output(['docker', 'image', 'inspect', core.IMAGE, '--format', '{{.Id}}'], text=True).strip()
    manifest = {'label': 'EXPOSED_STATE_BASE_ADAPTER_HARNESS_QUALIFICATION', 'arm': arm,
                'source_binding': data['binding'], 'caps': data['binding']['remaining_caps'],
                'profile_path': str(Path(profile_path).resolve()), 'profile_sha256': profile_sha,
                'serving': server, 'model_id': CLIENT_ID, 'sampling': core.model_payload({}, 'student8b', server, 17, False),
                'dtype': 'bfloat16', 'lora_dtype': bound['lora_dtype'], 'tokenizer_files_sha256': token_binding,
                'uid': os.getuid(), 'gid': os.getgid(), 'image_id': image, 'components': components(),
                'prompt_sha256': sha(root / 'task.txt'), 'handoff_sha256': sha(root / 'handoff_public.json'),
                'config_sha256': sha(root / 'opencode_config.json'),
                'heldout_evaluation': False, 'trained_prompt_and_layout': True,
                'no_gguf_bf16_method_comparison': True, 'source_cost_charge_once': data['binding']['sha256']['receipt.json']}
    core.write_new(root / 'manifest.json', manifest)
    return manifest


def verify(root, digest):
    root = Path(root).absolute()
    if sha(root / 'manifest.json') != digest:
        raise ValueError('frozen episode manifest changed')
    m = json.loads((root / 'manifest.json').read_text())
    check_root(root, m['arm'])
    rec, core = recovery(), recovery().actor()
    bound = profile(m['profile_path'], m['profile_sha256'])
    data = rec.source('heat2_history_v1')
    binding, qualify = tokenizer_qualifier()
    if (m['components'] != components() or m['source_binding'] != data['binding'] or
            m['caps'] != data['binding']['remaining_caps'] or m['serving'] != serving(bound, m['arm']) or
            m['model_id'] != CLIENT_ID or m['tokenizer_files_sha256'] != binding or
            (m['uid'], m['gid']) != (os.getuid(), os.getgid()) or
            m['sampling'] != core.model_payload({}, 'student8b', m['serving'], 17, False)):
        raise ValueError('episode inputs/model/components/caps changed')
    for name, key in [('task.txt', 'prompt_sha256'), ('handoff_public.json', 'handoff_sha256'), ('opencode_config.json', 'config_sha256')]:
        if sha(root / name) != m[key]:
            raise ValueError('frozen actor input changed')
    if (root / 'task.txt').read_bytes() != rec.recovery_prompt(data, data['steps'][-1]['state']).encode():
        raise ValueError('public recovery prompt changed')
    return m, data, qualify


def execute(root, digest, *, fake_endpoint=None):
    root = Path(root).absolute()
    m, data, qualify = verify(root, digest)
    rec, core = recovery(), recovery().actor()
    core.write_new(root / 'reservation.json', {'manifest_sha256': digest, 'mode': 'OWNED_FAKE' if fake_endpoint else 'REAL_EXPOSED_STATE_QUALIFICATION'})
    world = relay = model_dir = None
    replay_cost = None
    errors, status, docker_exit = [], 'FAILED', None
    started = time.monotonic()
    name = 'alf-adapter-actor-owned-' + str(os.getpid()) + '-' + str(time.monotonic_ns())
    class QualifiedRelay(core.ModelRelay):
        def forward(self, upstream, packet, payload=None, post_index=None):
            proof = qualify(payload)
            core.write_new(root / 'actual_template_tokens' / (str(post_index).zfill(5) + '.json'), proof)
            if not proof['fits']:
                raise ValueError('actual native template exceeds context with reserved output')
            return super().forward(upstream, packet, payload, post_index)
    try:
        src = data['manifest']
        world, initial, _ = core.start_world(root, src['game_id'], 17, 'execute', src['caps'],
                                            src['pool_binding']['path'], src['pool_binding']['sha256'])
        current, replay_cost = rec.replay(data, initial, lambda action: rec.bridge().client_step(world[1] / 's', action),
                                          root / 'execute_replay.jsonl')
        if current != json.loads((root / 'handoff_public.json').read_text()):
            raise ValueError('actual handoff differs from preflight')
        work = root / 'workspace'
        work.mkdir()
        for original, copied in [('task.txt', 'task.txt'), ('opencode_config.json', 'opencode.json')]:
            (work / copied).write_bytes((root / original).read_bytes())
        (work / 'guest.py').write_text(core.GUEST)
        model_dir = core.socket_directory('m')
        server = m['serving']
        relay = QualifiedRelay(root, model_dir, 'student8b', server, 17,
                  fake_endpoint or (server['host'], server['port']), m['caps'], m['sampling'], student_enable_thinking=False)
        command = core.docker_command(work, world[1], model_dir, m, name)
        core.write_new(root / 'docker_command.json', {'argv': command})
        with (root / 'raw.jsonl').open('xb') as out, (root / 'docker.stderr').open('xb') as err:
            done = subprocess.run(command, stdout=out, stderr=err, timeout=m['caps']['seconds'])
        status, docker_exit = 'RETURNED', done.returncode
    except subprocess.TimeoutExpired:
        status = 'EPISODE_TIMEOUT'
    except Exception as exc:
        errors.append({'type': type(exc).__name__, 'error': str(exc)})
    finally:
        if relay:
            relay.begin_close()
        try:
            subprocess.run(['docker', 'rm', '-f', name], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, timeout=15)
        except Exception as exc:
            errors.append({'cleanup': 'actor_container', 'error': str(exc)})
        for label, cleanup in [('relay', relay.close if relay else (lambda: core.cleanup_directory(model_dir)) if model_dir else None),
                               ('world', (lambda: core.stop_world(world)) if world else None)]:
            if cleanup:
                try:
                    cleanup()
                except Exception as exc:
                    errors.append({'cleanup': label, 'error': str(exc)})
        events = [json.loads(line) for line in (root / 'execute_world.jsonl').read_text().splitlines()] if (root / 'execute_world.jsonl').exists() else []
        states = [event['state'] for event in events if event.get('event') in {'reset', 'step'}]
        final = states[-1] if states else None
        responses = [json.loads(p.read_text()) for p in sorted((root / 'responses').glob('*.receipt.json'))]
        receipt = {'label': 'OWNED_FAKE_NOT_METHOD' if fake_endpoint else m['label'], 'status': status,
                   'arm': m['arm'], 'dtype': m['dtype'], 'lora_dtype': m['lora_dtype'], 'serving': m['serving'],
                   'manifest_sha256': digest, 'source_binding': m['source_binding'], 'caps': m['caps'],
                   'elapsed_seconds': time.monotonic() - started, 'errors': errors,
                   'model_relay_errors': relay.errors if relay else [], 'docker_exit': docker_exit,
                   'model_posts': relay.budget.posts if relay else 0, 'forwarded_posts': relay.forwarded if relay else 0,
                   'real_model_calls': 0 if fake_endpoint else relay.forwarded if relay else 0,
                   'response_receipts': responses,
                   'unknown_usage_model_posts': max(0, (relay.forwarded if relay else 0) - sum(bool(r.get('complete') and r.get('usage')) for r in responses)),
                   'replay_control_cost': replay_cost, 'final_world_state': final,
                   'actor_world_actions': max(0, final['action_count'] - len(data['steps'])) if final else 0,
                   'won': bool(final and final['won']), 'handoff_delivery': relay.delivery if relay else None,
                   'qualifies_learning_gain': False, 'heldout_evaluation': False,
                   'sampling': m['sampling'], 'client_model_id_same_both_arms': CLIENT_ID}
        core.write_new(root / 'receipt.json', receipt)
    return receipt


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    mode = parser.add_mutually_exclusive_group(required=True)
    mode.add_argument('--preflight-only', action='store_true')
    mode.add_argument('--execute', action='store_true')
    parser.add_argument('--run-root', type=Path, required=True)
    parser.add_argument('--arm', choices=['base', 'trained'])
    parser.add_argument('--profile', type=Path)
    parser.add_argument('--profile-sha')
    parser.add_argument('--manifest-sha')
    args = parser.parse_args(argv)
    if args.execute:
        if not args.manifest_sha or args.arm or args.profile or args.profile_sha:
            parser.error('execute only accepts frozen root and manifest SHA')
        result = execute(args.run_root, args.manifest_sha)
    else:
        if not all([args.arm, args.profile, args.profile_sha]):
            parser.error('preflight requires arm and serving profile/SHA')
        result = prepare(args.run_root, args.arm, args.profile, args.profile_sha)
    print(json.dumps(result))


if __name__ == '__main__':
    main()
