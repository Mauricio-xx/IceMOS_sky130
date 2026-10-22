"""Synthetic regression cases and smoke tests using the bundled public models."""

from pathlib import Path
import shutil

import pytest

from IceMOS_sky130_mdm_parser import MDMParser, read_mdm
from IceMOS_sky130_model_io import model_blocks, parameters, patch_bin
from IceMOS_sky130_param_handler import ModelModifier
from IceMOS_sky130_pdk_exporter import export_calibrated_model

ROOT = Path(__file__).resolve().parents[1]
MODEL = '''* Synthetic fixture; values are arbitrary, not a calibrated device.
.model sky130_fd_pr__nfet_01v8__model.1 nmos
+ vth0 = {0.5 + offset} u0=0.1 $ keep this comment
.model sky130_fd_pr__nfet_01v8__model.10 nmos
+ vth0=0.8 u0=0.2
.model unrelated nmos
+ vth0=0.9
'''
MDM = '''BEGIN_HEADER
Synthetic measurement data
END_HEADER
BEGIN_DB
ICCAP_VAR VG 0.5
ICCAP_VAR VB 0
# VD ID
0 0
1 0.000001
END_DB
BEGIN_DB
ICCAP_VAR VG 0.5
ICCAP_VAR VB 1
# VD ID
0 0
1 0.000002
END_DB
'''


def test_exact_bin_and_expression_preservation(tmp_path):
    source = tmp_path / 'source.spice'
    output = tmp_path / 'modified.spice'
    source.write_text(MODEL)
    modifier = ModelModifier(source, output)
    modifier.modify_parameters(1, {'VTH0': 0.75})
    assert output.read_text() == MODEL.replace('{0.5 + offset}', '{0.75 + offset}')
    modifier.modify_parameter(10, 'u0', 0.25)
    assert 'vth0=0.8 u0=0.25' in output.read_text()
    assert source.read_text() == MODEL
    before = output.read_bytes()
    with pytest.raises(ValueError, match='Unknown parameters'):
        modifier.modify_parameters(1, {'vth0': 0.6, 'missing': 0})
    assert output.read_bytes() == before


@pytest.mark.parametrize('value', [float('nan'), float('inf'), True, '0.5 extra'])
def test_invalid_values_cannot_change_model(value):
    with pytest.raises(ValueError):
        patch_bin(MODEL, 'nch', 1, {'vth0': value})


def test_export_multi_bin_and_atomic_validation(tmp_path):
    source, output = tmp_path / 'source.spice', tmp_path / 'export.spice'
    source.write_text(MODEL)
    export_calibrated_model(source, output, 'nch', {1: {'vth0': {'value': 0.75}}, 10: {'u0': 0.25}})
    assert output.read_text() == MODEL.replace('{0.5 + offset}', '{0.75 + offset}').replace('u0=0.2', 'u0=0.25')
    before = output.read_bytes()
    with pytest.raises(ValueError):
        export_calibrated_model(source, output, 'nch', {1: {'vth0': 0.6}, 99: {'u0': 0.3}})
    assert output.read_bytes() == before
    with pytest.raises(ValueError):
        export_calibrated_model(source, source, 'nch', {1: {'u0': 0.3}})


@pytest.mark.parametrize('device,basename', [('nch', 'nfet'), ('pch', 'pfet')])
def test_export_bundled_model_changes_only_selected_parameter(tmp_path, device, basename):
    source = ROOT / 'pdk_original_models' / f'sky130_fd_pr__{basename}_01v8.pm3.spice'
    original = source.read_text()
    blocks = model_blocks(original, device)
    start, end = blocks[1]
    original_value = parameters(original[start:end])['vth0']
    output = tmp_path / 'export.spice'
    export_calibrated_model(source, output, device, {1: {'vth0': 0.75}})
    updated = output.read_text()
    assert updated[:start] == original[:start]
    assert updated.endswith(original[end:])
    assert original_value != parameters(updated[start:model_blocks(updated, device)[1][1]])['vth0']
    assert source.read_text() == original


