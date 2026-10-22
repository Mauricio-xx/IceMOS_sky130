#!/usr/bin/env python3
"""Check a public revision or revision range for unexpected release artifacts.

Optional private pattern files stay outside this repository. Patterns use Python
regular expressions, one per line. Diagnostics report paths, never matched text.
"""

import argparse
from pathlib import PurePosixPath, Path
import re
import subprocess
import sys


def git(*args):
    return subprocess.check_output(['git', *args])


def check_paths(entries, patterns):
    failures = []
    for name, data in entries:
        path = PurePosixPath(name)
        reasons = []
        if any(part in {'myenv', '.venv', '__pycache__', '.idea', '.ipynb_checkpoints'} for part in path.parts):
            reasons.append('generated environment or cache')
        if path.suffix.lower() in {'.zip', '.gz', '.tar', '.ipynb', '.pyc', '.so'}:
            reasons.append('unexpected packaged or generated artifact')
        if b'\0' in data:
            reasons.append('binary artifact requires separate review')
        text = data.decode('utf-8', errors='replace')
        if any(pattern.search(text) or pattern.search(name) for pattern in patterns):
            reasons.append('external content policy match')
        if path.suffix.lower() in {'.lib', '.spice', '.pm3', '.scs'}:
            for match in re.finditer(r'^\s*(?:\.model|model)\s+(\S+)', text, re.I | re.M):
                if not match[1].lower().startswith('sky130_'):
                    reasons.append('model outside the SKY130 namespace')
                    break
        if reasons:
            failures.append(f'{name}: {", ".join(reasons)}')
    return failures


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--base', help='Inspect every added/modified blob in base..HEAD')
    parser.add_argument('--deny-pattern-file', type=Path, help='External private content policy')
    args = parser.parse_args(argv)
    patterns = []
    if args.deny_pattern_file:
        patterns = [re.compile(line, re.I) for line in args.deny_pattern_file.read_text().splitlines()
                    if line and not line.startswith('#')]
    revisions = git('rev-list', '--reverse', f'{args.base}..HEAD').decode().splitlines() if args.base else ['HEAD']
    failures, scanned = [], set()
    for revision in revisions:
        paths = (git('diff-tree', '--no-commit-id', '--name-only', '-r', '-m', '--no-renames', '-z', '--diff-filter=AM', revision)
                 if args.base else git('ls-tree', '-r', '--name-only', '-z', revision))
        for raw in paths.split(b'\0'):
            if not raw:
                continue
            name = raw.decode()
            oid = git('rev-parse', f'{revision}:{name}').strip()
            key = (name, oid)
            if key in scanned:
                continue
            scanned.add(key)
            failures.extend(check_paths([(name, git('cat-file', 'blob', oid.decode()))], patterns))
    for failure in failures:
        print(failure, file=sys.stderr)
    print(f'Checked {len(scanned)} file versions across {len(revisions)} revision(s); {len(failures)} policy findings.')
    return bool(failures)


if __name__ == '__main__':
    raise SystemExit(main())
