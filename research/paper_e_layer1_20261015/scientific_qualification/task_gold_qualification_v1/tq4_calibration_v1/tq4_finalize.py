# -*- coding: utf-8 -*-
'''TQ-4 finalize: build PANEL_V2_MANIFEST.json and root MANIFEST.json (self-excluded; no pycache / runs content).'''
import hashlib
import json
from datetime import datetime, timezone
from pathlib import Path

Q = Path(__file__).resolve().parent             # tq4_calibration_v1
TQ3 = Q.parent / 'tq3_execution_prep_v1'
RUNS = Q / 'runs'


def sha(p):
    return hashlib.sha256(Path(p).read_bytes()).hexdigest()


def write_json(p, obj):
    Path(p).write_text(json.dumps(obj, ensure_ascii=False, indent=2) + chr(10), encoding='utf-8')


def collect(root, name_exclude, extra_skip=None):
    files = []
    for p in sorted(root.rglob('*')):
        if not p.is_file():
            continue
        if p.name == name_exclude:
            continue
        if '__pycache__' in p.parts or p.suffix == '.pyc':
            continue
        if extra_skip and extra_skip(p):
            continue
        files.append({'path': p.relative_to(root).as_posix(), 'sha256': sha(p), 'bytes': p.stat().st_size})
    return files


def main():
    panel = Q / 'panel_v2'
    panel_files = collect(panel, 'PANEL_V2_MANIFEST.json')
    natural = [f for f in panel_files if f['path'].startswith('natural/')]
    cands = [f for f in panel_files if f['path'].startswith('candidates/')]
    panel_manifest = {'schema': 'tq4_panel_v2_manifest_v1',
                      'generated_utc': datetime.now(timezone.utc).strftime('%Y-%m-%dT%H:%M:%SZ'),
                      'counts': {'natural_files': len(natural), 'candidate_files': len(cands), 'total': len(panel_files)},
                      'files': panel_files, 'self_excluded': True}
    write_json(panel / 'PANEL_V2_MANIFEST.json', panel_manifest)

    def skip_runs(p):
        return RUNS in p.parents and p.name != '.gitignore'

    root_files = collect(Q, 'MANIFEST.json', extra_skip=skip_runs)
    manifest = {'schema': 'tq4_package_manifest_v1',
                'generated_utc': datetime.now(timezone.utc).strftime('%Y-%m-%dT%H:%M:%SZ'),
                'status': 'PREPARED_AWAITING_AUTHORIZATION_V2',
                'model_calls_this_round': 0,
                'inputs': {'tq3_material_manifest': {'path': '../tq3_execution_prep_v1/MANIFEST.json',
                                                     'sha256': sha(TQ3 / 'MANIFEST.json')}},
                'counts': {'files': len(root_files), 'panel_v2_files': len(panel_files)},
                'files': root_files, 'manifest_self_excluded': True}
    write_json(Q / 'MANIFEST.json', manifest)
    print(json.dumps({'panel_files': len(panel_files), 'root_files': len(root_files)}, ensure_ascii=True))


if __name__ == '__main__':
    main()
