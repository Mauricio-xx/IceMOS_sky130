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

    # Option 1: Generate netlists by providing a bin number.
    print("Generating netlists using bin number 0 for NMOS...")
    netlists_by_bin = generator.generate_iv_netlists(
        device_type='nch',
        bin_number=0,
        vgate_start=0,
        vgate_stop=1.8,
        vgate_step=0.1
    )
    print("Generated netlists (by bin number):")
    print(netlists_by_bin)

    # Option 1, example 2: Generate netlists by providing a bin number.
    print("Generating netlists using bin number 10 for NMOS...")
    netlists_by_bin = generator.generate_iv_netlists(
        device_type='nch',
        bin_number=10,
        vgate_start=0,
        vgate_stop=1.8,
        vgate_step=0.1
    )
    print("Generated netlists (by bin number):")
    print(netlists_by_bin)

    # Option 2: Generate netlists by providing dimensions (for NMOS: W=1.26 µm, L=0.15 µm)
    print("Generating netlists using dimensions W=1.26 µm, L=0.15 µm for NMOS...")
    netlists_by_dims = generator.generate_iv_netlists(
        device_type='nch',
        W=1.26,
        L=0.15,
        vgate_start=0,
        vgate_stop=1.8,
        vgate_step=0.1
    )
    print("Generated netlists (by dimensions):")
    print(netlists_by_dims)


if __name__ == '__main__':
    main()
