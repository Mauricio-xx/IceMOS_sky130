# IceMOS_sky130

IceMOS_sky130 is a toolbox for manual cryogenic calibration of the SKY130 open
PDK. It imports measurements, extracts NMOS and PMOS model bins, runs simulations,
compares simulated and measured curves, and exports calibrated model files.
ngspice is the default simulator; a separate optional Spectre backend is included.

## Install

Use Python 3.10 or newer. Install ngspice for the default backend, or provide your
own Spectre installation and runtime environment. From this checkout:

```bash
python3 -m venv .venv
.venv/bin/python -m pip install -e '.[gui,test]'
```

The command line tools and simulator wrappers use only the Python standard
library. For those tools alone, install with `.venv/bin/python -m pip install -e .`.
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
2. Open the simulation window and select **ngspice** or **spectre**, and the
   **modified** or **original** model. Import MDM files to CSV if needed, then use
   **Load Lab Data** to select CSV curves and their voltage/current columns.
3. Use **Apply and Simulate** to write the selected values and update the plot.
   Continuous simulation applies current values before every run, at five second
   intervals. Errors stop continuous simulation.
4. Choose **Export Calibrated Model** to write the selected calibration into a
   separate copy of the supplied full model file. Other bins and expression
   suffixes remain unchanged. The input file is never overwritten.

Launching a workspace again preserves its modified bin model and recovers its
changed numeric parameters. Removing a parameter from the selection restores its
source value on the next apply. The GUI also supports opening previously extracted bins through the Python `MainWindow` API;
without a full source model path, its export contains only that extracted bin.

The fitting loop is manual. Exporting a model does not establish its physical
accuracy. Modified netlists currently use the inherited effective temperature
of -220 °C (53.15 K); original netlists use 27 °C. Measurements taken at 4 K need
an independently validated calibration. Simulation runs synchronously in the GUI,
with a 120 second timeout. No extra PDK installation or user ngspice startup
configuration is needed for these standalone device simulations.

## Simulator backends

Model-file structure and simulator syntax are separate concerns. Both backends
use the existing SKY130 bin extractor and the same calibration state. Each tool
has its own testbench generation, process invocation and result reader; the GUI
consumes processed voltage/current curves.

| Component | ngspice | Spectre |
| --- | --- | --- |
| Model input | Extracted SKY130 BSIM4 bin | Same extracted SKY130 BSIM4 bin |
| Netlist | SPICE with control commands | Native Spectre with a `bsim4` model |
| Results | ngspice whitespace tables | Scalar DC PSF ASCII, then two-column CSV |
| Configuration | `ngspice` on PATH | `--spectre-bin`, `SPECTRE_BIN`, or `spectre` on PATH |

Spectre model cards are generated from the selected extracted SKY130 bin. The
SPICE `level` selector becomes the native `bsim4` model type; numerical parameter
values come from the selected original or modified bin. This converter expects
resolved numerical parameters from the existing extractor, and rejects unresolved
expressions. It does not load another model collection.

Spectre uses one DC analysis per gate bias in an output sweep. Each invocation
gets its own result directory under `circuits/<device>/bin_<number>/spectre/`,
so a failed run cannot reuse results from an earlier invocation. Its parser
accepts the scalar, one-dimensional DC PSF ASCII files requested by this backend;
other PSF formats are outside its scope. There is no binary PSF dependency.

The native circuit uses explicit micrometre dimensions. PMOS biases are negative
relative to its grounded source and body; returned curves use positive VSG/VSD
and a consistently oriented sense source for ISD. This is the same terminal-bias
convention as the ngspice flow, with a different common-mode voltage.

To start the GUI with Spectre selected:

```bash
.venv/bin/icemos-sky130 gui \
  pdk_original_models/sky130_fd_pr__nfet_01v8.pm3.spice \
  --device nch --bin 40 --backend spectre
```

To run a sweep without the GUI:

```bash
.venv/bin/icemos-sky130 simulate \
  pdk_original_models/sky130_fd_pr__nfet_01v8.pm3.spice \
  --device nch --bin 40 --backend spectre --analysis output \
  --gate-step 0.6 --drain-step 0.1 --output output/curves.csv
```

Use `--backend ngspice` for the default engine and `--variant original` to simulate
an original bin. The combined CLI CSV has `curve,voltage,current` columns for
either backend. Native result files remain in each backend's own format.

An executable outside PATH can be supplied with `--spectre-bin /path/to/spectre`
or `SPECTRE_BIN`. Configure any required license/runtime environment in your own
shell. The wrapper inherits it and does not set installation paths or license
servers. Spectre must be installed separately.

The native syntax follows the
[Cadence DC/BSIM4 example](https://community.cadence.com/cadence_technology_forums/f/custom-ic-design/43902/unit-of-self_gain-in-bsim4-v4-5).
The reader is intentionally limited to the scalar sweep layout described in the
[PSF ASCII parser documentation](https://chwa.github.io/psfdata/psfascii.html).

**Validation status:** ngspice is tested with actual simulations. Spectre model
conversion, process invocation, result parsing, GUI selection, original/modified
selection and failures are tested with public SKY130 models and a synthetic test
executable. Physical simulation with Spectre has not yet been validated in this
environment. The suite includes optional NMOS/PMOS smoke tests which run when
`SPECTRE_BIN` or a `spectre` executable is available with a working license. The
test executable is not a physical device simulator, and passing its tests does
not establish numerical agreement between engines.

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
when ngspice is available; real Spectre tests require its executable and runtime
environment. Older scripts under `test/` are interactive examples;
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
