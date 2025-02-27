import os
import sys

# Add the 'src' directory to the Python path.
# Assuming the 'test' directory is one level below the project root and 'src' is in the project root.
sources_path = os.path.join(os.path.dirname(__file__), "../src")
sys.path.insert(0, sources_path)

from IceMOS_sky130_simulator import IceMOS_simulator_sky130


def test_nmos_qt_nonblocking():
    """
    Test simulation and non-blocking interactive plotting for NMOS.

    Simulates an IV netlist (IDRAIN vs. VGATE) using a specified bin number for NMOS,
    then displays the interactive plot using PyQtGraph.
    """
    original_model_file = "../pdk_original_models/sky130_fd_pr__nfet_01v8.pm3.spice"
    simulator = IceMOS_simulator_sky130(original_model_file)

    print("Simulating IV for NMOS using bin number 0:")
    iv_output = simulator.simulate_iv(device_type='nch', bin_number=0,
                                      vgate_start=0, vgate_stop=1.8, vgate_step=0.1)
    print(iv_output)

    print("Displaying interactive IV plot for NMOS (bin 0) without blocking:")
    win_nmos = simulator.plot_iv_results_qt(device_type='nch', bin_number=0, csv_filename="IV_ID_vs_VG.csv")
    # Keep a reference to the NMOS window to prevent it from being garbage-collected.
    return win_nmos


def test_pmos_qt_nonblocking():
    """
    Test simulation and non-blocking interactive plotting for PMOS.

    Simulates an IV netlist (IDRAIN vs. VGATE) using a specified bin number for PMOS,
    then displays the interactive plot using PyQtGraph.
    """
    original_model_file = "../pdk_original_models/sky130_fd_pr__pfet_01v8.pm3.spice"
    simulator = IceMOS_simulator_sky130(original_model_file)

    print("Simulating IV for PMOS using bin number 10:")
    iv_output = simulator.simulate_iv(device_type='pch', bin_number=10,
                                      vgate_start=0, vgate_stop=1.8, vgate_step=0.1)
    print(iv_output)

    print("Displaying interactive IV plot for PMOS (bin 10) without blocking:")
    win_pmos = simulator.plot_iv_results_qt(device_type='pch', bin_number=10, csv_filename="IV_ID_vs_VG.csv")
    return win_pmos


def main():
    print("===== Testing NMOS interactive IV plotting (non-blocking) =====")
    win_nmos = test_nmos_qt_nonblocking()

    print("\n===== Testing PMOS interactive IV plotting (non-blocking) =====")
    win_pmos = test_pmos_qt_nonblocking()

    # Optionally, keep the script running so that windows remain interactive.
    # If you're running in an interactive environment (or a proper Qt event loop),
    # the windows should remain responsive.
    input("Press Enter to exit and close all plot windows...")


if __name__ == '__main__':
    main()
