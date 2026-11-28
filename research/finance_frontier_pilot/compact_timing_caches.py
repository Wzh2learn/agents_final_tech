"""Deduplicate npm package blobs in accepted, closed GB10 timing shards."""

import argparse
import fcntl
import json
import re
import subprocess
from pathlib import Path


def read_json(path):
    return json.loads(path.read_bytes())


def accepted_shard(shard, progress):
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


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('shard', type=Path)
    parser.add_argument('--apply', action='store_true', help='replace duplicate package blobs with hard links')
    args = parser.parse_args()
    shard = args.shard.absolute()
    if (shard != shard.resolve() or shard.parent.name != 'shards'
            or not re.fullmatch(r'\d{5}', shard.name)):
        parser.error('expected the absolute path of a numbered timing shard')
    namespace = shard.parent.parent
    with (namespace / '.joint-timing.lock').open('rb') as lock:
        try:
            fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
        except BlockingIOError:
            parser.exit(2, f'{namespace} has an active timing writer\n')
        accepted_shard(shard, read_json(namespace / 'progress.json'))
        locations = [*shard.glob('calls/*/*/*/solve/.npm/_cacache/content-v2'),
                     *shard.glob('actors/slot-*/*/.npm/_cacache/content-v2')]
        caches = sorted(path for path in locations if path.is_dir() and path.resolve() == path)
        if len(caches) < 2:
            parser.exit(message='No duplicate cache stores to compare\n')
        flags = ['--ignore-time', '--respect-name', '--respect-xattrs', '--method', 'memcmp', '--reflink=never']
        if not args.apply:
            flags.append('--dry-run')
        subprocess.run(['hardlink', *flags, *map(str, caches)], check=True)


if __name__ == '__main__':
    main()
