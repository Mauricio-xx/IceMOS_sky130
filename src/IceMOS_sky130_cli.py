"""Command line entry points for SKY130 calibration workflows."""

import argparse
from pathlib import Path


def main(argv=None):
    parser = argparse.ArgumentParser(description='IceMOS SKY130 calibration toolbox')
    commands = parser.add_subparsers(dest='command', required=True)
    mdm = commands.add_parser('mdm', help='Convert every MDM measurement block to CSV')
    mdm.add_argument('input', type=Path)
    mdm.add_argument('--output', type=Path, required=True)
    mdm.add_argument('--variables', nargs='*', default=[])
    export = commands.add_parser('export', help='Apply a calibration JSON to a public model bin')
    export.add_argument('model', type=Path)
    export.add_argument('calibration', type=Path)
    export.add_argument('--device', choices=['nch', 'pch'], required=True)
    export.add_argument('--bin', type=int, required=True)
    export.add_argument('--output', type=Path, required=True)
    gui = commands.add_parser('gui', help='Extract a SKY130 bin and open the calibration GUI')
    gui.add_argument('model', type=Path)
    gui.add_argument('--device', choices=['nch', 'pch'], required=True)
    gui.add_argument('--bin', type=int, required=True)
    gui.add_argument('--backend', choices=['ngspice', 'spectre'], default='ngspice')
    gui.add_argument('--spectre-bin', help='Spectre executable; otherwise use SPECTRE_BIN or PATH')
    simulate = commands.add_parser('simulate', help='Run a SKY130 IV or output sweep')
    simulate.add_argument('model', type=Path)
    simulate.add_argument('--backend', choices=['ngspice', 'spectre'], default='ngspice')
    simulate.add_argument('--spectre-bin', help='Spectre executable; otherwise use SPECTRE_BIN or PATH')
    simulate.add_argument('--device', choices=['nch', 'pch'], required=True)
    simulate.add_argument('--bin', type=int, required=True)
    simulate.add_argument('--analysis', choices=['iv', 'output'], default='iv')
    simulate.add_argument('--variant', choices=['original', 'modified'], default='modified')
    simulate.add_argument('--gate-start', type=float, default=0)
    simulate.add_argument('--gate-stop', type=float, default=1.8)
    simulate.add_argument('--gate-step', type=float, default=0.1)
    simulate.add_argument('--drain-start', type=float, default=0)
    simulate.add_argument('--drain-stop', type=float, default=1.8)
    simulate.add_argument('--drain-step', type=float, default=0.1)
    simulate.add_argument('--output', type=Path, required=True)
    args = parser.parse_args(argv)
    try:
        if args.command == 'mdm':
            from IceMOS_sky130_mdm_parser import MDMParser
            files, _ = MDMParser(args.input.parent, args.input.name, args.variables).export_csv(args.output)
            for path in files:
                print(path)
        elif args.command == 'export':
            from IceMOS_sky130_pdk_exporter import export_calibrated_model, load_calibration
            print(export_calibrated_model(args.model, args.output, args.device,
                                          {args.bin: load_calibration(args.calibration)}))
        elif args.command == 'simulate':
            import csv
            from IceMOS_sky130_simulation import create_simulator
            simulator = create_simulator(args.model.resolve(), args.backend, spectre_executable=args.spectre_bin)
            common = dict(bin_number=args.bin, model_type=args.variant)
            if args.analysis == 'iv':
                simulator.simulate_iv(args.device, **common, vgate_start=args.gate_start,
                                      vgate_stop=args.gate_stop, vgate_step=args.gate_step)
                curves = [simulator.read_iv_results(args.device, args.bin)]
            else:
                if args.device == 'nch':
                    simulator.simulate_id_vs_vds_sweep_vg(
                        args.device, **common, vgs_start=args.gate_start,
                        vgs_stop=args.gate_stop, vgs_step=args.gate_step,
                        vds_start=args.drain_start, vds_stop=args.drain_stop, vds_step=args.drain_step)
                else:
                    simulator.simulate_is_vs_vsd_sweep_vg(
                        args.device, **common, vsg_start=args.gate_start,
                        vsg_stop=args.gate_stop, vsg_step=args.gate_step,
                        vsd_start=args.drain_start, vsd_stop=args.drain_stop, vsd_step=args.drain_step)
                curves = simulator.read_output_results(args.device, args.bin)
            args.output.parent.mkdir(parents=True, exist_ok=True)
            with args.output.open('w', newline='') as stream:
                writer = csv.writer(stream)
                writer.writerow(['curve', 'voltage', 'current'])
                for curve in curves:
                    writer.writerows((curve.label, x, y) for x, y in zip(curve.x, curve.y))
            print(args.output)
        else:
            from PyQt5 import QtWidgets
            from IceMOS_sky130_circuit_model_extractor import ModelExtractor
            from IceMOS_sky130_calibrator import MainWindow
            model = args.model.resolve()
            ModelExtractor(model, args.device).extract_bin_parameters(args.bin)
            app = QtWidgets.QApplication.instance() or QtWidgets.QApplication([])
            window = MainWindow(args.device, args.bin, original_model_file=model, backend=args.backend,
                                spectre_executable=args.spectre_bin)
            window.resize(1100, 650)
            window.show()
            return app.exec_()
    except (OSError, ValueError, KeyError, RuntimeError) as error:
        parser.error(str(error))
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