def test_mdm_preserves_all_blocks_and_repeated_gate_bias(tmp_path):
    source = tmp_path / 'synthetic.mdm'
    source.write_text(MDM)
    parser = MDMParser(tmp_path, source.name, ['VG', 'VB'])
    paths, sweeps = parser.export_csv(tmp_path / 'csv')
    assert len(set(paths)) == 2
    assert sweeps == [{'VG': 0.5, 'VB': 0}, {'VG': 0.5, 'VB': 1}]
    assert '2e-06' in Path(paths[1]).read_text()
    with pytest.raises(ValueError, match='Multiple blocks'):
        parser.process_mdm_file_for_IV()
    legacy_paths, gates = parser.process_mdm_file_for_IV_VGsweep(0)
    assert len(set(legacy_paths)) == 2 and gates == [0.5, 0.5]


@pytest.mark.parametrize('text', [MDM.replace('1 0.000001', '1'), MDM[:-7], 'nothing', MDM.replace('0.000001', 'nan')])
def test_malformed_mdm_rejected(tmp_path, text):
    source = tmp_path / 'synthetic.mdm'
    source.write_text(text)
    with pytest.raises(ValueError):
        read_mdm(source)


def test_cli_import_and_export(tmp_path, capsys):
    from IceMOS_sky130_cli import main
    mdm = tmp_path / 'synthetic.mdm'
    mdm.write_text(MDM)
    assert main(['mdm', str(mdm), '--output', str(tmp_path / 'csv')]) == 0
    assert len(list((tmp_path / 'csv').glob('*.csv'))) == 2
    source = tmp_path / 'model.spice'
    source.write_text(MODEL)
    calibration = tmp_path / 'session.json'
    calibration.write_text('{"vth0": {"value": 0.75, "min": 0, "max": 1}}')
    output = tmp_path / 'out.spice'
    assert main(['export', str(source), str(calibration), '--device', 'nch', '--bin', '1', '--output', str(output)]) == 0
    assert '{0.75 + offset}' in output.read_text()


@pytest.mark.skipif(shutil.which('ngspice') is None, reason='ngspice is not installed')
@pytest.mark.parametrize('device,basename,number', [('nch', 'nfet', 40), ('pch', 'pfet', 1)])
def test_ngspice_public_model_iv_and_output_sweep(tmp_path, monkeypatch, device, basename, number):
    from IceMOS_sky130_simulator import IceMOS_simulator_sky130
    model = ROOT / 'pdk_original_models' / f'sky130_fd_pr__{basename}_01v8.pm3.spice'
    monkeypatch.chdir(tmp_path)
    simulator = IceMOS_simulator_sky130(str(model))
    simulator.simulate_iv(device, bin_number=number, vgate_step=0.3)
    folder = tmp_path / 'circuits' / device / f'bin_{number}'
    csv = folder / 'results_IV_ID_vs_VG' / 'IV_ID_vs_VG.csv'
    rows = [[float(v) for v in line.split()] for line in csv.read_text().splitlines()]
    assert len(rows) == 7
    assert abs(rows[-1][-1]) > abs(rows[0][-1])
    if device == 'nch':
        simulator.simulate_id_vs_vds_sweep_vg(device, bin_number=number, vgs_step=0.9, vds_step=0.3)
        results = folder / 'results_IV_IDS_vs_VDS_for_VG_sweep'
    else:
        simulator.simulate_is_vs_vsd_sweep_vg(device, bin_number=number, vsg_step=0.9, vsd_step=0.3)
        results = folder / 'results_IV_ISD_vs_VSD_for_VG_sweep'
    assert len(list(results.glob('*.csv'))) == 3
    assert all(len(p.read_text().splitlines()) == 7 for p in results.glob('*.csv'))


def test_zero_or_negative_sweep_rejected_before_simulation():
    from IceMOS_sky130_netlist_generator import NetlistGeneratorSky130
    generator = NetlistGeneratorSky130('unused')
    for step in [0, -0.1, float('nan')]:
        with pytest.raises(ValueError):
            generator.generate_iv_vds_netlists('nch', bin_number=1, vgs_step=step)
