"""Synthetic simulator executable; deliberately does not emulate device physics."""

from pathlib import Path
import sys

import pytest


@pytest.fixture
def fake_spectre(tmp_path):
    executable = tmp_path / 'fake spectre executable'
    executable.write_text(f'#!{sys.executable}\n' + r'''
import json, os, re, sys
from pathlib import Path
args = sys.argv[1:]
netlist = Path(args[0])
raw = Path(args[args.index('-raw') + 1])
log = Path(args[args.index('+log') + 1])
mode = os.environ.get('FAKE_SPECTRE_MODE', '')
(raw.parent / 'invocation.json').write_text(json.dumps({
    'args': args, 'cwd': os.getcwd(), 'license': os.environ.get('LM_LICENSE_FILE')}))
if mode == 'fail':
    log.write_text('ERROR (TEST-1): synthetic failure\n')
    sys.exit(1)
if mode == 'logfailure':
    log.write_text('FATAL (TEST-2): synthetic failure\n')
    sys.exit(0)
log.write_text('Synthetic test executable; no physical simulation\n')
if mode == 'missing':
    sys.exit(0)
text = netlist.read_text()
match = re.search(r'icemos_dc dc dev=(\w+) param=dc start=(\S+) stop=(\S+) step=(\S+)', text)
start, stop, step = map(float, match.groups()[1:])
gate = float(re.search(r'^VGATE .* dc=(\S+)', text, re.M)[1])
rows = [
 'HEADER', '"source" "synthetic test"', 'TYPE', '"real" FLOAT DOUBLE',
 'SWEEP', '"dc" "real" PROP(', '"units" "V"', ')', 'TRACE',
 '"VMEAS:p" "real"', 'VALUE']
index = 0
while start + index * step <= stop + 1e-10:
    value = start + index * step
    current = value * (gate + 1) * 1e-6
    rows.extend([f'"dc" {value:.17g}', f'"VMEAS:p" {current:.17g}'])
    index += 1
    if mode == 'incomplete':
        break
if mode != 'truncated':
    rows.append('END')
(raw / 'icemos_dc.dc').write_text('\n'.join(rows) + '\n')
''')
    executable.chmod(0o755)
    return executable
