"""Finite, matched LoRA comparison on frozen native corrective-fragment data.

Private plans contain tokenized public contexts, D-extracted reference edits and
native outcome bindings. Training is not an OpenCode episode or method benefit.
All arms use the same four sequence forwards, initialization and update count.
"""
from __future__ import annotations

import argparse
import fcntl
import gc
import hashlib
import importlib.util
import json
import math
from pathlib import Path
import time
import traceback


def digest(path):
    sha = hashlib.sha256()
    with Path(path).open('rb') as stream:
        for block in iter(lambda: stream.read(8 * 1024**2), b''):
            sha.update(block)
    return sha.hexdigest()


def load_module(path):
    spec = importlib.util.spec_from_file_location(Path(path).stem, path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def sequence_score(model, row, device):
    """Sum log p over the current complete assistant fragment, including EOS.

    Prompt/tool-result tokens and trailing template whitespace never receive
    supervision. Predictor positions are offset by one for causal scoring.
    """
    import torch
    labels, ids = row['labels'], row['input_ids']
    if len(ids) != len(labels) or not ids:
        raise ValueError('aligned nonempty ids and labels required')
    positions = [i for i, x in enumerate(labels) if x != -100]
    if (not positions or positions[0] <= 0
            or positions != list(range(positions[0], positions[-1] + 1))
            or any(labels[i] != ids[i] for i in positions)):
        raise ValueError('one contiguous unchanged completion, after a prompt, required')
    predictors = torch.tensor([i - 1 for i in positions], device=device)
    inputs = torch.tensor([ids], device=device)
    targets = torch.tensor([labels[i] for i in positions], device=device)
    output = model(input_ids=inputs, attention_mask=torch.ones_like(inputs),
                   logits_to_keep=predictors, use_cache=False)
    if output.logits.shape[:2] != (1, len(positions)):
        raise ValueError('model did not honor sparse causal predictor positions')
    chosen = output.logits[0].float().log_softmax(-1).gather(1, targets[:, None])
    return chosen.sum(), len(positions)


def compare_loss(scores, reference, utilities, observed, *, arm, beta):
    """Return common BC anchor and the declared arm's preference component."""
    import torch
    import torch.nn.functional as F
    if arm not in {'bc', 'dpo', 'row', 'coupled'}:
        raise ValueError('unknown comparison arm')
    core = load_module(Path(__file__).with_name('feedback_interaction_learning.py'))
    logp, lengths = scores
    # One successful complete fragment per context; native ties are not used here.
    winners = utilities.argmax(-1)
    bc = -(logp.gather(-1, winners[..., None]).squeeze(-1)
           / lengths.gather(-1, winners[..., None]).squeeze(-1)).mean()
    if arm == 'bc':
        pref = logp.sum() * 0
    elif arm == 'dpo':
        margin = beta * ((logp - reference)[..., 0] - (logp - reference)[..., 1])
        sign = (utilities[..., 0] - utilities[..., 1]).sign()
        pref = -F.logsigmoid(sign * margin).mean()
    else:
        result = core.interaction_update(logp, reference, utilities, observed,
                    behavior_clone=0., beta=beta,
                    interaction_weight=1. if arm == 'coupled' else 0.)
        pref = result['total']
    return bc, pref


def run(root, plan_sha):
    import torch
    from peft import LoraConfig, get_peft_model
    from transformers import AutoModelForCausalLM, AutoTokenizer

    root = Path(root).resolve()
    plan_path = root / 'PLAN.json'
    if (digest(plan_path) != plan_sha or (root / 'RESULT.json').exists()
            or (root / 'LIVE.json').exists()):
        raise ValueError('wrong plan or terminal run; do not resume blindly')
    plan = json.loads(plan_path.read_text())
    if (sorted(plan['arm_order']) != ['bc', 'coupled', 'dpo', 'row']
            or not 1 <= plan['updates_per_arm'] <= 24
            or not 0 < plan['arm_wall_seconds'] <= 1200
            or not 0 < plan['max_wall_seconds'] <= 6000):
        raise ValueError('finite four-arm budget required')
    for path, sha in plan['components'].items():
        if digest(path) != sha:
            raise ValueError('component changed: ' + path)
    data_path = Path(plan['data']['path'])
    if digest(data_path) != plan['data']['sha256']:
        raise ValueError('data changed')
    data = json.loads(data_path.read_text())
    rows = data['rows']
    if len(rows) != 4 or [r['cell'] for r in rows] != [[0, 0], [0, 1], [1, 0], [1, 1]]:
        raise ValueError('exact ordered native four-cell data required')
    lease = Path(plan['resource_lock']).open('a')
    fcntl.flock(lease, fcntl.LOCK_EX | fcntl.LOCK_NB)
    started = time.monotonic()
    receipt = dict(status='RUNNING', pid=__import__('os').getpid(), plan_sha256=plan_sha,
                   model_loads=0, forward_calls_started=0, forward_calls_completed=0,
                   forward_sequence_tokens_upper_bound=0, forward_sequence_tokens_completed=0,
                   forward_supervised_tokens_completed=0, generation_calls=0,
                   optimizer_updates=0, http_model_requests=0, arms={})
    def publish():
        tmp = root / 'LIVE.tmp'
        tmp.write_text(json.dumps(receipt, indent=2))
        tmp.replace(root / 'LIVE.json')
    def score_all(model):
        values, lengths = [], []
        for row in rows:
            receipt['forward_calls_started'] += 1
            receipt['forward_sequence_tokens_upper_bound'] += len(row['input_ids'])
            value, length = sequence_score(model, row, 'cuda:0')
            receipt['forward_calls_completed'] += 1
            receipt['forward_sequence_tokens_completed'] += len(row['input_ids'])
            receipt['forward_supervised_tokens_completed'] += length
            values.append(value)
            lengths.append(length)
        return torch.stack(values).reshape(1, 2, 2), torch.tensor(lengths, device='cuda:0').reshape(1, 2, 2)
    def save_new(path, value):
        with path.open('x') as stream:
            json.dump(value, stream, indent=2)
    model = optimizer = None
    try:
        binding_path = Path(plan['model_binding']['path'])
        if digest(binding_path) != plan['model_binding']['sha256']:
            raise ValueError('base model binding changed')
        binding = json.loads(binding_path.read_text())
        if binding['model_dir'] != plan['model_path']:
            raise ValueError('wrong base model')
        verifier = load_module(Path(__file__).with_name('alfworld_supervision_learning.py'))
        verifier.validate_model_binding(str(binding_path), plan['model_binding']['sha256'],
                    dict(model_path=plan['model_path'], tokenizer_binding=data['tokenizer']))
        torch.manual_seed(plan['seed'])
        tokenizer = AutoTokenizer.from_pretrained(plan['model_path'], local_files_only=True,
                                                  trust_remote_code=False)
        receipt['model_loads'] += 1
        model = AutoModelForCausalLM.from_pretrained(plan['model_path'],
                    dtype=torch.bfloat16, device_map={'': 0}, attn_implementation='sdpa',
                    trust_remote_code=False, local_files_only=True)
        model = get_peft_model(model, LoraConfig(r=8, lora_alpha=16, lora_dropout=0.,
                        target_modules=['q_proj', 'v_proj'], task_type='CAUSAL_LM', bias='none'))
        trainable = [p for p in model.parameters() if p.requires_grad]
        initial = {n: p.detach().clone() for n, p in model.named_parameters() if p.requires_grad}
        if not trainable or any('lora_' not in n for n in initial):
            raise ValueError('unexpected trainable base parameters')
        receipt['trainable_parameters'] = sum(p.numel() for p in trainable)
        receipt['initial_adapter_sha256'] = hashlib.sha256(b''.join(
            initial[n].cpu().contiguous().view(torch.uint8).numpy().tobytes()
            for n in sorted(initial))).hexdigest()
        model.eval()
        with torch.no_grad(), model.disable_adapter():
            reference = score_all(model)[0].detach()
        save_new(root / 'REFERENCE.json', reference.cpu().tolist())
        utilities = torch.tensor(data['utilities'], device='cuda:0', dtype=torch.float32).reshape(1, 2, 2)
        observed = torch.ones_like(utilities, dtype=torch.bool)
        model.gradient_checkpointing_enable(gradient_checkpointing_kwargs={'use_reentrant': False})
        model.enable_input_require_grads()
        target_grad_norm = None
        # Calibrate from frozen initial data, never from evaluation outcomes.
        model.train()
        values = score_all(model)
        calibrations = {}
        for arm in ['row', 'dpo', 'coupled']:
            _, pref = compare_loss(values, reference, utilities, observed, arm=arm, beta=plan['beta'])
            grads = torch.autograd.grad(pref, trainable, retain_graph=True, allow_unused=True)
            norm = math.sqrt(sum(float(g.detach().float().square().sum()) for g in grads if g is not None))
            if not math.isfinite(norm) or norm <= 0:
                raise ValueError('invalid initial preference gradient')
            if arm == 'row':
                target_grad_norm = norm
            calibrations[arm] = dict(initial_gradient_norm=norm, fixed_scale=target_grad_norm / norm)
        calibrations['bc'] = dict(initial_gradient_norm=0., fixed_scale=0.)
        save_new(root / 'GRADIENT_SCALES.json', calibrations)
        del values, grads, pref, _
        gc.collect()
        for arm in plan['arm_order']:
            if time.monotonic() - started > plan['max_wall_seconds']:
                raise TimeoutError('batch wall cap reached before arm')
            arm_root = root / arm
            arm_root.mkdir()
            with torch.no_grad():
                for name, param in model.named_parameters():
                    if name in initial:
                        param.copy_(initial[name])
            torch.manual_seed(plan['seed'])
            optimizer = torch.optim.AdamW(trainable, lr=plan['learning_rate'], weight_decay=.01)
            arm_start = time.monotonic()
            steps = []
            for step in range(plan['updates_per_arm']):
                if (time.monotonic() - arm_start > plan['arm_wall_seconds']
                        or time.monotonic() - started > plan['max_wall_seconds']):
                    raise TimeoutError('training wall cap reached')
                optimizer.zero_grad(set_to_none=True)
                scores = score_all(model)
                bc, pref = compare_loss(scores, reference, utilities, observed, arm=arm, beta=plan['beta'])
                loss = bc + calibrations[arm]['fixed_scale'] * pref
                if not torch.isfinite(loss):
                    raise FloatingPointError('nonfinite loss')
                loss.backward()
                norm = float(torch.nn.utils.clip_grad_norm_(trainable, 1.))
                if not math.isfinite(norm) or norm <= 0:
                    raise FloatingPointError('nonfinite or zero adapter gradient')
                optimizer.step()
                receipt['optimizer_updates'] += 1
                steps.append(dict(step=step + 1, bc=float(bc.detach()),
                                  preference=float(pref.detach()), total=float(loss.detach()),
                                  gradient_norm_before_clipping=norm))
                receipt['arms'][arm] = dict(updates=len(steps), seconds=time.monotonic() - arm_start,
                                          latest=steps[-1])
                publish()
                del scores, bc, pref, loss
            model.eval()
            model.gradient_checkpointing_disable()
            model.save_pretrained(arm_root / 'adapter', safe_serialization=True)
            with torch.no_grad():
                final_scores = score_all(model)[0].cpu().tolist()
            save_new(arm_root / 'TRAINING.json', dict(steps=steps, final_logp=final_scores,
                    seconds=time.monotonic() - arm_start, adapter_files={
                    p.name: digest(p) for p in (arm_root / 'adapter').iterdir() if p.is_file()}))
            model.gradient_checkpointing_enable(gradient_checkpointing_kwargs={'use_reentrant': False})
            model.train()
            del optimizer
            optimizer = None
            gc.collect()
        receipt['status'] = 'ALL_FOUR_ADAPTERS_TRAINED'
    except Exception:
        receipt['status'] = 'FAILED'
        receipt['error'] = traceback.format_exc()
        raise
    finally:
        receipt['wall_seconds'] = time.monotonic() - started
        publish()
        save_new(root / 'RESULT.json', receipt)
        del model, optimizer
        gc.collect()
        torch.cuda.empty_cache()
        fcntl.flock(lease, fcntl.LOCK_UN)
        lease.close()


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--root', required=True)
    parser.add_argument('--plan-sha', required=True)
    args = parser.parse_args()
    run(args.root, args.plan_sha)
