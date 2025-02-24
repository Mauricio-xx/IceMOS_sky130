import os
import sys

# Add the 'src' directory to the Python path.
# Assuming the 'test' directory is one level below the project root and 'src' is in the project root.
sources_path = os.path.join(os.path.dirname(__file__), "../src")
sys.path.insert(0, sources_path)

from IceMOS_sky130_netlist_generator import NetlistGeneratorSky130


def main():
    # Path to the original PMOS model file
    original_model_file = "../pdk_original_models/sky130_fd_pr__pfet_01v8.pm3.spice"

    # Create an instance of the netlist generator.
    generator = NetlistGeneratorSky130(original_model_file)

    # Option 1: Generate IV netlists (IDRAIN vs. VGATE) for PMOS using an explicit bin number.
    print("Generating IV netlists for PMOS using bin number 0...")
    netlists_iv = generator.generate_iv_netlists(
        device_type='pch',
        bin_number=0,
        vgate_start=0,
        vgate_stop=1.8,
        vgate_step=0.1
    )
    print("Generated IV netlists for PMOS:")
    print(netlists_iv)

    # Option 2: Generate IV VDS netlists (IDRAIN vs. VDRAIN with VGATE sweep) for PMOS using dimensions.
    print("Generating IV VDS netlists for PMOS using dimensions W=1.26 µm, L=0.15 µm...")
    netlists_iv_vds = generator.generate_iv_vds_netlists(
        device_type='pch',
        W=1.26,
        L=0.15,
        vgs_start=0,
        vgs_stop=1.8,
        vgs_step=0.6,
        vds_start=0,
        vds_stop=1.8,
        vds_step=0.1
    )
    print("Generated IV VDS netlists for PMOS:")
    print(netlists_iv_vds)


if __name__ == '__main__':
    main()
