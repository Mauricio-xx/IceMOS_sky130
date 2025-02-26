import os
import sys

# Add the 'src' directory to the Python path.
sources_path = os.path.join(os.path.dirname(__file__), "../src")
sys.path.insert(0, sources_path)

from IceMOS_sky130_simulator import IceMOS_simulator_sky130


def test_iv_vds_plot_nmos():
    """
    Test interactive IV VDS plotting for NMOS.
    Simulate IV VDS using a specified bin number for NMOS and plot the results.
    """
    original_model_file = "../pdk_original_models/sky130_fd_pr__nfet_01v8.pm3.spice"
    simulator = IceMOS_simulator_sky130(original_model_file)

    print("Simulating IV VDS for NMOS using bin number 0:")
    iv_vds_output = simulator.simulate_iv_vds(device_type='nch', bin_number=0,
                                              vgs_start=0, vgs_stop=1.8, vgs_step=0.6,
                                              vds_start=0, vds_stop=1.8, vds_step=0.1)
    print(iv_vds_output)

    print("Plotting IV VDS results for NMOS (Bin 0) interactively using PyQtGraph:")
    win = simulator.plot_iv_vds_results_qt(device_type='nch', bin_number=0)
    return win


def test_iv_vds_plot_pmos():
    """
    Test interactive IV VDS plotting for PMOS.
    Simulate IV VDS using a specified bin number for PMOS and plot the results.
    """
    original_model_file = "../pdk_original_models/sky130_fd_pr__pfet_01v8.pm3.spice"
    simulator = IceMOS_simulator_sky130(original_model_file)

    print("Simulating IV VDS for PMOS using bin number 10:")
    iv_vds_output = simulator.simulate_iv_vds(device_type='pch', bin_number=10,
                                              vgs_start=0, vgs_stop=1.8, vgs_step=0.6,
                                              vds_start=0, vds_stop=1.8, vds_step=0.1)
    print(iv_vds_output)

    print("Plotting IV VDS results for PMOS (Bin 10) interactively using PyQtGraph:")
    win = simulator.plot_iv_vds_results_qt(device_type='pch', bin_number=10)
    return win


def main():
    print("===== Testing IV VDS interactive plotting for NMOS =====")
    win_nmos = test_iv_vds_plot_nmos()

    print("\n===== Testing IV VDS interactive plotting for PMOS =====")
    win_pmos = test_iv_vds_plot_pmos()

    input("Press Enter to exit and close all plot windows...")


if __name__ == '__main__':
    main()
