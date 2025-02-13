import os
import re


class ModelExtractor:
    # Internal data for NMOS bins (nch)
    nmos_bins = {
        0: (1.26, 0.15),
        1: (1.68, 0.15),
        2: (1.0, 1.0),
        3: (1.0, 2.0),
        4: (1.0, 4.0),
        5: (1.0, 8.0),
        6: (1.0, 0.15),
        7: (1.0, 0.18),
        8: (1.0, 0.25),
        9: (1.0, 0.5),
        10: (2.0, 0.15),
        11: (3.0, 1.0),
        12: (3.0, 2.0),
        13: (3.0, 4.0),
        14: (3.0, 8.0),
        15: (3.0, 0.15),
        16: (3.0, 0.18),
        17: (3.0, 0.25),
        18: (3.0, 0.5),
        19: (5.0, 1.0),
        20: (5.0, 2.0),
        21: (5.0, 4.0),
        22: (5.0, 8.0),
        23: (5.0, 0.15),
        24: (5.0, 0.18),
        25: (5.0, 0.25),
        26: (5.0, 0.5),
        27: (7.0, 1.0),
        28: (7.0, 2.0),
        29: (7.0, 4.0),
        30: (7.0, 8.0),
        31: (7.0, 0.15),
        32: (7.0, 0.18),
        33: (7.0, 0.25),
        34: (7.0, 0.5),
        35: (0.42, 1.0),
        36: (0.42, 20.0),
        37: (0.42, 2.0),
        38: (0.42, 4.0),
        39: (0.42, 8.0),
        40: (0.42, 0.15),
        41: (0.42, 0.18),
        42: (0.42, 0.5),
        43: (0.55, 1.0),
        44: (0.55, 2.0),
        45: (0.55, 4.0),
        46: (0.55, 8.0),
        47: (0.55, 0.15),
        48: (0.55, 0.5),
        49: (0.64, 0.15),
        50: (0.84, 0.15),
        51: (0.74, 0.15),
        52: (0.36, 0.15),
        53: (0.39, 0.15),
        54: (0.52, 0.15),
        55: (0.54, 0.15),
        56: (0.58, 0.15),
        57: (0.6, 0.15),
        58: (0.61, 0.15),
        59: (0.65, 0.15),
        60: (0.65, 0.18),
        61: (0.65, 0.25),
        62: (0.65, 0.5)
    }

    # Internal data for PFET bins (pch)
    pmos_bins = {
        0: (1.26, 0.15),
        1: (1.68, 0.15),
        2: (1.0, 1.0),
        3: (1.0, 2.0),
        4: (1.0, 4.0),
        5: (1.0, 8.0),
        6: (1.0, 0.15),
        7: (1.0, 0.18),
        8: (1.0, 0.25),
        9: (1.0, 0.5),
        10: (2.0, 0.15),
        11: (3.0, 1.0),
        12: (3.0, 2.0),
        13: (3.0, 4.0),
        14: (3.0, 8.0),
        15: (3.0, 0.15),
        16: (3.0, 0.18),
        17: (3.0, 0.25),
        18: (3.0, 0.5),
        19: (5.0, 1.0),
        20: (5.0, 2.0),
        21: (5.0, 4.0),
        22: (5.0, 8.0),
        23: (5.0, 0.15),
        24: (5.0, 0.18),
        25: (5.0, 0.25),
        26: (5.0, 0.5),
        27: (7.0, 1.0),
        28: (7.0, 2.0),
        29: (7.0, 4.0),
        30: (7.0, 8.0),
        31: (7.0, 0.15),
        32: (7.0, 0.18),
        33: (7.0, 0.25),
        34: (7.0, 0.5),
        35: (0.42, 1.0),
        36: (0.42, 20.0),
        37: (0.42, 2.0),
        38: (0.42, 4.0),
        39: (0.42, 8.0),
        40: (0.42, 0.15),
        41: (0.42, 0.18),
        42: (0.42, 0.5),
        43: (0.55, 1.0),
        44: (0.55, 2.0),
        45: (0.55, 4.0),
        46: (0.55, 8.0),
        47: (0.55, 0.15),
        48: (0.55, 0.5),
        49: (0.64, 0.15),
        50: (0.84, 0.15),
        51: (1.65, 0.15)
    }

    def __init__(self, original_file_path, device_type='nch'):
        """
        Initializes the ModelExtractor with the path to the original SPICE model file and device type.

        Parameters:
            original_file_path (str): The path to the original SPICE model file.
            device_type (str): 'nch' for NMOS extraction or 'pch' for PMOS extraction. Default is 'nch'.
        """
        self.original_file_path = original_file_path
        self.device_type = device_type.lower()  # Ensure lower-case for comparison
        with open(original_file_path, 'r') as file:
            self.original_file = file.read()

    def extract_bin_parameters(self, bin_number):
        """
        Extracts parameters of a specific bin and saves them in two separate files: one "original" and one "modified".
        The extracted files are saved in a directory structure:
            circuits/<device_type>/bin_<bin_number>/bin_<bin_number>_<device_type>_original.lib
            circuits/<device_type>/bin_<bin_number>/bin_<bin_number>_<device_type>_modified.lib

        Additionally, the method prints the dimensions for the current bin and, if available, the next bin's dimensions.

        Parameters:
            bin_number (int): The bin number to extract parameters for.
        """
        # Choose the expected device string, model prefix, and dimensions table based on the device type.
        if self.device_type == 'nch':
            device_str = 'nmos'
            bin_prefix = "sky130_fd_pr__nfet_01v8__model"
            dims = ModelExtractor.nmos_bins
        else:  # For pch
            device_str = 'pmos'
            bin_prefix = "sky130_fd_pr__pfet_01v8__model"
            dims = ModelExtractor.pmos_bins

        # Regular expression to find the start of a bin model section for the correct device type
        bin_pattern = re.compile(
            rf"\.model\s+{bin_prefix}\.{bin_number}\s+{device_str}"
        )
        param_pattern = re.compile(r"\+?\s*([\w]+)\s*=\s*(\{?[^\s\}]+\}?)")
        output_lines = []
        found_bin = False

        # Read the original file to find and extract bin parameters
        with open(self.original_file_path, 'r') as file:
            for line in file:
                # Check if this line is the start of the desired bin section
                if bin_pattern.match(line):
                    found_bin = True
                    output_lines.append(line)
                    continue

                # If we are processing the desired bin, extract parameters
                if found_bin:
                    if line.startswith("+"):
                        new_line = line
                        for param_match in param_pattern.finditer(line):
                            param_value = param_match.group(2)
                            if '{' in param_value:
                                numeric_value_match = re.match(r"\{([\d\.\-+eE]+)", param_value)
                                if numeric_value_match:
                                    param_value = numeric_value_match.group(1).rstrip("+-")
                                    new_line = new_line.replace(param_match.group(2), param_value)
                        output_lines.append(new_line)
                    # End extraction if an empty line or the next bin section is reached
                    elif not line.strip() or line.startswith(".model"):
                        break
                    else:
                        output_lines.append(line)

        if not found_bin:
            print(f"Bin {bin_number} not found in the file for device type '{self.device_type}'.")
            return

        # Prepare the output directory and file names
        output_dir = os.path.join("circuits", self.device_type, f"bin_{bin_number}")
        os.makedirs(output_dir, exist_ok=True)
        original_file_name = os.path.join(output_dir, f"bin_{bin_number}_{self.device_type}_original.lib")
        modified_file_name = os.path.join(output_dir, f"bin_{bin_number}_{self.device_type}_modified.lib")

        # Modify the first line to add an opening parenthesis and add closing parts at the end
        output_lines[0] = output_lines[0].rstrip() + " (\n"
        output_lines.append(")\n\n")
        output_lines.append(".END\n")

        # Write the extracted lines to both the original and modified files
        with open(original_file_name, 'w') as orig_file:
            orig_file.writelines(output_lines)
        with open(modified_file_name, 'w') as mod_file:
            mod_file.writelines(output_lines)

        print(f"Parameters for bin {bin_number} ({self.device_type}) have been extracted to:")
        print(f"  Original: {original_file_name}")
        print(f"  Modified: {modified_file_name}")

        # Look up dimensions for the current bin from the internal table
        if bin_number in dims:
            W_current, L_current = dims[bin_number]
            # Look for the next bin dimensions if available
            if (bin_number + 1) in dims:
                W_next, L_next = dims[bin_number + 1]
                next_info = f"bin {bin_number + 1} (W = {W_next} µm, L = {L_next} µm)"
            else:
                next_info = "no next bin"
            print(f"Bin {bin_number} is valid for dimensions: W = {W_current} µm, L = {L_current} µm, "
                  f"and these dimensions are valid until {next_info}.")
        else:
            print(f"Dimensions for bin {bin_number} are not defined in the internal table.")

    def extract_bin_parameters_by_dimensions(self, W, L, tol=1e-6):
        """
        Extracts bin parameters based on given dimensions W and L (in µm) for the specified device type.
        The method searches the internal dimensions table for an entry that matches (within a tolerance)
        the provided W and L. If found, it calls extract_bin_parameters with the corresponding bin number.

        Parameters:
            W (float): The desired transistor width in µm.
            L (float): The desired transistor length in µm.
            tol (float): Tolerance for matching floating-point values (default is 1e-6).
        """
        # Select the proper dimensions table based on the device type.
        if self.device_type == 'nch':
            dims = ModelExtractor.nmos_bins
        else:
            dims = ModelExtractor.pmos_bins

        found_bin = None
        for bin_number, (w_val, l_val) in dims.items():
            if abs(w_val - W) < tol and abs(l_val - L) < tol:
                found_bin = bin_number
                break

        if found_bin is None:
            print(f"No bin found for dimensions W = {W} µm, L = {L} µm for device type '{self.device_type}'.")
        else:
            print(f"Found bin {found_bin} for dimensions W = {W} µm, L = {L} µm.")
            self.extract_bin_parameters(found_bin)


# Example usage:
# if __name__ == '__main__':
#     # For NMOS extraction by bin number:
#     original_model_file_nch = "sky130_fd_pr__nfet_01v8.pm3.spice"
#     extractor_nch = ModelExtractor(original_model_file_nch, device_type='nch')
#     extractor_nch.extract_bin_parameters(0)
#
#     # For NMOS extraction by dimensions:
#     # Example: Extract the bin for W = 1.26 µm, L = 0.15 µm
#     extractor_nch.extract_bin_parameters_by_dimensions(1.26, 0.15)
#
#     # For PMOS extraction by dimensions (uncomment when ready and ensure correct original file):
#     # original_model_file_pch = "sky130_fd_pr__pfet_01v8_modified.pm3.spice"
#     # extractor_pch = ModelExtractor(original_model_file_pch, device_type='pch')
#     # extractor_pch.extract_bin_parameters_by_dimensions(1.26, 0.15)
