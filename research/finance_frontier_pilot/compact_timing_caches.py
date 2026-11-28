"""Deduplicate npm package blobs in accepted, closed GB10 timing shards."""

import argparse
import fcntl
import json
import re
import subprocess
from pathlib import Path


def read_json(path):
    return json.loads(path.read_bytes())


def accepted_shard(shard, progress, *, run=None):
    if run is None:
        run = read_json(shard / 'run.json')
    collection = read_json(shard / 'collection.json')
    size = len(run['case_order'])
    with (shard / 'outcomes.jsonl').open(encoding='utf-8') as rows:
        outcomes = [(row['id'], row['complete_pair']) for row in map(json.loads, rows)]
    if (run['schema'] != 'finance-live-joint-timing-steady-shard-v1'
            or run['joint_plan_sha256'] != progress['joint_plan_sha256']
            or size <= 0 or run['case_offset'] + size > progress['next_offset']
            or collection['stop_reason'] is not None
            or collection['complete_paired_questions'] != size
            or outcomes != [(case['id'], True) for case in run['case_order']]):
        raise ValueError(f'{shard} is outside the closed, accepted timing prefix')


def compact_shard(shard, apply, *, lock_fd=None):
    locations = [*shard.glob('calls/*/*/*/solve/.npm/_cacache/content-v2'),
                 *shard.glob('actors/slot-*/*/.npm/_cacache/content-v2')]
    caches = sorted(path for path in locations if path.is_dir() and path.resolve() == path)
    if len(caches) < 2:
        return False
    flags = ['--ignore-time', '--respect-name', '--respect-xattrs', '--method', 'memcmp', '--reflink=never']
    if not apply:
        flags.append('--dry-run')
    kwargs = {}
    if lock_fd is not None:
        flags.append('--quiet')
        kwargs['pass_fds'] = (lock_fd,)
    subprocess.run(['hardlink', *flags, *map(str, caches)], check=True, **kwargs)
    return True


def compact_namespace(namespace, progress, apply, lock_fd, from_offset):
    processed, no_stores, skipped, earlier = [], 0, 0, 0
    for shard in sorted((namespace / 'shards').iterdir()):
        if not re.fullmatch(r'\d{5}', shard.name):
            continue
        if shard.is_symlink() or not shard.is_dir():
            skipped += 1
            continue
        try:
            run = read_json(shard / 'run.json')
            if from_offset and run['case_offset'] < from_offset:
                earlier += 1
                continue
            accepted_shard(shard, progress, run=run)
        except (FileNotFoundError, ValueError, KeyError, TypeError):
            skipped += 1
            continue
        if compact_shard(shard, apply, lock_fd=lock_fd):
            processed.append(shard.name)
        else:
            no_stores += 1
    mode = 'Applied' if apply else 'Preview'
    offset_note = f'; {earlier} entries before offset {from_offset} skipped' if from_offset else ''
    print(f'{mode}: {len(processed)} closed shards checked, {no_stores} without multiple stores, '
          f'{skipped} unaccepted skipped; shards: {", ".join(processed) or "none"}{offset_note}')


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('shard', type=Path, nargs='?')
    parser.add_argument('--namespace', type=Path, help='check all closed shards while holding one timing lock')
    parser.add_argument('--from-offset', type=int, help='skip shards starting before this offset in namespace mode (default 0)')
    parser.add_argument('--apply', action='store_true', help='replace duplicate package blobs with hard links')
    args = parser.parse_args()
    if (args.shard is None) == (args.namespace is None):
        parser.error('specify a numbered timing shard or --namespace, not both')
    if args.from_offset is not None and (args.namespace is None or args.from_offset < 0):
        parser.error('--from-offset requires --namespace and a nonnegative value')
    if args.shard is not None:
        shard = args.shard.absolute()
        if (shard != shard.resolve() or shard.parent.name != 'shards'
                or not re.fullmatch(r'\d{5}', shard.name)):
            parser.error('expected the absolute path of a numbered timing shard')
        namespace = shard.parent.parent
    else:
        namespace = args.namespace.absolute()
        shards = namespace / 'shards'
        lock_path = namespace / '.joint-timing.lock'
        if (namespace != namespace.resolve() or shards != shards.resolve() or not shards.is_dir()
                or lock_path.is_symlink() or not lock_path.is_file()):
            parser.error('expected an existing timing namespace with its own shards directory and timing lock')
    with (namespace / '.joint-timing.lock').open('rb') as lock:
        try:
            fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
        except BlockingIOError:
            parser.exit(2, f'{namespace} has an active timing writer\n')
        progress = read_json(namespace / 'progress.json')
        if args.namespace is not None:
            compact_namespace(namespace, progress, args.apply, lock.fileno(), args.from_offset or 0)
        else:
            accepted_shard(shard, progress)
            if not compact_shard(shard, args.apply):
                parser.exit(message='No duplicate cache stores to compare\n')


if __name__ == '__main__':
    main()
