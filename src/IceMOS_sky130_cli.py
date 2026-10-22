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
        else:
            from PyQt5 import QtWidgets
            from IceMOS_sky130_circuit_model_extractor import ModelExtractor
            from IceMOS_sky130_calibrator import MainWindow
            model = args.model.resolve()
            ModelExtractor(model, args.device).extract_bin_parameters(args.bin)
            app = QtWidgets.QApplication.instance() or QtWidgets.QApplication([])
            window = MainWindow(args.device, args.bin, original_model_file=model)
            window.resize(1100, 650)
            window.show()
            return app.exec_()
    except (OSError, ValueError, KeyError, RuntimeError) as error:
        parser.error(str(error))
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
