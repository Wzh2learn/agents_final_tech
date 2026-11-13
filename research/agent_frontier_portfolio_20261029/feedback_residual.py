"""Exact low-rank controls for the existing ordinary/recovery adapters.

Parameter arithmetic is a borrowed mechanism probe, not a new-method claim.
In particular, subtracting LoRA A/B factors separately is NOT subtraction of
their effective updates. This module concatenates factors so the dense update
is exactly the requested signed combination, without loading the base model.
"""
import argparse
import copy
import hashlib
import json
from pathlib import Path


def compose(ordinary, recovery, ordinary_config, recovery_config, weights):
    """Return an exact signed sum of standard, constant-scale LoRA updates."""
    import math
    import torch
    if len(weights) != 2 or not all(math.isfinite(v) for v in weights):
        raise ValueError('two finite weights required')
    for config in (ordinary_config, recovery_config):
        if (config.get('peft_type') != 'LORA' or config.get('bias') != 'none'
                or any(config.get(k) for k in ('use_dora', 'use_rslora',
                    'fan_in_fan_out', 'rank_pattern', 'alpha_pattern', 'modules_to_save'))):
            raise ValueError('only ordinary constant-scale, unbiased LoRA is supported')
        if (type(config['r']) is not int or config['r'] <= 0
                or not math.isfinite(config['lora_alpha']) or config['lora_alpha'] <= 0):
            raise ValueError('invalid rank or alpha')
    if ordinary_config.get('base_model_name_or_path') != recovery_config.get('base_model_name_or_path'):
        raise ValueError('base model bindings differ')
    if set(ordinary) != set(recovery) or not ordinary:
        raise ValueError('adapter projection sets differ or are empty')
    suffix = '.lora_A.weight'
    prefixes = sorted(k[:-len(suffix)] for k in ordinary if k.endswith(suffix))
    expected = {p + '.lora_' + factor + '.weight' for p in prefixes for factor in ('A', 'B')}
    if set(ordinary) != expected:
        raise ValueError('unpaired or unsupported adapter tensors')
    rank = ordinary_config['r'] + recovery_config['r']
    result = {}
    for prefix in prefixes:
        factors = []
        for source, config, weight in zip((ordinary, recovery),
                (ordinary_config, recovery_config), weights):
            a = source[prefix + '.lora_A.weight'].detach().to(device='cpu', dtype=torch.float32)
            b = source[prefix + '.lora_B.weight'].detach().to(device='cpu', dtype=torch.float32)
            if (a.ndim != 2 or b.ndim != 2 or a.shape[0] != config['r']
                    or b.shape[1] != config['r'] or not torch.isfinite(a).all()
                    or not torch.isfinite(b).all()):
                raise ValueError('invalid, nonfinite or rank-inconsistent projection')
            scaled = b * (weight * config['lora_alpha'] / config['r'])
            if not torch.isfinite(scaled).all():
                raise ValueError('weighted update is nonfinite')
            factors.append((a, scaled))
        if factors[0][0].shape[1] != factors[1][0].shape[1] or factors[0][1].shape[0] != factors[1][1].shape[0]:
            raise ValueError('base projection shapes differ')
        result[prefix + '.lora_A.weight'] = torch.cat([v[0] for v in factors], dim=0).contiguous()
        result[prefix + '.lora_B.weight'] = torch.cat([v[1] for v in factors], dim=1).contiguous()
    config = copy.deepcopy(recovery_config)
    config.update(r=rank, lora_alpha=rank, inference_mode=True)
    return result, config


def main():
    from safetensors.torch import load_file, save_file
    import torch
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--ordinary', type=Path, required=True)
    parser.add_argument('--recovery', type=Path, required=True)
    parser.add_argument('--mode', choices=['average', 'residual'], required=True)
    parser.add_argument('--out', type=Path, required=True)
    args = parser.parse_args()
    if args.out.exists():
        raise FileExistsError('preserve existing adapter output')
    sources = []
    bindings = {}
    for name, directory in [('ordinary', args.ordinary), ('recovery', args.recovery)]:
        for filename in ['adapter_model.safetensors', 'adapter_config.json']:
            p = directory / filename
            bindings[name + '/' + filename] = dict(path=str(p.resolve()),
                sha256=hashlib.sha256(p.read_bytes()).hexdigest())
        sources.append((load_file(str(directory / 'adapter_model.safetensors'), device='cpu'),
            json.loads((directory / 'adapter_config.json').read_text())))
    weights = (.5, .5) if args.mode == 'average' else (-1., 1.)
    tensors, config = compose(sources[0][0], sources[1][0], sources[0][1], sources[1][1], weights)
    # Compare actual linear maps, rather than merely inspecting factor shapes.
    generator = torch.Generator().manual_seed(17)
    max_error = 0.
    for name, a in tensors.items():
        if not name.endswith('.lora_A.weight'):
            continue
        bname = name.replace('.lora_A.weight', '.lora_B.weight')
        x = torch.randn(a.shape[1], 3, generator=generator, dtype=torch.float64)
        actual = tensors[bname].double() @ (a.double() @ x)
        expected = sum(w * c['lora_alpha'] / c['r'] *
            (s[bname].double() @ (s[name].double() @ x))
            for (s, c), w in zip(sources, weights))
        error = (actual - expected).abs().max().item()
        max_error = max(max_error, error)
        if not torch.allclose(actual, expected, atol=1e-7, rtol=1e-5):
            raise ValueError('composed effective update differs')
    args.out.mkdir(parents=True)
    save_file(tensors, str(args.out / 'adapter_model.safetensors'))
    (args.out / 'adapter_config.json').write_text(json.dumps(config, indent=2) + '\n')
    report = dict(mode=args.mode, weights=weights, source_bindings=bindings,
        rank=config['r'], alpha=config['lora_alpha'], effective_scale=1,
        tensors=len(tensors), max_probe_error=max_error, probe_vectors_per_projection=3,
        model_loads=0, generation=0, optimizer_updates=0,
        scope='Exact parameter control; neither causal isolation of feedback nor demonstrated task benefit.')
    (args.out / 'COMPOSITION.json').write_text(json.dumps(report, indent=2) + '\n')
    print(json.dumps(report))


if __name__ == '__main__':
    main()
