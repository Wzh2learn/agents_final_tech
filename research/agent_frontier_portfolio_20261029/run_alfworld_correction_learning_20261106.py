"""Two-step PEFT qualification on frozen real correction data, not a method trial.

No model is loaded on import or prepare. Execute needs a frozen manifest and a
fresh reservation. Shared servers are never managed by this program.
"""
from __future__ import annotations
import argparse
import gc
import hashlib
import importlib.metadata
import json
import math
from pathlib import Path
import re
import time

REPO = Path(__file__).resolve().parents[2]
ROOT = Path('/home/testuser/wzh/research_evidence/agent_learning_20261030/alfworld_text_qualification_20261106/learning_qualification_v1')
MODEL_BINDING = ROOT / 'HF4B_MODEL_BINDING_V1.json'
MODEL_BINDING_SHA = 'e74513f1fe22a2cb9198714738bb86b2f78c05eb0474b25e3759394b8a709823'
MODEL = Path('/home/testuser/wzh/models/hf/Qwen3-4B')
CORRECTIONS_SHA = '06a6313b8d62709699dfe8e88b13e9736b24d3daccee22eaa98abeb56893b7c1'
PROVIDER_MANIFEST_SHA = 'afdc84eb2a337a06be923cebe742debee8d92c08cab5645c5369eff639eab058'
CONFIG = {'seed': 17, 'optimizer_steps': 2, 'batch_size': 1, 'learning_rate': 0.0002,
          'lora_r': 8, 'lora_alpha': 16, 'lora_dropout': 0.05,
          'target_modules': ['q_proj', 'v_proj'], 'max_length': 8192,
          'min_cuda_free_bytes': 14 * 1024**3, 'generation_limit': 192,
          'qualification_only': True}


def sha(path):
    h = hashlib.sha256()
    with Path(path).open('rb') as stream:
        for chunk in iter(lambda: stream.read(8 * 1024**2), b''):
            h.update(chunk)
    return h.hexdigest()


def write_new(path, value):
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open('x', encoding='utf8') as stream:
        json.dump(value, stream, indent=2, ensure_ascii=False)
        stream.write('\n')


def validate_row(row):
    ids, mask, labels = (row[key] for key in ('input_ids', 'attention_mask', 'labels'))
    if not ids or not (len(ids) == len(mask) == len(labels)) or len(ids) > CONFIG['max_length']:
        raise ValueError('missing, unequal or overlength arrays; truncation is prohibited')
    if any(type(x) is not int or x < 0 for x in ids) or any(x != 1 for x in mask):
        raise ValueError('only complete unpadded token rows are accepted')
    positions = [i for i, label in enumerate(labels) if label != -100]
    if not positions or positions[0] == 0 or positions != list(range(positions[0], positions[-1] + 1)):
        raise ValueError('missing or non-contiguous current assistant completion')
    if any(type(labels[i]) is not int or labels[i] != ids[i] for i in positions):
        raise ValueError('supervised token is not the actual completion token')
    if row.get('source_role') != 'teacher' or not row.get('source_group') or not row.get('row_id'):
        raise ValueError('teacher-only qualification requires source identity')
    return positions


def load_rows(path, digest):
    path = Path(path)
    if path.is_symlink() or sha(path) != digest:
        raise ValueError('frozen rows changed')
    rows = [json.loads(line) for line in path.read_text().splitlines() if line.strip()]
    if len(rows) < CONFIG['optimizer_steps']:
        raise ValueError('not enough distinct rows for the two-step qualification')
    for row in rows:
        validate_row(row)
    if len({row['row_id'] for row in rows}) != len(rows):
        raise ValueError('duplicate row identities')
    return rows


def model_binding():
    if sha(MODEL_BINDING) != MODEL_BINDING_SHA:
        raise ValueError('model binding changed')
    binding = json.loads(MODEL_BINDING.read_text())
    if binding['model_dir'] != str(MODEL):
        raise ValueError('unexpected qualification base')
    for row in binding['files']:
        path = Path(row['path'])
        if path.is_symlink() or path.parent != MODEL or path.stat().st_size != row['bytes'] or sha(path) != row['sha256']:
            raise ValueError('base-model file changed')
    return binding


