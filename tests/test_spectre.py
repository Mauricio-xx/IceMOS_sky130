"""Test Spectre's tool-specific processing using only public models and synthetic data."""

import csv
import json
import math
import os
from pathlib import Path
import re
import shutil
import subprocess

import pytest

from icemos.model_io import parameters
from icemos.simulation import create_simulator
from icemos.spectre_netlist_generator import SpectreNetlistGenerator
from icemos.spectre_simulator import SpectreSimulator, read_psf_dc

ROOT = Path(__file__).resolve().parents[1]


def public_model(device):
    family = 'nfet' if device == 'nch' else 'pfet'
    return ROOT / 'pdk_original_models' / f'sky130_fd_pr__{family}_01v8.pm3.spice'


@pytest.mark.parametrize('device,number', [('nch', 40), ('pch', 1)])
def test_native_models_use_only_parameters_from_public_bin(tmp_path, monkeypatch, device, number):
    monkeypatch.chdir(tmp_path)
    source = public_model(device)
    before = source.read_bytes()
    generator = SpectreNetlistGenerator(source)
    jobs = generator.generate(device, bin_number=number, gate_step=0.3)
    job = jobs[0]
    original = job.netlist.parent.parent / f'bin_{number}_{device}_modified.lib'
    expected = {key: float(value) for key, value in parameters(original.read_text()).items() if key != 'level'}
    native = (job.netlist.parent / f'bin_{number}_{device}_modified.scs').read_text()
    values = {key: float(value) for key, value in re.findall(r'^\s+(\w+)=(\S+)', native, re.M)}
    assert values == expected
    assert 'Copyright 2020 The SkyWater PDK Authors' in native
    assert f'model sky130_icemos_{device}_bin_{number} bsim4 type={device[0]}' in native
    assert 'level=' not in native
    text = job.netlist.read_text()
    assert '.control' not in text and 'wrdata' not in text
    assert 'options temp=-220' in text
    assert 'save VMEAS:p' in text
    assert ('VGATE (g 0)' if device == 'nch' else 'VGATE (0 g)') in text
    assert ('VMEAS (supply d)' if device == 'nch' else 'VMEAS (d supply)') in text
    assert source.read_bytes() == before
    original_job = generator.generate(device, bin_number=number, variant='original')[0]
    assert 'options temp=27' in original_job.netlist.read_text()


def test_psf_uses_value_section_and_retains_zero_sample(tmp_path):
    path = tmp_path / 'synthetic.dc'
    path.write_text('''HEADER
"dc" 99
TYPE
"real" FLOAT DOUBLE
SWEEP
"dc" "real" PROP(
"units" "V"
)
TRACE
"VMEAS:p" "real"
VALUE
"dc" 0
"VMEAS:p" 0
"dc" 1e-1
"VMEAS:p" 2e-6
END
''')
    curve = read_psf_dc(path)
    assert curve.x == [0, 0.1] and curve.y == [0, 2e-6]
    for bad in [path.read_text().replace('END', ''),
                path.read_text().replace('"VMEAS:p" 2e-6', '"other" 2e-6'),
                path.read_text().replace('2e-6', 'nan'),
                path.read_text().replace('"VMEAS:p" 0', '"VMEAS:p" 0\n"VMEAS:p" 0')]:
        path.write_text(bad)
        with pytest.raises(ValueError):
            read_psf_dc(path)


@pytest.mark.parametrize('device,number', [('nch', 40), ('pch', 1)])
def test_wrapper_iv_output_csv_and_inherited_environment(tmp_path, monkeypatch, fake_spectre, device, number):
    monkeypatch.chdir(tmp_path)
    monkeypatch.setenv('SPECTRE_BIN', str(fake_spectre))
    monkeypatch.setenv('LM_LICENSE_FILE', 'synthetic-license-setting')
    simulator = create_simulator(public_model(device), 'spectre')
    simulator.simulate_iv(device, bin_number=number, vgate_step=0.3)
    curve = simulator.read_iv_results(device, number)
    assert curve.x == pytest.approx([0, 0.3, 0.6, 0.9, 1.2, 1.5, 1.8])
    root = tmp_path / 'circuits' / device / f'bin_{number}' / 'spectre'
    invocation = json.loads(next(root.rglob('invocation.json')).read_text())
    assert invocation['license'] == 'synthetic-license-setting'
    assert invocation['args'][invocation['args'].index('-format') + 1] == 'psfascii'
    assert invocation['cwd'] == str(root)
    with next(root.rglob('curve.csv')).open() as stream:
        rows = list(csv.reader(stream))
    assert rows[0] == ['voltage', 'current'] and len(rows) == 8
    if device == 'nch':
        simulator.simulate_id_vs_vds_sweep_vg(device, bin_number=number, vgs_step=0.9, vds_step=0.3)
    else:
        simulator.simulate_is_vs_vsd_sweep_vg(device, bin_number=number, vsg_step=0.9, vsd_step=0.3)
    curves = simulator.read_output_results(device, number)
    assert len(curves) == 3 and all(len(item.x) == 7 for item in curves)
    assert curves[-1].y[-1] > curves[0].y[-1]
    assert not list((root.parent / 'results_IV_ID_vs_VG').glob('*.csv'))


