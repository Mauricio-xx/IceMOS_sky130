import os
import sys

# Add the 'src' directory to the Python path.
# Assuming the 'test' directory is one level below the project root and 'src' is in the project root.
sources_path = os.path.join(os.path.dirname(__file__), "../src")
sys.path.insert(0, sources_path)

from IceMOS_sky130_netlist_generator import NetlistGeneratorSky130


def main():
    # Path to the original model file (without "modified" in its name)
    original_model_file = "../pdk_original_models/sky130_fd_pr__nfet_01v8.pm3.spice"

    # Create an instance of the netlist generator.
    generator = NetlistGeneratorSky130(original_model_file)

    # Option 1: Generate IV vs VDS netlists by providing a bin number for NMOS.
    print("Generating IV vs VDS netlists for NMOS using bin number 0...")
    netlists_vds = generator.generate_iv_vds_netlists(
        device_type='nch',
        bin_number=0,
        vgs_start=0,
        vgs_stop=1.8,
        vgs_step=0.6,
        vds_start=0,
        vds_stop=1.8,
        vds_step=0.1
    )
    print("Generated IV vs VDS netlists (by bin number):")
    print(netlists_vds)

    # Option 2: Generate IV vs VDS netlists by providing dimensions for NMOS.
    print("Generating IV vs VDS netlists for NMOS using dimensions W=1.26 µm, L=0.15 µm...")
    netlists_vds_dims = generator.generate_iv_vds_netlists(
        device_type='nch',
        W=1.26,
        L=0.15,
        vgs_start=0,
        vgs_stop=1.8,
        vgs_step=0.6,
        vds_start=0,
        vds_stop=1.8,
        vds_step=0.1
    )
    print("Generated IV vs VDS netlists (by dimensions):")
    print(netlists_vds_dims)


if __name__ == '__main__':
    main()
