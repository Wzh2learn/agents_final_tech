"""Pinned offline tools for new research episodes; never installs a service."""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
import subprocess
import time

RG = Path('/home/testuser/.cache/opencode/bin/rg')
RG_SHA256 = '968cabe8efed72fd8fd482cb76b6084fcb695fc5293af7fb62296b02f487fb69'
OPENCODE = Path('/home/testuser/.opencode/bin/opencode')


def sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def ripgrep_binding(path: Path = RG) -> list[str]:
    path = Path(path)
    if not path.is_absolute() or path.is_symlink() or not path.is_file():
        raise ValueError('expected an existing regular absolute ripgrep path')
    if ',' in str(path) or '\n' in str(path) or '\r' in str(path):
        raise ValueError('unsafe Docker mount path')
    if sha(path) != RG_SHA256:
        raise ValueError('ripgrep binary hash changed')
    return ['--mount', f'type=bind,src={path},dst=/usr/local/bin/rg,readonly']


def probe(image: str, source: Path, out: Path) -> dict:
    """Paired no-model checks with no endpoint bridge or host HOME mount."""
    binding = ripgrep_binding()
    if not image.startswith('sha256:') or len(image) != 71:
        raise ValueError('an immutable local image ID is required')
    if source.is_symlink() or not source.is_dir():
        raise ValueError('expected source directory')
    out.mkdir(parents=True, exist_ok=False)
    result = {'status': 'IN_PROGRESS', 'model_calls': 0, 'image': image,
              'ripgrep_sha256': sha(RG), 'opencode_sha256': sha(OPENCODE), 'runs': {}}
    for arm, extra in (('missing_rg', []), ('pinned_rg', binding)):
        name = 'research-rg-' + str(time.monotonic_ns()) + '-' + arm
        cmd = ['docker', 'run', '--name', name, '--rm', '--pull', 'never', '--network', 'none', '--read-only',
            '--cpus', '1', '--memory', '1g', '--pids-limit', '128', '--cap-drop', 'ALL',
            '--security-opt', 'no-new-privileges', '--tmpfs', '/tmp:rw,nosuid,size=128m',
            '--tmpfs', '/home/agent:rw,nosuid,size=128m', '-e', 'HOME=/home/agent',
            '-e', 'OPENCODE_DISABLE_MODELS_FETCH=1',
            '--mount', f'type=bind,src={source},dst=/workspace,readonly',
            '--mount', f'type=bind,src={OPENCODE},dst=/opt/opencode,readonly',
            *extra, '--workdir', '/workspace', '--entrypoint', '/opt/opencode', image,
            'debug', 'rg', 'search', 'decode_unicode', '--pure', '--print-logs', '--log-level', 'DEBUG']
        start = time.monotonic()
        try:
            proc = subprocess.run(cmd, capture_output=True, timeout=90)
            code, raw_out, raw_err = proc.returncode, proc.stdout, proc.stderr
        except subprocess.TimeoutExpired as exc:
            subprocess.run(['docker', 'kill', name], capture_output=True, timeout=15)
            code, raw_out, raw_err = 124, exc.stdout or b'', exc.stderr or b''
        stdout, stderr = out / (arm + '.stdout'), out / (arm + '.stderr')
        stdout.write_bytes(raw_out)
        stderr.write_bytes(raw_err)
        result['runs'][arm] = {'exit': code, 'seconds': round(time.monotonic() - start, 3),
            'stdout_sha256': sha(stdout), 'stderr_sha256': sha(stderr),
            'stdout_bytes': len(raw_out), 'stderr_bytes': len(raw_err)}
    good = result['runs']['pinned_rg']
    result['status'] = 'PROBE_COMPLETED'
    result['fixed_search_success'] = good['exit'] == 0 and good['stdout_bytes'] > 0
    (out / 'receipt.json').write_text(json.dumps(result, indent=2) + '\n', encoding='utf8')
    return result


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--image', required=True)
    parser.add_argument('--source', type=Path, required=True)
    parser.add_argument('--out', type=Path, required=True)
    args = parser.parse_args()
    print(json.dumps(probe(args.image, args.source, args.out)))
