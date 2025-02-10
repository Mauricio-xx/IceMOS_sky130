import re

class ModelExtractor:
    def __init__(self, original_file_path):
        """
        Initializes the ModelExtractor with the path to the original SPICE model file.
        
        Parameters:
        original_file_path (str): The path to the original SPICE model file.
        """
        self.original_file_path = original_file_path

    def extract_bin_parameters(self, bin_number):
        """
        Extracts parameters of a specific bin and saves them in a separate text file.
        
        Parameters:
        bin_number (int): The bin number to extract parameters for.
        """
        # Regular expression to find the start of a bin model section
        bin_pattern = re.compile(rf"\.model\s+sky130_fd_pr__nfet_01v8__model\.{bin_number}\s+(nmos|pmos)")
        param_pattern = re.compile(r"\+?\s*([\w]+)\s*=\s*(\{?[^\s\}]+\}?)")

        output_lines = []
        found_bin = False

        # Reading the original file to find and extract bin parameters
        with open(self.original_file_path, 'r') as file:
            for line in file:
                # Check if this line is the start of the desired bin section
                if bin_pattern.match(line):
                    found_bin = True
                    output_lines.append(line)
                    continue
                
                # If we are processing the desired bin, extract parameters
                if found_bin:
                    # Check if the line is a parameter line starting with '+'
                    if line.startswith("+"):
                        # Extract all parameters in the line
                        new_line = line
                        for param_match in param_pattern.finditer(line):
                            param_name = param_match.group(1)
                            param_value = param_match.group(2)

                            if '{' in param_value:
                                # If the parameter is enclosed in {}, extract only the numerical part with optional scientific notation
                                numeric_value_match = re.match(r"\{([\d\.\-+eE]+)", param_value)
                                if numeric_value_match:
                                    param_value = numeric_value_match.group(1).rstrip("+-")  # Remove trailing '+' or '-'
                                    # Replace the full parameter in the line with the cleaned value
                                    new_line = new_line.replace(param_match.group(2), param_value)

                        output_lines.append(new_line)
                    # End extracting if an empty line or next bin section is reached
                    elif not line.strip() or line.startswith(".model"):
                        break
                    else:
                        output_lines.append(line)

        # If the bin was not found, notify the user
        if not found_bin:
            print(f"Bin {bin_number} not found in the file.")
            return

        # Save extracted lines to a new file for the specific bin
        output_file_name = f"bin_{bin_number}_nch.model"

        # Add extra characters to the model
        output_lines[0] = output_lines[0][:-1] + ' (\n'
        output_lines.append(')\n')
        output_lines.append('\n')
        output_lines.append('.END\n')

        with open(output_file_name, 'w') as output_file:
            output_file.writelines(output_lines)
        
        print(f"Parameters for bin {bin_number} have been extracted to {output_file_name}.")



extractor = ModelExtractor("sky130_fd_pr__nfet_01v8_modified.pm3.spice")
extractor.extract_bin_parameters(0)