def validate_export(path, digest, rows_path, rows_sha, rows, binding):
    if sha(path) != digest:
        raise ValueError('export manifest changed')
    data = json.loads(Path(path).read_text())
    assets = data['model_assets']
    if (data['rows_file'] != 'rows.jsonl' or Path(path).parent / data['rows_file'] != Path(rows_path) or
            data['rows_sha256'] != rows_sha or data['row_count'] != len(rows) or
            data['source_roles'] != ['teacher'] or assets['model_path'] != str(MODEL) or
            assets['enable_thinking'] is not False or
            data['frozen_manifest_sha256'] != CORRECTIONS_SHA or data['provider_manifest_sha256'] != PROVIDER_MANIFEST_SHA or
            data['exporter_sha256'] != components()[str(Path(__file__).with_name('alfworld_correction_data_20261106.py'))]):
        raise ValueError('export model/roles/source/files do not match the qualification')
    files = {Path(row['path']).name: row['sha256'] for row in binding['files']}
    if any(files.get(name) != digest for name, digest in assets['files_sha256'].items()):
        raise ValueError('export tokenizer differs from bound training base')
    groups = sorted({r['source_group'] for r in rows})
    if data['source_groups'] != groups or data['source_group_count'] != len(groups):
        raise ValueError('export incorrectly splits source groups')
    for row in rows:
        positions = validate_row(row)
        if row['input_ids'][positions[-1]] != assets['eos_token_id'] or row['target_token_ids'] != [row['labels'][i] for i in positions]:
            raise ValueError('export assistant EOS or target token identity mismatch')
    return data


def check_root(root):
    root = Path(root).resolve()
    if root.parent != ROOT or not re.fullmatch(r'attempt_v[1-9][0-9]*', root.name):
        raise ValueError('use canonical learning_qualification_v1/attempt_vN')
    return root


def components():
    data = Path(__file__).with_name('alfworld_correction_data_20261106.py')
    return {str(path): sha(path) for path in (Path(__file__).resolve(), data)}


def prepare(root, rows_path, rows_sha, data_manifest, data_manifest_sha):
    root = check_root(root)
    root.mkdir(parents=True, exist_ok=True)
    if any(root.iterdir()):
        raise FileExistsError('fresh empty qualification root required')
    rows_path, data_manifest = Path(rows_path).resolve(), Path(data_manifest).resolve()
    if data_manifest.is_symlink() or sha(data_manifest) != data_manifest_sha:
        raise ValueError('export manifest changed')
    rows = load_rows(rows_path, rows_sha)
    binding = model_binding()
    data = validate_export(data_manifest, data_manifest_sha, rows_path, rows_sha, rows, binding)
    manifest = {'label': 'TRAINING_AND_ADAPTER_QUALIFICATION_NOT_METHOD_EVIDENCE',
                'config': CONFIG, 'components': components(), 'model_binding_sha256': MODEL_BINDING_SHA,
                'model_path': str(MODEL), 'model_file_count': len(binding['files']),
                'rows_path': str(rows_path), 'rows_sha256': rows_sha,
                'data_manifest_path': str(data_manifest), 'data_manifest_sha256': data_manifest_sha,
                'all_rows': len(rows), 'selected_row_ids': [r['row_id'] for r in rows[:2]],
                'source_groups': sorted({r['source_group'] for r in rows}),
                'future_confirmation_exclusions': [case['future_confirmation_exclusion'] for case in data['source_cases']],
                'not_independent_train_test_split': True, 'heldout_evaluation': False,
                'training_start': 'fresh HF base, one default adapter, no parent adapter',
                'method': 'q/v LoRA; exact masked causal CE with only supervised prediction positions projected',
                'references': ['https://github.com/huggingface/transformers/blob/main/src/transformers/models/qwen3/modeling_qwen3.py',
                               'https://github.com/huggingface/trl/blob/main/docs/source/sft_trainer.md'],
                'inference_scope': 'in-process matched BF16 base versus trained adapter on one exposed prompt; not an OpenCode or world rollout'}
    write_new(root / 'manifest.json', manifest)
    return manifest


