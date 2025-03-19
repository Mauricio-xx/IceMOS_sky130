import os
import sys

# Add the 'src' directory to the Python path.
sources_path = os.path.join(os.path.dirname(__file__), "../src")
sys.path.insert(0, sources_path)

from IceMOS_sky130_calibrator import MainWindow
from PyQt5 import QtWidgets
from IceMOS_sky130_circuit_model_extractor import ModelExtractor # for model extraction


def extraction(device_type, bin_number):
    # ---------- setup for extraction ---------- #
    original_model_file_nch = "../pdk_original_models/sky130_fd_pr__nfet_01v8.pm3.spice"
    original_model_file_pch = "../pdk_original_models/sky130_fd_pr__pfet_01v8.pm3.spice"

    if device_type == 'nch':
        # Create an instance of ModelExtractor for NMOS (nch)
        extractor_nch = ModelExtractor(original_model_file_nch, device_type='nch')
        extractor_nch.extract_bin_parameters(bin_number)
    else:
        extractor_pch = ModelExtractor(original_model_file_pch, device_type='pch')
        extractor_pch.extract_bin_parameters(bin_number)


def main():
    app = QtWidgets.QApplication(sys.argv)
    window = MainWindow(device_type, bin_number)  #set the device that will be calibrated
    window.resize(400, 500)
    window.show()
    sys.exit(app.exec_())

if __name__ == "__main__":

    # ---------- device configuration ---------- #
    device_type = "nch"
    bin_number = 40

    # ---------- device extraction ---------- #
    extraction(device_type, bin_number)

    # ---------- Calibrator ---------- #
    main()
