import os
import sys

# Add the 'sources' directory to the Python path.
# Assuming the 'test' directory is one level below the project root and 'sources' is in the project root.
sources_path = os.path.join(os.path.dirname(__file__), "../src")
sys.path.insert(0, sources_path)

from IceMOS_sky130_circuit_model_extractor import ModelExtractor


def main():
    # Path to the original SPICE model file.
    # Adjust the file name/path as needed; here we assume it's located in the 'sources' directory.
    original_model_file_nch = "../pdk_original_models/sky130_fd_pr__nfet_01v8.pm3.spice"
    original_model_file_pch = "../pdk_original_models/sky130_fd_pr__pfet_01v8.pm3.spice"

    # ---------------------------------
    # Create an instance of ModelExtractor for NMOS (nch)
    # extractor_nch = ModelExtractor(original_model_file_nch, device_type='nch')

    # Extract parameters for bin 0.
    # This will save the extracted model in:
    # circuits/nch/bin_0/bin_0_nch.model
    # extractor_nch.extract_bin_parameters(0)

    # ---------------------------------
    # Create an instance of ModelExtractor for PMOS (pch)
    extractor_pch = ModelExtractor(original_model_file_pch, device_type='pch')

    # Extract parameters for bin 1.
    # This will save the extracted model in:
    # circuits/nch/bin_0/bin_0_nch.model
    # extractor_pch.extract_bin_parameters(1)

    # For PMOS extraction by dimensions:
    extractor_pch.extract_bin_parameters_by_dimensions(1.68, 0.15)

    # ---------------------------------
    # For NMOS extraction by dimensions:
    # Example: Extract the bin for W = 1.26 µm, L = 0.15 µm
    # extractor_nch.extract_bin_parameters_by_dimensions(1.26, 0.15)


if __name__ == '__main__':
    main()
