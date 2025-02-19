import os
import sys

# Add the 'src' directory to the Python path.
# Assuming the 'test' directory is one level below the project root and 'src' is in the project root.
sources_path = os.path.join(os.path.dirname(__file__), "../src")
sys.path.insert(0, sources_path)

from IceMOS_sky130_simulator import IceMOS_simulator_sky130


def test_nmos_by_bin():
    print("=== NMOS Simulation using bin number ===")
    # Path to the original NMOS model file (without "modified" in its name)
    original_model_file = "../pdk_original_models/sky130_fd_pr__nfet_01v8.pm3.spice"
    simulator = IceMOS_simulator_sky130(original_model_file)
    # Simulate IV (IDRAIN vs. VGATE) using a provided bin number (e.g., 0)
    print("Simulating IV for NMOS using bin number 0:")
    iv_output = simulator.simulate_iv(device_type='nch', bin_number=0,
                                      vgate_start=0, vgate_stop=1.8, vgate_step=0.1)
    print(iv_output)
    # Simulate IV VDS (IDRAIN vs. VDRAIN with VGATE sweep) using a provided bin number (e.g., 0)
    print("Simulating IV VDS for NMOS using bin number 0:")
    iv_vds_output = simulator.simulate_iv_vds(device_type='nch', bin_number=0,
                                              vgs_start=0, vgs_stop=1.8, vgs_step=0.6,
                                              vds_start=0, vds_stop=1.8, vds_step=0.1)
    print(iv_vds_output)


def test_nmos_by_dimensions():
    print("=== NMOS Simulation using dimensions ===")
    original_model_file = "../pdk_original_models/sky130_fd_pr__nfet_01v8.pm3.spice"
    simulator = IceMOS_simulator_sky130(original_model_file)
    # Simulate IV using dimensions (e.g., W=1.26 µm, L=0.15 µm)
    print("Simulating IV for NMOS using dimensions W=1.26 µm, L=0.15 µm:")
    iv_output = simulator.simulate_iv(device_type='nch', W=1.26, L=0.15,
                                      vgate_start=0, vgate_stop=1.8, vgate_step=0.1)
    print(iv_output)
    # Simulate IV VDS using dimensions
    print("Simulating IV VDS for NMOS using dimensions W=1.26 µm, L=0.15 µm:")
    iv_vds_output = simulator.simulate_iv_vds(device_type='nch', W=1.26, L=0.15,
                                              vgs_start=0, vgs_stop=1.8, vgs_step=0.6,
                                              vds_start=0, vds_stop=1.8, vds_step=0.1)
    print(iv_vds_output)


def test_pmos_by_bin():
    print("=== PMOS Simulation using bin number ===")
    # Path to the original PMOS model file (without "modified" in its name)
    original_model_file = "../pdk_original_models/sky130_fd_pr__pfet_01v8.pm3.spice"
    simulator = IceMOS_simulator_sky130(original_model_file)
    # Simulate IV using an explicit bin number (e.g., 10)
    print("Simulating IV for PMOS using bin number 10:")
    iv_output = simulator.simulate_iv(device_type='pch', bin_number=10,
                                      vgate_start=0, vgate_stop=1.8, vgate_step=0.1)
    print(iv_output)
    # Simulate IV VDS using an explicit bin number (e.g., 10)
    print("Simulating IV VDS for PMOS using bin number 10:")
    iv_vds_output = simulator.simulate_iv_vds(device_type='pch', bin_number=10,
                                              vgs_start=0, vgs_stop=1.8, vgs_step=0.6,
                                              vds_start=0, vds_stop=1.8, vds_step=0.1)
    print(iv_vds_output)


def test_pmos_by_dimensions():
    print("=== PMOS Simulation using dimensions ===")
    original_model_file = "../pdk_original_models/sky130_fd_pr__pfet_01v8.pm3.spice"
    simulator = IceMOS_simulator_sky130(original_model_file)
    # Simulate IV using dimensions (for example, W=1.26 µm, L=0.15 µm)
    print("Simulating IV for PMOS using dimensions W=1.26 µm, L=0.15 µm:")
    iv_output = simulator.simulate_iv(device_type='pch', W=1.26, L=0.15,
                                      vgate_start=0, vgate_stop=1.8, vgate_step=0.1)
    print(iv_output)
    # Simulate IV VDS using dimensions
    print("Simulating IV VDS for PMOS using dimensions W=1.26 µm, L=0.15 µm:")
    iv_vds_output = simulator.simulate_iv_vds(device_type='pch', W=1.26, L=0.15,
                                              vgs_start=0, vgs_stop=1.8, vgs_step=0.6,
                                              vds_start=0, vds_stop=1.8, vds_step=0.1)
    print(iv_vds_output)


def main():
    print("===== Testing NMOS simulations =====")
    test_nmos_by_bin()
    test_nmos_by_dimensions()
    print("")

    print("\n===== Testing PMOS simulations =====")
    test_pmos_by_bin()
    test_pmos_by_dimensions()
    print("")


if __name__ == '__main__':
    main()
