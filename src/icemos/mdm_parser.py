"""Read measurement database blocks and export each sweep to a separate CSV."""

import csv
from dataclasses import dataclass
import math
from pathlib import Path
import re


@dataclass
class MeasurementBlock:
    voltages: dict
    columns: list
    data: list


def read_mdm(path):
    blocks = []
    block = None
    for number, raw in enumerate(Path(path).read_text().splitlines(), 1):
        line = raw.strip()
        if line == 'BEGIN_DB':
            if block is not None:
                raise ValueError(f'Nested BEGIN_DB at line {number}')
            block = MeasurementBlock({}, [], [])
        elif line == 'END_DB':
            if block is None or not block.columns or not block.data:
                raise ValueError(f'Empty or unmatched END_DB at line {number}')
            blocks.append(block)
            block = None
        elif block is not None and line:
            if line.startswith('ICCAP_VAR'):
                parts = line.split()
                if len(parts) != 3:
                    raise ValueError(f'Invalid sweep variable at line {number}')
                value = float(parts[2])
                if not math.isfinite(value):
                    raise ValueError(f'Non-finite sweep variable at line {number}')
                block.voltages[parts[1]] = value
            elif line.startswith('#'):
                # Database comments may follow the column header.
                if not block.columns:
                    block.columns = line[1:].split()
                    if len(set(block.columns)) != len(block.columns):
                        raise ValueError(f'Duplicate columns at line {number}')
            else:
                values = [float(value) for value in line.split()]
                if len(values) != len(block.columns) or not all(map(math.isfinite, values)):
                    raise ValueError(f'Invalid measurement row at line {number}')
                block.data.append(values)
    if block is not None:
        raise ValueError('Unterminated measurement block')
    if not blocks:
        raise ValueError('No measurement blocks found')
    return blocks


class MDMParser:
    """Generic sweep importer with the original parser's public entry points."""

    def __init__(self, mdm_files_path, mdm_file_name, voltage_var_names):
        self.path = Path(mdm_files_path) / mdm_file_name
        self.voltage_var_names = list(voltage_var_names)

    def export_csv(self, output_dir, blocks=None):
        blocks = read_mdm(self.path) if blocks is None else blocks
        for block in blocks:
            missing = set(self.voltage_var_names) - block.voltages.keys()
            if missing:
                raise ValueError('Missing sweep variables: ' + ', '.join(sorted(missing)))
        output_dir = Path(output_dir)
        output_dir.mkdir(parents=True, exist_ok=True)
        paths, sweeps = [], []
        for index, block in enumerate(blocks):
            sweep = {key: block.voltages[key] for key in self.voltage_var_names}
            suffix = ''.join(f'_{key}_{value:g}' for key, value in sweep.items())
            # User-supplied metadata must never become directory traversal.
            name = re.sub(r'[^\w.+=-]', '_', self.path.stem + suffix)
            path = output_dir / f'{index:04d}_{name}.csv'
            with path.open('w', newline='') as stream:
                writer = csv.writer(stream)
                writer.writerow(block.columns)
                writer.writerows(block.data)
            paths.append(str(path))
            sweeps.append(sweep)
        return paths, sweeps

    def process_mdm_file_generic(self):
        return self.export_csv(self.path.parent / 'MDM_to_CSV_IV_Vsweep_generic')

    def process_mdm_file_for_IV_VGsweep(self, vgate_position_in_voltage_var_names):
        key = self.voltage_var_names[vgate_position_in_voltage_var_names]
        paths, sweeps = self.export_csv(self.path.parent / 'MDM_to_CSV_IV_VGsweep')
        return paths, [sweep[key] for sweep in sweeps]

    def process_mdm_file_for_IV(self):
        blocks = read_mdm(self.path)
        if len(blocks) != 1:
            raise ValueError('Multiple blocks: use the generic sweep exporter to retain every curve')
        return self.export_csv(self.path.parent / 'MDM_to_CSV_IV', blocks)[0][0]
