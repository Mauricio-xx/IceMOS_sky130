# IceMOS_sky130

A toolbox for manual cryogenic calibration of the SKY130 open PDK: import
measurements, tune NMOS/PMOS model parameters, compare simulations with measured
curves, and export calibrated models.

## Install

Requires Python 3.10+ and ngspice, or a separately configured Spectre installation.

```bash
python3 -m venv .venv
.venv/bin/python -m pip install -e '.[gui]'
```

## Use

From this checkout, open the calibration GUI:

```bash
.venv/bin/icemos-sky130 gui \
  pdk_original_models/sky130_fd_pr__nfet_01v8.pm3.spice --device nch --bin 40
```

Select parameters, load CSV measurements (or import MDM), then **Apply and
Simulate**. Save sessions as JSON or use **Export Calibrated Model**.

For PMOS, use `sky130_fd_pr__pfet_01v8.pm3.spice` with `--device pch --bin 1`.
Choose ngspice or Spectre in the simulation window; ngspice is the default.
Spectre can also be selected with `--backend spectre`. Set `SPECTRE_BIN` if its
executable is outside PATH.

The CLI also provides `mdm`, `simulate` and `export` commands. Run
`.venv/bin/icemos-sky130 <command> --help` for options.

## Status

- ngspice is tested with real NMOS/PMOS simulations. Spectre's wrapper is tested
  with synthetic results; validation with a real Spectre installation is pending.

## License

[Educational Community License 2.0](LICENSE). Copyright 2025 University College
Cork. Bundled SKY130 models retain their original Apache 2.0 notices.

Based on the ideas described in [the associated publication](https://ieeexplore.ieee.org/document/10658695).
