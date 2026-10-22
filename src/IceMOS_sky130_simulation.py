"""Processed curves shared by the UI; model extraction stays in the SKY130 adapter."""

from dataclasses import dataclass
import math


@dataclass
class SimulationCurve:
    x: list
    y: list
    label: str

    def __post_init__(self):
        if not self.x or len(self.x) != len(self.y):
            raise ValueError('Simulation curve must have matching, nonempty vectors')
        if not all(math.isfinite(v) for v in (*self.x, *self.y)):
            raise ValueError('Simulation curve contains non-finite values')


def sweep_values(start, stop, step):
    if not all(math.isfinite(v) for v in (start, stop, step)) or step <= 0 or stop < start:
        raise ValueError('Sweep requires finite values, a positive step and stop >= start')
    count = (stop - start) / step
    if count > 100000:
        raise ValueError('Sweep exceeds 100000 steps')
    return [start + index * step for index in range(math.floor(count + 1e-9) + 1)]


def create_simulator(model, backend='ngspice', *, spectre_executable=None):
    if backend == 'ngspice':
        from IceMOS_sky130_simulator import IceMOS_simulator_sky130
        return IceMOS_simulator_sky130(model)
    if backend == 'spectre':
        from IceMOS_sky130_spectre_simulator import SpectreSimulatorSky130
        return SpectreSimulatorSky130(model, executable=spectre_executable)
    raise ValueError(f'Unknown simulator backend: {backend}')
