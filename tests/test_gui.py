"""Exercise GUI connections without a display or private data."""

import os
from pathlib import Path

import pytest

os.environ.setdefault('QT_QPA_PLATFORM', 'offscreen')
pytest.importorskip('PyQt5')
pytest.importorskip('pyqtgraph')
from PyQt5 import QtWidgets


def test_apply_simulate_reuses_window_and_applies_current_values(tmp_path, monkeypatch):
    from icemos.calibrator import MainWindow
    from icemos.circuit_model_extractor import ModelExtractor
    root = Path(__file__).resolve().parents[1]
    monkeypatch.chdir(tmp_path)
    source = root / 'pdk_original_models/sky130_fd_pr__nfet_01v8.pm3.spice'
    ModelExtractor(source).extract_bin_parameters(40)
    app = QtWidgets.QApplication.instance() or QtWidgets.QApplication([])
    window = MainWindow('nch', 40, original_model_file=source)
    window.current_parameters['vth0'] = {'value': 0.75, 'min': 0, 'max': 1}
    simulation = window.open_simulation_window()
    assert window.open_simulation_window() is simulation
    calls = []
    monkeypatch.setattr(simulation, '_run_simulation', lambda: calls.append(True))
    window.run_calibration()
    assert calls == [True]
    modified = Path('circuits/nch/bin_40/bin_40_nch_modified.lib').read_text()
    assert 'vth0 = 0.75' in modified
    simulation.timer.stop()
    simulation.close()
    window.close()
    app.processEvents()


def test_parameter_ranges_slider_reset_and_invalid_session(tmp_path, monkeypatch):
    from icemos.calibrator import ParameterTunerWindow
    app = QtWidgets.QApplication.instance() or QtWidgets.QApplication([])
    monkeypatch.setattr(QtWidgets.QMessageBox, 'information', lambda *args: None)
    warnings = []
    monkeypatch.setattr(QtWidgets.QMessageBox, 'warning', lambda *args: warnings.append(args[-1]))
    params = {'vth0': {'value': 0.5, 'min': 0.25, 'max': 0.75}}
    tuner = ParameterTunerWindow(params, {'vth0': 0.5}, {'vth0': 0.5})
    slider, spin, min_edit, max_edit, manual, set_min, set_max, _ = tuner.controls['vth0']
    min_edit.setValue(0)
    set_min.click()
    max_edit.setValue(2)
    set_max.click()
    assert params['vth0']['min'] == 0 and params['vth0']['max'] == 2
    slider.setValue(slider.maximum())
    assert params['vth0']['value'] == pytest.approx(2)
    assert spin.value() == pytest.approx(2)
    tuner.reset_selected()
    assert params['vth0']['value'] == pytest.approx(0.5)
    tuner.update_parameter_from_text('vth0', 'nan')
    assert params['vth0']['value'] == pytest.approx(0.5)
    assert warnings
    malformed = tmp_path / 'invalid.json'
    malformed.write_text('{"unknown": 1}')
    monkeypatch.setattr(QtWidgets.QFileDialog, 'getOpenFileName', lambda *args: (str(malformed), ''))
    tuner.load_calibration()
    assert list(params) == ['vth0']
    tuner.close()
    app.processEvents()


@pytest.mark.skipif(__import__('shutil').which('ngspice') is None, reason='ngspice is not installed')
@pytest.mark.parametrize('device,basename,number', [('nch', 'nfet', 40), ('pch', 'pfet', 1)])
def test_gui_runs_real_simulation_and_updates_both_plots(tmp_path, monkeypatch, device, basename, number):
    from icemos.calibrator import MainWindow
    from icemos.circuit_model_extractor import ModelExtractor
    app = QtWidgets.QApplication.instance() or QtWidgets.QApplication([])
    monkeypatch.chdir(tmp_path)
    warnings = []
    monkeypatch.setattr(QtWidgets.QMessageBox, 'warning', lambda *args: warnings.append(args[-1]))
    source = Path(__file__).resolve().parents[1] / 'pdk_original_models' / f'sky130_fd_pr__{basename}_01v8.pm3.spice'
    ModelExtractor(source, device).extract_bin_parameters(number)
    window = MainWindow(device, number, original_model_file=source)
    simulation = window.open_simulation_window()
    simulation.vgStepEdit.setText('0.9')
    simulation.vdsStepEdit.setText('0.3')
    window.run_calibration()
    assert not warnings
    assert simulation.plotWin_IV_vs_VG.isVisible()
    simulation.simTypeCombo.setCurrentText('IV vs VDS')
    window.run_calibration()
    assert not warnings
    assert simulation.plotWin_IV_vs_VDS.isVisible()
    simulation.plotWin_IV_vs_VG.close()
    simulation.plotWin_IV_vs_VDS.close()
    simulation.close()
    window.close()
    app.processEvents()


