# IceMOS_sky130

IceMOS_sky130 is a toolbox for manual cryogenic calibration of the SKY130 open
PDK. It imports measurements, extracts NMOS and PMOS model bins, runs ngspice,
compares simulated and measured curves, and exports calibrated model files.

## Install

Use Python 3.10 or newer and install ngspice on your system. From this checkout:

```bash
python3 -m venv .venv
.venv/bin/python -m pip install -e '.[gui,test]'
```

The command line import and export tools use only the Python standard library.
For those tools alone, install with `.venv/bin/python -m pip install -e .`.
The bundled models under `pdk_original_models/` are public SKY130 models; their
original copyright and Apache 2.0 notices remain in the files.

## Calibrate a bin

Run from a working directory where generated `circuits/` files can be saved:

```bash
.venv/bin/icemos-sky130 gui \
  pdk_original_models/sky130_fd_pr__nfet_01v8.pm3.spice --device nch --bin 40
```

For PMOS, choose `sky130_fd_pr__pfet_01v8.pm3.spice`, `--device pch` and the
appropriate bin, for example `--bin 1`.

1. Select parameters and adjust their values or ranges. Save/load calibration
   sessions as JSON.
2. Open the simulation window. Import MDM files to CSV if needed, then use
   **Load Lab Data** to select CSV curves and their voltage/current columns.
3. Use **Apply and Simulate** to write the selected values and update the plot.
   Continuous simulation applies current values before every run, at five second
   intervals. Errors stop continuous simulation.
4. Choose **Export Calibrated Model** to write the selected calibration into a
   separate copy of the supplied full model file. Other bins and expression
   suffixes remain unchanged. The input file is never overwritten.

Launching a workspace again preserves its modified bin model. The GUI also
supports opening previously extracted bins through the Python `MainWindow` API;
without a full source model path, its export contains only that extracted bin.

The fitting loop is manual. Exporting a model does not establish its physical
accuracy. Modified netlists currently use the inherited effective temperature
of -220 °C (53.15 K); original netlists use 27 °C. Measurements taken at 4 K need
an independently validated calibration. Simulation runs synchronously in the GUI,
with a 120 second timeout. No extra PDK installation or user ngspice startup
configuration is needed for these standalone device simulations.

## Import measurement sweeps

```bash
.venv/bin/icemos-sky130 mdm measurements.mdm \
  --variables VG VB --output output/measurements
```

Each `BEGIN_DB` / `END_DB` block becomes a separate CSV. Variable names are
optional and come from the input file. Indexed filenames preserve curves with
repeated bias values. Malformed rows, incomplete blocks and non-finite numbers
are rejected. Import does not modify the source measurement file.

## Export saved calibrations

```bash
.venv/bin/icemos-sky130 export \
  pdk_original_models/sky130_fd_pr__nfet_01v8.pm3.spice calibration.json \
  --device nch --bin 40 --output output/nfet_calibrated.spice
```

The command accepts GUI session dictionaries (`{"vth0": {"value": 0.75}}`) or
plain numeric maps (`{"vth0": 0.75}`). These values illustrate the format only.
The Python `export_calibrated_model` API accepts multiple calibrated bins in one
operation. Export validates all requested changes before writing the destination.
It produces a model file; packaging a full calibrated PDK is a separate step.

## Development and content review

```bash
.venv/bin/python -m pytest -q
.venv/bin/python tools/check_public_content.py
.venv/bin/python tools/check_public_content.py --base origin/main
```

Tests use synthetic inputs and the bundled public models. Simulation tests run
when ngspice is available. Older scripts under `test/` are interactive examples;
the automated suite is under `tests/`.

The content checker inspects tracked files, or every added/modified file version
in the requested commit range. It flags generated environments, archives,
notebooks, binaries and model declarations outside the SKY130 namespace. An
optional `--deny-pattern-file /path/outside/checkout` adds a local content policy
without placing its patterns in the public repository. This check complements
manual review of source provenance and numerical data; it cannot prove that
arbitrary text or numeric values are suitable for publication.

## Background and license

This work follows the ideas reported in
[the associated publication](https://ieeexplore.ieee.org/document/10658695).

IceMOS is released under the [Educational Community License 2.0](LICENSE).
Copyright 2025 University College Cork. See the license for permissions,
conditions and the disclaimer of warranties.
