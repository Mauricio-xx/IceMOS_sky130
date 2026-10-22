"""Native Spectre testbenches built solely from extracted public SKY130 bins."""

from dataclasses import dataclass
from pathlib import Path
import re

from IceMOS_sky130_circuit_model_extractor import ModelExtractor
from IceMOS_sky130_model_io import model_blocks, numeric_value, parameters
from IceMOS_sky130_simulation import sweep_values


@dataclass
class SpectreJob:
    netlist: Path
    analysis: str
    gate_bias: float | None
    expected_x: list


class SpectreNetlistGeneratorSky130:
    def __init__(self, original_model_file):
        self.original_model_file = Path(original_model_file)

    def _resolve_bin(self, device_type, bin_number, W, L):
        if device_type not in ('nch', 'pch'):
            raise ValueError('Device must be nch or pch')
        dims = ModelExtractor.nmos_bins if device_type == 'nch' else ModelExtractor.pmos_bins
        if (W is None) != (L is None):
            raise ValueError('Supply both W and L in micrometres')
        if bin_number is None:
            bin_number = next((number for number, size in dims.items()
                               if W is not None and abs(size[0] - W) < 1e-6
                               and abs(size[1] - L) < 1e-6), None)
        if bin_number not in dims:
            raise ValueError('No supported SKY130 bin matches the requested device')
        width, length = dims[bin_number]
        if W is not None and (abs(width - W) >= 1e-6 or abs(length - L) >= 1e-6):
            raise ValueError('Requested dimensions differ from the selected SKY130 bin')
        return bin_number, width, length

    def _native_model(self, device, number, variant, folder):
        source = folder.parent / f'bin_{number}_{device}_{variant}.lib'
        if not source.exists():
            ModelExtractor(self.original_model_file, device).extract_bin_parameters(number)
        text = source.read_text()
        blocks = model_blocks(text, device)
        if number not in blocks:
            raise ValueError(f'Extracted model does not contain {device} bin {number}')
        start, end = blocks[number]
        values = parameters(text[start:end])
        if float(values.get('level', '0')) != 54:
            raise ValueError('Spectre conversion requires an extracted SKY130 BSIM4 model')
        model_name = f'sky130_icemos_{device}_bin_{number}'
        # Preserve copyright comments, use source values, and remove only SPICE's
        # level selector. Spectre selects the device family with the bsim4 keyword.
        comments = ['// ' + line.lstrip()[1:].lstrip() for line in text.splitlines()
                    if line.lstrip().startswith('*')]
        lines = [*comments, 'simulator lang=spectre',
                 f'model {model_name} bsim4 type={device[0]}']
        for name, value in values.items():
            if name != 'level':
                if not re.fullmatch(r'[-+0-9.eE]+', value):
                    raise ValueError(f'Unresolved expression in extracted parameter {name}')
                lines[-1] += ' \\'
                lines.append(f'    {name}={numeric_value(value)}')
        model = folder / f'bin_{number}_{device}_{variant}.scs'
        model.write_text('\n'.join(lines) + '\n')
        return model, model_name

    def generate(self, device_type, *, bin_number=None, W=None, L=None, analysis='iv',
                 gate_start=0, gate_stop=1.8, gate_step=0.1,
                 drain_start=0, drain_stop=1.8, drain_step=0.1, variant='modified'):
        device = device_type.lower()
        number, width, length = self._resolve_bin(device, bin_number, W, L)
        if variant not in ('original', 'modified') or analysis not in ('iv', 'output'):
            raise ValueError('Unknown model variant or analysis')
        gates = sweep_values(gate_start, gate_stop, gate_step)
        drains = sweep_values(drain_start, drain_stop, drain_step)
        folder = Path('circuits') / device / f'bin_{number}' / 'spectre'
        folder.mkdir(parents=True, exist_ok=True)
        model, name = self._native_model(device, number, variant, folder)
        temperature = 27 if variant == 'original' else -220
        jobs = []
        for index, gate in enumerate([None] if analysis == 'iv' else gates):
            # PMOS uses negative gate/drain biases relative to source/body at 0 V.
            # Sense-source orientation makes IDS/ISD positive in both cases.
            gate_nodes, drain_nodes, sense_nodes = (
                ('g 0', 'supply 0', 'supply d') if device == 'nch'
                else ('0 g', '0 supply', 'd supply'))
            gate_dc = gate_start if gate is None else gate
            drain_dc = 1.8 if analysis == 'iv' else drain_start
            sweep = 'VGATE' if analysis == 'iv' else 'VDRAIN'
            start, stop, step = ((gate_start, gate_stop, gate_step) if analysis == 'iv'
                                 else (drain_start, drain_stop, drain_step))
            path = folder / f'{analysis}_{variant}_{index:04d}.scs'
            # Diffusion geometry follows the public ngspice testbench (nf=1).
            area = width * 0.29 * 1e-12
            perimeter = 2 * (width + 0.29) * 1e-6
            text = f'''// IceMOS SKY130 standalone {device} {analysis} simulation
simulator lang=spectre
include "{model.name}"
simulatorOptions options temp={temperature}
VGATE ({gate_nodes}) vsource dc={gate_dc:.17g}
VDRAIN ({drain_nodes}) vsource dc={drain_dc:.17g}
VMEAS ({sense_nodes}) vsource dc=0
M1 (d g 0 0) {name} w={width:.17g}u l={length:.17g}u nf=1 \\
    ad={area:.17g} as={area:.17g} pd={perimeter:.17g} ps={perimeter:.17g} \\
    nrd={0.29/width:.17g} nrs={0.29/width:.17g} sa=0 sb=0 sd=0
save VMEAS:p
saveOptions options save=selected
icemos_dc dc dev={sweep} param=dc start={start:.17g} stop={stop:.17g} step={step:.17g}
'''
            path.write_text(text)
            jobs.append(SpectreJob(path, analysis, gate, gates if analysis == 'iv' else drains))
        return jobs
