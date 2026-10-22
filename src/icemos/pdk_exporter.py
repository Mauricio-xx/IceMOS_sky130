"""Apply calibration sessions to a separate copy of a public SKY130 model file."""

import json
from pathlib import Path

from icemos.model_io import atomic_write, patch_bin


def calibration_values(session):
    """Accept GUI sessions (value/min/max dictionaries) or plain numeric maps."""
    if not isinstance(session, dict) or not session:
        raise ValueError('Calibration must be a nonempty parameter mapping')
    return {name: value['value'] if isinstance(value, dict) else value
            for name, value in session.items()}


def export_calibrated_model(source, destination, device_type, calibrations):
    """Patch {bin_number: session} atomically, preserving all other source text."""
    if Path(source).resolve() == Path(destination).resolve():
        raise ValueError('Export destination must differ from the original model')
    if not calibrations:
        raise ValueError('At least one calibrated bin is required')
    text = Path(source).read_text()
    for number, session in calibrations.items():
        text = patch_bin(text, device_type, int(number), calibration_values(session))
    atomic_write(destination, text)
    return Path(destination)


def load_calibration(path):
    with open(path) as stream:
        session = json.load(stream)
    calibration_values(session)
    return session
