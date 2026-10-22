"""Spectre process wrapper and a strict reader for scalar DC PSF ASCII data."""

import csv
import math
import os
from pathlib import Path
import re
import subprocess
import tempfile

from IceMOS_sky130_model_io import NUMBER, numeric_value
from IceMOS_sky130_simulation import SimulationCurve
from IceMOS_sky130_spectre_netlist_generator import SpectreNetlistGeneratorSky130


def read_psf_dc(path, signal='VMEAS:p'):
    """Read VALUE samples using the declared sweep; never consume header values."""
    section = None
    sweep_names, rows = [], []
    row = None
    finished = False
    sweep_depth = 0
    record = re.compile(r'"([^"\\]+)"\s+(' + NUMBER + r')\s*$')
    for raw in Path(path).read_text().splitlines():
        line = raw.strip()
        if line in ('HEADER', 'TYPE', 'SWEEP', 'TRACE', 'VALUE', 'END'):
            section = line
            if line == 'END':
                finished = True
                break
            continue
        if section == 'SWEEP':
            match = re.match(r'^"([^"\\]+)"\s+"', line)
            if match and sweep_depth == 0:
                sweep_names.append(match[1])
            unquoted = re.sub(r'"[^"]*"', '', line)
            sweep_depth += unquoted.count('(') - unquoted.count(')')
        elif section == 'VALUE' and line:
            if len(sweep_names) != 1:
                raise ValueError('Expected a scalar DC PSF file with one sweep variable')
            match = record.fullmatch(line)
            if match is None:
                raise ValueError('Unsupported or malformed scalar PSF sample')
            name, value = match[1], float(numeric_value(match[2]))
            if name == sweep_names[0]:
                if row is not None:
                    rows.append(row)
                row = {name: value}
            elif row is None or name in row:
                raise ValueError('PSF trace is duplicated or has no sweep point')
            else:
                row[name] = value
    if row is not None:
        rows.append(row)
    if not finished or not rows or any(signal not in item for item in rows):
        raise ValueError(f'Incomplete DC PSF data or missing signal {signal}')
    return SimulationCurve([item[sweep_names[0]] for item in rows],
                           [item[signal] for item in rows], 'Spectre')


