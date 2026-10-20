# -*- coding: utf-8 -*-
'''TQ-5 finalize: MANIFEST.json + tq5_material_pins_lf_v1.json (self-excluded; runs content / pycache / derived pins excluded).'''
import hashlib
import json
from datetime import datetime, timezone
from pathlib import Path

Q = Path(__file__).resolve().parent
RUNS = Q / 'runs'
LF_SELF = Q / 'execution_v1' / 'tq5_material_pins_lf_v1.json'


def sha(p):
    return hashlib.sha256(Path(p).read_bytes()).hexdigest()


def write_json(p, obj):
    Path(p).write_text(json.dumps(obj, ensure_ascii=False, indent=2) + chr(10), encoding='utf-8')


def skip(p):
    if p.name == 'MANIFEST.json':
        return True
    if '__pycache__' in p.parts or p.suffix == '.pyc':
        return True
    if RUNS in p.parents and p.name != '.gitignore':
        return True
    if p == LF_SELF:
        return True
    return False


files = []
for p in sorted(Q.rglob('*')):
    if p.is_file() and not skip(p):
        files.append({'path': p.relative_to(Q).as_posix(), 'sha256': sha(p), 'bytes': p.stat().st_size})
manifest = {'schema': 'tq5_package_manifest_v1',
            'generated_utc': datetime.now(timezone.utc).strftime('%Y-%m-%dT%H:%M:%SZ'),
            'status': 'PREPARED_AWAITING_RUN (S4)',
            'counts': {'files': len(files)},
            'files': files, 'manifest_self_excluded': True}
write_json(Q / 'MANIFEST.json', manifest)

CRLF = bytes([13, 10])
LF = bytes([10])
lf = {}
for f in files:
    b = (Q / f['path']).read_bytes()
    lf[f['path']] = hashlib.sha256(b.replace(CRLF, LF)).hexdigest()
write_json(LF_SELF, {'schema': 'tq5_material_pins_lf_v1',
                     'note': 'sha256 of LF-normalised bytes for the TQ-5 package files; derived from files that passed the frozen raw pins.',
                     'source_manifest_sha256': sha(Q / 'MANIFEST.json'), 'files': lf})
print(json.dumps({'files': len(files), 'lf_pins': len(lf)}, ensure_ascii=True))