@pytest.mark.parametrize('mode', ['fail', 'logfailure', 'missing', 'truncated', 'incomplete'])
def test_failed_or_incomplete_run_never_reuses_previous_curves(tmp_path, monkeypatch, fake_spectre, mode):
    monkeypatch.chdir(tmp_path)
    simulator = SpectreSimulator(public_model('nch'), executable=fake_spectre)
    simulator.simulate_iv('nch', bin_number=40, vgate_step=0.9)
    monkeypatch.setenv('FAKE_SPECTRE_MODE', mode)
    with pytest.raises((RuntimeError, ValueError)):
        simulator.simulate_iv('nch', bin_number=40, vgate_step=0.9)
    with pytest.raises(ValueError, match='No successful'):
        simulator.read_iv_results('nch', 40)


def test_missing_executable_and_timeout_are_reported(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    simulator = SpectreSimulator(public_model('nch'), executable=tmp_path / 'missing')
    with pytest.raises(RuntimeError, match='Spectre executable not found'):
        simulator.simulate_iv('nch', bin_number=40)
    def timeout(*args, **kwargs):
        raise subprocess.TimeoutExpired(args[0], 1)
    monkeypatch.setattr(subprocess, 'run', timeout)
    with pytest.raises(RuntimeError, match='timeout|exceeded'):
        simulator.simulate_iv('nch', bin_number=40)


def test_invalid_request_does_not_launch_spectre(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    generator = SpectreNetlistGenerator(public_model('nch'))
    with pytest.raises(ValueError):
        generator.generate('nch', bin_number=40, gate_step=0)
    with pytest.raises(ValueError):
        generator.generate('nch', bin_number=40, W=10, L=10)
    with pytest.raises(ValueError):
        generator.generate('bad', bin_number=40)
    assert not (tmp_path / 'circuits').exists()


def test_cli_spectre_and_model_variant(tmp_path, monkeypatch, fake_spectre):
    from icemos.cli import main
    monkeypatch.chdir(tmp_path)
    output = tmp_path / 'curves.csv'
    assert main(['simulate', str(public_model('pch')), '--backend', 'spectre',
                 '--spectre-bin', str(fake_spectre), '--device', 'pch', '--bin', '1',
                 '--analysis', 'output', '--variant', 'original', '--gate-step', '0.9',
                 '--drain-step', '0.3', '--output', str(output)]) == 0
    with output.open() as stream:
        rows = list(csv.reader(stream))
    assert rows[0] == ['curve', 'voltage', 'current'] and len(rows) == 22
    assert len({row[0] for row in rows[1:]}) == 3
    assert not list(Path('circuits/pch/bin_1/spectre').glob('output_modified*'))


SPECTRE = os.environ.get('SPECTRE_BIN') or shutil.which('spectre')


@pytest.mark.skipif(not SPECTRE, reason='A real Spectre installation and license are not available')
@pytest.mark.parametrize('device,number', [('nch', 40), ('pch', 1)])
def test_real_spectre_public_model_iv_and_output(tmp_path, monkeypatch, device, number):
    monkeypatch.chdir(tmp_path)
    simulator = SpectreSimulator(public_model(device), executable=SPECTRE)
    simulator.simulate_iv(device, bin_number=number, vgate_step=0.3)
    curve = simulator.read_iv_results(device, number)
    assert len(curve.x) == 7 and all(map(math.isfinite, curve.y))
    assert abs(curve.y[-1]) > abs(curve.y[0])
    if device == 'nch':
        simulator.simulate_id_vs_vds_sweep_vg(device, bin_number=number, vgs_step=0.9, vds_step=0.3)
    else:
        simulator.simulate_is_vs_vsd_sweep_vg(device, bin_number=number, vsg_step=0.9, vsd_step=0.3)
    assert len(simulator.read_output_results(device, number)) == 3
