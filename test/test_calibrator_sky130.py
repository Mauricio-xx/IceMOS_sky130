import os
import sys

# Add the 'src' directory to the Python path.
sources_path = os.path.join(os.path.dirname(__file__), "../src")
sys.path.insert(0, sources_path)

from IceMOS_sky130_calibrator import MainWindow
from PyQt5 import QtWidgets

def main():
    app = QtWidgets.QApplication(sys.argv)
    # For example, calibrate PMOS bin 10:
    window = MainWindow("pch", 1)
    window.resize(1200, 800)
    window.show()
    sys.exit(app.exec_())

if __name__ == "__main__":
    main()