def verify(root, digest):
    root = check_root(root)
    if sha(root / 'manifest.json') != digest:
        raise ValueError('qualification manifest changed')
    manifest = json.loads((root / 'manifest.json').read_text())
    if manifest['config'] != CONFIG or manifest['components'] != components() or manifest['model_binding_sha256'] != MODEL_BINDING_SHA:
        raise ValueError('qualification implementation or configuration changed')
    if sha(manifest['data_manifest_path']) != manifest['data_manifest_sha256']:
        raise ValueError('source data manifest changed')
    rows = load_rows(manifest['rows_path'], manifest['rows_sha256'])
    if [r['row_id'] for r in rows[:2]] != manifest['selected_row_ids']:
        raise ValueError('selected teacher rows changed')
    binding = model_binding()
    validate_export(manifest['data_manifest_path'], manifest['data_manifest_sha256'],
                    manifest['rows_path'], manifest['rows_sha256'], rows, binding)
    return root, manifest, rows


def sparse_causal(model, row, device):
    """Equivalent to ordinary masked causal CE, without prefix-vocabulary logits."""
    import torch
    import torch.nn.functional as functional
    positions = validate_row(row)
    ids = torch.tensor([row['input_ids']], device=device)
    attention = torch.tensor([row['attention_mask']], device=device)
    # The logit at t-1 predicts the label at t, exactly as the HF causal shift.
    predictors = torch.tensor([p - 1 for p in positions], device=device)
    targets = torch.tensor([row['labels'][p] for p in positions], device=device)
    output = model(input_ids=ids, attention_mask=attention, logits_to_keep=predictors, use_cache=False)
    logits = output.logits[0]
    return functional.cross_entropy(logits.float(), targets), logits


