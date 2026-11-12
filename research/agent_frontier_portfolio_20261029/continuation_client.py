"""Guest-side execution of one learned controller over the existing world RPC.

No model/API credential is available here. Every action goes through the same
role/turn checks as ordinary OpenCode decisions; private world state is absent.
"""
from __future__ import annotations
import argparse
import json
from pathlib import Path
import socket

from continuation_program import load_program, public_step


def rpc(request):
    s = socket.socket(socket.AF_UNIX)
    s.settimeout(850)
    try:
        s.connect('/world/s')
        s.sendall(json.dumps(request, allow_nan=False).encode()+b'\n')
        parts = []; total = 0
        while True:
            part = s.recv(65536)
            if not part:break
            parts.append(part); total += len(part)
            if total > 2*1024**2:raise ValueError('world response size limit')
            if b'\n' in part:break
        return json.loads(b''.join(parts))
    finally:
        s.close()


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--program', type=Path, required=True)
    parser.add_argument('--memory', type=Path, default=Path('/workspace/program_memory.json'))
    parser.add_argument('--max-actions', type=int, default=32, choices=range(1,49))
    args = parser.parse_args()
    program = load_program(args.program.read_text())
    tools = json.loads(Path('/workspace/tools.json').read_text())
    names = [t['function']['name'] for t in tools]
    current = rpc({'op':'observe'})
    saved = json.loads(args.memory.read_text()) if args.memory.exists() else {'memory':{},'turn':current.get('turn')}
    if not current.get('done') and saved['turn'] != current.get('turn'):
        print(json.dumps({'kind':'yield','reason':'world advanced outside the program; rebind from public feedback','observation':current}))
        return
    trace = args.memory.with_suffix('.trace.jsonl')
    for _ in range(args.max_actions):
        if current.get('done'):
            print(json.dumps({'kind':'stop','observation':current})); return
        try:
            decision = public_step(program,current,saved['memory'],names)
        except Exception as exc:
            print(json.dumps({'kind':'yield','reason':'controller error: '+str(exc),'observation':current}));return
        with trace.open('a') as f:
            f.write(json.dumps({'observation':current,'memory_before':saved['memory'],'decision':decision},allow_nan=False)+'\n')
        saved['memory'] = decision['memory']
        if decision['kind'] != 'act':
            args.memory.write_text(json.dumps(saved,allow_nan=False))
            print(json.dumps({'kind':decision['kind'],'reason':decision.get('reason'),'observation':current}));return
        current = rpc(dict(op='act',turn=current['turn'],name=decision['name'],arguments=decision['arguments']))
        if current.get('error'):
            print(json.dumps({'kind':'yield','reason':'world rejected operation','observation':current}));return
        saved['turn'] = current.get('turn')
        args.memory.write_text(json.dumps(saved,allow_nan=False))
    print(json.dumps({'kind':'yield','reason':'controller action cap','observation':current}))


if __name__ == '__main__':
    main()