class SpectreSimulatorSky130:
    name = 'spectre'

    def __init__(self, original_model_file, *, executable=None, timeout=120):
        self.generator = SpectreNetlistGeneratorSky130(original_model_file)
        self.executable = os.fspath(executable or os.environ.get('SPECTRE_BIN') or 'spectre')
        candidate = Path(self.executable).expanduser()
        if '/' in self.executable or candidate.is_file():
            self.executable = str(candidate.resolve())
        if not math.isfinite(timeout) or timeout <= 0:
            raise ValueError('Simulation timeout must be positive and finite')
        self.timeout = timeout
        self._results = {}

    def _run_job(self, job):
        netlist = job.netlist.resolve()
        run_dir = Path(tempfile.mkdtemp(prefix=netlist.stem + '_', dir=netlist.parent))
        raw_dir = run_dir / 'psf'
        raw_dir.mkdir()
        log = run_dir / 'spectre.log'
        command = [self.executable, str(netlist), '+escchars', '-format', 'psfascii',
                   '-raw', str(raw_dir), '+log', str(log)]
        try:
            process = subprocess.run(command, cwd=netlist.parent, capture_output=True,
                                     text=True, timeout=self.timeout, check=False)
        except FileNotFoundError as error:
            raise RuntimeError('Spectre executable not found; set SPECTRE_BIN or configure its path') from error
        except subprocess.TimeoutExpired as error:
            raise RuntimeError(f'Spectre exceeded the {self.timeout:g} second timeout; see {run_dir}') from error
        log_text = log.read_text(errors='replace') if log.exists() else ''
        diagnostics = process.stdout + process.stderr + log_text
        if process.returncode or re.search(r'(?im)^\s*(?:ERROR|FATAL)\s*(?:\(|:)', diagnostics):
            raise RuntimeError(f'Spectre failed; see {log}\n' + diagnostics)
        result = raw_dir / 'icemos_dc.dc'
        if not result.exists():
            raise RuntimeError(f'Spectre produced no DC result; see {log}')
        curve = read_psf_dc(result)
        if len(curve.x) != len(job.expected_x) or any(
                not math.isclose(a, b, rel_tol=1e-8, abs_tol=1e-10)
                for a, b in zip(curve.x, job.expected_x)):
            raise ValueError('Spectre sweep is incomplete or differs from the requested sweep')
        # Keep an ordinary two-column CSV alongside native results for external use.
        with (run_dir / 'curve.csv').open('w', newline='') as stream:
            writer = csv.writer(stream)
            writer.writerow(['voltage', 'current'])
            writer.writerows(zip(curve.x, curve.y))
        return curve, process.stdout

    def _simulate(self, device_type, analysis, **kwargs):
        device = device_type.lower()
        key = (device, analysis)
        self._results.pop(key, None)
        jobs = self.generator.generate(device, analysis=analysis, **kwargs)
        curves, output = [], []
        for job in jobs:
            curve, stdout = self._run_job(job)
            bias = 'VGS' if device == 'nch' else 'VSG'
            curve.label = f'Spectre ({analysis})' if job.gate_bias is None else f'{bias}={job.gate_bias:g} V (Spectre)'
            curves.append(curve)
            output.append(stdout)
        self._results[key] = (kwargs.get('bin_number'), curves)
        return '\n'.join(output)

    def simulate_iv(self, device_type, bin_number=None, W=None, L=None,
                    vgate_start=0, vgate_stop=1.8, vgate_step=0.1, model_type='modified'):
        return self._simulate(device_type, 'iv', bin_number=bin_number, W=W, L=L,
                              gate_start=vgate_start, gate_stop=vgate_stop, gate_step=vgate_step,
                              variant=model_type)

    def simulate_id_vs_vds_sweep_vg(self, device_type, bin_number=None, W=None, L=None,
                                   vgs_start=0, vgs_stop=1.8, vgs_step=0.6,
                                   vds_start=0, vds_stop=1.8, vds_step=0.1, model_type='modified'):
        if device_type.lower() != 'nch':
            raise ValueError('Use the VSD method for PMOS')
        return self._simulate(device_type, 'output', bin_number=bin_number, W=W, L=L,
                              gate_start=vgs_start, gate_stop=vgs_stop, gate_step=vgs_step,
                              drain_start=vds_start, drain_stop=vds_stop, drain_step=vds_step,
                              variant=model_type)

    def simulate_is_vs_vsd_sweep_vg(self, device_type, bin_number=None, W=None, L=None,
                                   vsg_start=0, vsg_stop=1.8, vsg_step=0.2,
                                   vsd_start=0, vsd_stop=1.8, vsd_step=0.1, model_type='modified'):
        if device_type.lower() != 'pch':
            raise ValueError('Use the VDS method for NMOS')
        return self._simulate(device_type, 'output', bin_number=bin_number, W=W, L=L,
                              gate_start=vsg_start, gate_stop=vsg_stop, gate_step=vsg_step,
                              drain_start=vsd_start, drain_stop=vsd_stop, drain_step=vsd_step,
                              variant=model_type)

    def _curves(self, device_type, bin_number, analysis):
        number, curves = self._results.get((device_type.lower(), analysis), (None, None))
        if curves is None or (number is not None and number != bin_number):
            raise ValueError('No successful Spectre result for this device and analysis')
        return curves

    def read_iv_results(self, device_type, bin_number):
        return self._curves(device_type, bin_number, 'iv')[0]

    def read_output_results(self, device_type, bin_number):
        return self._curves(device_type, bin_number, 'output')