def execute(root, digest):
    root, manifest, rows = verify(root, digest)
    write_new(root / 'reservation.json', {'manifest_sha256': digest, 'mode': 'TWO_OPTIMIZER_STEPS_AND_TWO_IN_PROCESS_GENERATIONS'})
    import torch
    from peft import LoraConfig, get_peft_model
    from transformers import AutoModelForCausalLM, AutoTokenizer, set_seed
    started = time.monotonic()
    receipt = {'label': manifest['label'], 'status': 'FAILED', 'manifest_sha256': digest,
               'versions': {n: importlib.metadata.version(n) for n in ['torch', 'transformers', 'peft']},
               'optimizer_steps_attempted': 0, 'optimizer_steps_completed': 0, 'training_input_tokens': 0,
               'training_supervised_tokens': 0, 'training_attempted_input_tokens_upper_bound': 0,
               'training_attempted_supervised_tokens_upper_bound': 0, 'diagnostic_forward_calls': 0,
               'generation_attempts_started': 0, 'generation_attempts_completed': 0,
               'generation_prompt_tokens': 0, 'generation_completion_tokens': 0,
               'generation_attempted_prompt_tokens_upper_bound': 0,
               'http_model_requests': 0, 'judge_calls': 0, 'heldout_evaluation': False,
               'source_groups': manifest['source_groups'], 'qualifies_learning_gain': False}
    model = optimizer = None
    try:
        free, total = torch.cuda.mem_get_info(0)
        receipt['cuda_memory_before'] = {'free': free, 'total': total}
        if free < CONFIG['min_cuda_free_bytes']:
            raise RuntimeError('insufficient measured CUDA headroom; no automatic service changes')
        set_seed(CONFIG['seed'])
        torch.cuda.reset_peak_memory_stats()
        model = AutoModelForCausalLM.from_pretrained(MODEL, dtype=torch.bfloat16,
                    device_map={'': 0}, attn_implementation='sdpa', local_files_only=True, trust_remote_code=False)
        model.config.use_cache = False
        model = get_peft_model(model, LoraConfig(r=8, lora_alpha=16, lora_dropout=0.05,
                    bias='none', task_type='CAUSAL_LM', target_modules=CONFIG['target_modules']))
        trainable = {n: p for n, p in model.named_parameters() if p.requires_grad}
        if not trainable or any('lora_' not in n for n in trainable):
            raise ValueError('unexpected trainable base parameters')
        receipt['trainable_parameters'] = sum(p.numel() for p in trainable.values())
        model.eval()
        with torch.no_grad(), model.disable_adapter():
            _, logits = sparse_causal(model, rows[0], model.device)
            base_before = logits.float().cpu()
        receipt['diagnostic_forward_calls'] += 1
        with torch.no_grad():
            _, logits = sparse_causal(model, rows[0], model.device)
            zero_before = logits.float().cpu()
        receipt['diagnostic_forward_calls'] += 1
        receipt['zero_adapter_max_logit_difference'] = float((base_before - zero_before).abs().max())
        del logits, zero_before
        model.gradient_checkpointing_enable(gradient_checkpointing_kwargs={'use_reentrant': False})
        model.enable_input_require_grads()
        model.train()
        optimizer = torch.optim.AdamW(trainable.values(), lr=CONFIG['learning_rate'])
        steps = []
        for row in rows[:CONFIG['optimizer_steps']]:
            receipt['optimizer_steps_attempted'] += 1
            receipt['training_attempted_input_tokens_upper_bound'] += len(row['input_ids'])
            receipt['training_attempted_supervised_tokens_upper_bound'] += len(validate_row(row))
            optimizer.zero_grad(set_to_none=True)
            loss, logits = sparse_causal(model, row, model.device)
            if not torch.isfinite(loss):
                raise ValueError('non-finite supervised loss')
            loss.backward()
            gradients = [p.grad for p in trainable.values() if p.grad is not None]
            if not gradients or not all(torch.isfinite(g).all() for g in gradients):
                raise ValueError('missing or non-finite LoRA gradients')
            norm = math.sqrt(sum(float(g.float().square().sum()) for g in gradients))
            if not norm or any(p.grad is not None for n, p in model.named_parameters() if n not in trainable):
                raise ValueError('zero adapter gradients or unexpected base gradients')
            optimizer.step()
            receipt['optimizer_steps_completed'] += 1
            receipt['training_input_tokens'] += len(row['input_ids'])
            receipt['training_supervised_tokens'] += len(validate_row(row))
            steps.append({'row_id': row['row_id'], 'input_tokens': len(row['input_ids']),
                          'supervised_tokens': len(validate_row(row)), 'loss': float(loss.detach()), 'gradient_norm': norm})
            write_new(root / ('step_' + str(len(steps)) + '.json'), steps[-1])
            del loss, logits
        model.eval()
        model.gradient_checkpointing_disable()
        with torch.no_grad():
            _, logits = sparse_causal(model, rows[0], model.device)
            trained = logits.float().cpu()
        receipt['diagnostic_forward_calls'] += 1
        with torch.no_grad(), model.disable_adapter():
            _, logits = sparse_causal(model, rows[0], model.device)
            base_after = logits.float().cpu()
        receipt['diagnostic_forward_calls'] += 1
        receipt['base_max_logit_difference'] = float((base_before - base_after).abs().max())
        receipt['trained_vs_base_max_logit_difference'] = float((trained - base_after).abs().max())
        del logits
        adapter = root / 'adapter'
        model.save_pretrained(adapter, safe_serialization=True)
        tokenizer = AutoTokenizer.from_pretrained(MODEL, local_files_only=True, trust_remote_code=False)
        tokenizer.save_pretrained(adapter)
        receipt['adapter_files'] = {p.name: sha(p) for p in adapter.iterdir() if p.is_file()}
        model.load_adapter(adapter, adapter_name='roundtrip', is_trainable=False)
        model.set_adapter('roundtrip')
        model.eval()
        with torch.no_grad():
            _, logits = sparse_causal(model, rows[0], model.device)
            reloaded = logits.float().cpu()
        receipt['diagnostic_forward_calls'] += 1
        receipt['reload_max_logit_difference'] = float((trained - reloaded).abs().max())
        del logits
        prefix_length = validate_row(rows[0])[0]
        prompt = torch.tensor([rows[0]['input_ids'][:prefix_length]], device=model.device)
        for arm in ['matched_bf16_base', 'trained_adapter_roundtrip']:
            receipt['generation_attempts_started'] += 1
            receipt['generation_attempted_prompt_tokens_upper_bound'] += prefix_length
            context = model.disable_adapter() if arm == 'matched_bf16_base' else __import__('contextlib').nullcontext()
            with torch.inference_mode(), context:
                output = model.generate(prompt, attention_mask=torch.ones_like(prompt), max_new_tokens=CONFIG['generation_limit'],
                                do_sample=False, use_cache=True, pad_token_id=tokenizer.eos_token_id)
            generated = output[0, prefix_length:].tolist()
            write_new(root / (arm + '_generation.json'), {'arm': arm, 'prompt_tokens': prefix_length,
                'completion_token_ids': generated, 'text': tokenizer.decode(generated, skip_special_tokens=False),
                'scope': 'One exposed training prompt; not a heldout or environment task result'})
            receipt['generation_attempts_completed'] += 1
            receipt['generation_prompt_tokens'] += prefix_length
            receipt['generation_completion_tokens'] += len(generated)
            del output
        receipt['steps'] = steps
        receipt['status'] = 'QUALIFIED_TRAINING_GRAPH_AND_IN_PROCESS_RELOAD' if (
            receipt['zero_adapter_max_logit_difference'] <= 1e-4 and receipt['base_max_logit_difference'] <= 1e-4 and
            receipt['reload_max_logit_difference'] <= 1e-4 and receipt['trained_vs_base_max_logit_difference'] > 0) else 'NUMERICAL_QUALIFICATION_FAILED'
    except Exception as exc:
        receipt['error'] = {'type': type(exc).__name__, 'message': str(exc)}
    finally:
        receipt['wall_seconds'] = time.monotonic() - started
        if torch.cuda.is_available():
            receipt['torch_peak_allocated_bytes'] = torch.cuda.max_memory_allocated()
            receipt['torch_peak_reserved_bytes'] = torch.cuda.max_memory_reserved()
        del optimizer, model
        gc.collect()
        if torch.cuda.is_available():
            torch.cuda.empty_cache()
        write_new(root / 'receipt.json', receipt)
    return receipt


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    mode = parser.add_mutually_exclusive_group(required=True)
    mode.add_argument('--prepare', action='store_true')
    mode.add_argument('--execute', action='store_true')
    parser.add_argument('--run-root', type=Path, required=True)
    parser.add_argument('--manifest-sha')
    parser.add_argument('--rows', type=Path)
    parser.add_argument('--rows-sha')
    parser.add_argument('--data-manifest', type=Path)
    parser.add_argument('--data-manifest-sha')
    args = parser.parse_args(argv)
    if args.execute:
        if not args.manifest_sha or any([args.rows, args.rows_sha, args.data_manifest, args.data_manifest_sha]):
            parser.error('execute takes only run-root and frozen manifest SHA')
        result = execute(args.run_root, args.manifest_sha)
    else:
        if not all([args.rows, args.rows_sha, args.data_manifest, args.data_manifest_sha]):
            parser.error('prepare requires frozen rows and data-manifest paths/SHA')
        result = prepare(args.run_root, args.rows, args.rows_sha, args.data_manifest, args.data_manifest_sha)
    print(json.dumps(result, ensure_ascii=False))


if __name__ == '__main__':
    main()
