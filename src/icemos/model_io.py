"""Validated, formatting-preserving edits to SKY130 model bins."""

import math
import os
from pathlib import Path
import re
import tempfile

PREFIXES = {
    'nch': 'sky130_fd_pr__nfet_01v8__model',
    'pch': 'sky130_fd_pr__pfet_01v8__model',
}
MODEL = re.compile(r'^\s*\.model\s+(\S+)\s+(\w+)', re.I | re.M)
ASSIGNMENT = re.compile(r'\b(\w+)\s*=\s*(\{[^{}]*\}|[^\s)]+)')
NUMBER = r'[-+]?(?:\d+(?:\.\d*)?|\.\d+)(?:[eE][-+]?\d+)?'


def model_blocks(text, device_type):
    """Return exact bin spans; any subsequent model terminates a block."""
    if device_type not in PREFIXES:
        raise ValueError("Device must be nch or pch")
    headers = list(MODEL.finditer(text))
    blocks = {}
    pattern = re.compile(re.escape(PREFIXES[device_type]) + r'\.(\d+)', re.I)
    for index, match in enumerate(headers):
        name = pattern.fullmatch(match[1])
        if name:
            bin_number = int(name[1])
            if bin_number in blocks:
                raise ValueError(f'Duplicate model bin {bin_number}')
            end = headers[index + 1].start() if index + 1 < len(headers) else len(text)
            blocks[bin_number] = (match.start(), end)
    return blocks


def parameters(text):
    """Read assignments from continuation lines, excluding comments."""
    return {m[1].lower(): m[2] for line in text.splitlines()
            if line.lstrip().startswith('+')
            for m in ASSIGNMENT.finditer(line.split('$', 1)[0])}


def numeric_value(value):
    if isinstance(value, bool):
        raise ValueError('Calibration values must be finite numbers')
    try:
        number = float(value)
    except (TypeError, ValueError) as error:
        raise ValueError('Calibration values must be finite numbers') from error
    if not math.isfinite(number):
        raise ValueError('Calibration values must be finite numbers')
    return format(number, '.17g')


def replace_value(original, value):
    value = numeric_value(value)
    if original.startswith('{'):
        # Preserve the public model's expression suffix; replace only its base.
        match = re.match(r'\{\s*(' + NUMBER + r')(?=\s*[+*/}-]|\s*$)', original)
        if not match:
            raise ValueError('Expression has no numeric base to calibrate')
        return original[:match.start(1)] + value + original[match.end(1):]
    if not re.fullmatch(NUMBER, original):
        raise ValueError('Only numeric parameters or expressions with a numeric base can be calibrated')
    return value


def patch_bin(text, device_type, bin_number, updates):
    blocks = model_blocks(text, device_type)
    if bin_number not in blocks:
        raise ValueError(f'Unknown {device_type} bin {bin_number}')
    start, end = blocks[bin_number]
    block = text[start:end]
    existing = parameters(block)
    normalized = {key.lower(): value for key, value in updates.items()}
    unknown = normalized.keys() - existing.keys()
    if unknown:
        raise ValueError('Unknown parameters: ' + ', '.join(sorted(unknown)))
    replacements = {key: replace_value(existing[key], value) for key, value in normalized.items()}
    lines = []
    for line in block.splitlines(keepends=True):
        if line.lstrip().startswith('+'):
            content, marker, comment = line.partition('$')
            content = ASSIGNMENT.sub(
                lambda m: m[0][:m.start(2) - m.start()] + replacements[m[1].lower()]
                if m[1].lower() in replacements else m[0], content)
            line = content + marker + comment
        lines.append(line)
    return text[:start] + ''.join(lines) + text[end:]


def atomic_write(destination, text):
    destination = Path(destination)
    destination.parent.mkdir(parents=True, exist_ok=True)
    temporary = None
    try:
        with tempfile.NamedTemporaryFile(mode='w', encoding='utf-8', dir=destination.parent,
                                         delete=False) as stream:
            temporary = stream.name
            stream.write(text)
        os.replace(temporary, destination)
    finally:
        if temporary and os.path.exists(temporary):
            os.unlink(temporary)