def test_reopened_calibration_recovers_deltas_and_removal_restores_source(tmp_path, monkeypatch):
    from icemos.calibrator import MainWindow
    from icemos.circuit_model_extractor import ModelExtractor
    app = QtWidgets.QApplication.instance() or QtWidgets.QApplication([])
    monkeypatch.chdir(tmp_path)
    source = Path(__file__).resolve().parents[1] / 'pdk_original_models/sky130_fd_pr__nfet_01v8.pm3.spice'
    extractor = ModelExtractor(source)
    extractor.extract_bin_parameters(40)
    window = MainWindow('nch', 40)
    window.current_parameters['vth0'] = {'value': 0.75}
    assert window.update_modified_lib(notify=False)
    window.close()
    # Extraction on a second launch retains the existing modified model.
    extractor.extract_bin_parameters(40)
    reopened = MainWindow('nch', 40)
    assert reopened.current_parameters['vth0']['value'] == pytest.approx(0.75)
    assert reopened.update_modified_lib(notify=False)
    reopened.current_parameters.clear()
    assert reopened.update_modified_lib(notify=False)
    folder = Path('circuits/nch/bin_40')
    assert (folder / 'bin_40_nch_modified.lib').read_text() == (folder / 'bin_40_nch_original.lib').read_text()
    reopened.close()
    app.processEvents()


def test_spectre_backend_gui_uses_native_results_and_switches_cleanly(tmp_path, monkeypatch, fake_spectre):
    from icemos.calibrator import MainWindow
    from icemos.circuit_model_extractor import ModelExtractor
    app = QtWidgets.QApplication.instance() or QtWidgets.QApplication([])
    monkeypatch.chdir(tmp_path)
    warnings = []
    monkeypatch.setattr(QtWidgets.QMessageBox, 'warning', lambda *args: warnings.append(args[-1]))
    source = Path(__file__).resolve().parents[1] / 'pdk_original_models/sky130_fd_pr__nfet_01v8.pm3.spice'
    ModelExtractor(source).extract_bin_parameters(40)
    window = MainWindow('nch', 40, backend='spectre', spectre_executable=fake_spectre)
    simulation = window.open_simulation_window()
    assert simulation.backendCombo.currentText() == 'spectre'
    simulation.vgStepEdit.setText('0.9')
    simulation.vdsStepEdit.setText('0.3')
    window.current_parameters['vth0'] = {'value': 0.75}
    window.run_calibration()
    assert not warnings
    assert 'spectre' in simulation.plotWin_IV_vs_VG.windowTitle()
    assert simulation.simulator.read_iv_results('nch', 40).x == [0, 0.9, 1.8]
    simulation.simTypeCombo.setCurrentText('IV vs VDS')
    simulation.variantCombo.setCurrentText('original')
    window.run_calibration()
    assert not warnings and simulation.plotWin_IV_vs_VDS.isVisible()
    assert 'original' in simulation.plotWin_IV_vs_VDS.windowTitle()
    assert len(simulation.simulator.read_output_results('nch', 40)) == 3
    assert not Path('circuits/nch/bin_40/results_IV_ID_vs_VG').exists()
    simulation.timer.start(5000)
    simulation.backendCombo.setCurrentText('ngspice')
    assert not simulation.timer.isActive()
    assert simulation.simulator.name == 'ngspice'
    simulation.backendCombo.setCurrentText('spectre')
    monkeypatch.setenv('FAKE_SPECTRE_MODE', 'missing')
    simulation.timer.start(5000)
    window.run_calibration()
    assert not simulation.timer.isActive()
    assert warnings and 'produced no DC result' in warnings[-1]
    simulation.plotWin_IV_vs_VG.close()
    simulation.plotWin_IV_vs_VDS.close()
    simulation.close()
    window.close()
    app.processEvents()
