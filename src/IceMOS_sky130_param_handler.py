import re
import os

class ModelModifier:
    """
    A class to modify parameters within a specified SPICE model file.

    Attributes
    ----------
    original_file_path : str
        The path to the original SPICE model file.
    modified_file_path : str
        The path to the modified SPICE model file.
    data : dict
        A dictionary containing the parsed model parameters for each bin.

    Methods
    -------
    parse_parameters(file_path)
        Parses the SPICE model file and extracts parameters for each bin.
    modify_parameter(bin_number, param_name, new_value)
        Modifies the value of a specific parameter in a given bin.
    update_bin_in_file(bin_number)
        Updates the content of a specific bin in the modified file.
    modify_line(line, bin_number)
        Modifies a line of parameters within a bin and returns the updated line.
    """

    def __init__(self, original_file_path, modified_file_path):
        """
        Initializes the ModelModifier with paths to the original and modified files.
        
        Parameters
        ----------
        original_file_path : str
            The path to the original SPICE model file.
        modified_file_path : str
            The path to the modified SPICE model file.
        """
        self.original_file_path = original_file_path
        self.modified_file_path = modified_file_path
        self.data = self.parse_parameters(original_file_path)

        if not os.path.exists(self.modified_file_path):
            with open(self.original_file_path, 'r') as original, open(self.modified_file_path, 'w') as modified:
                modified.write(original.read())

    def parse_parameters(self, file_path):
        """
        Parses the SPICE model file and extracts parameters for each bin.

        Parameters
        ----------
        file_path : str
            The path to the SPICE model file to be parsed.

        Returns
        -------
        dict
            A dictionary where keys are bin numbers and values are dictionaries of parameters.
        """
        bin_pattern = re.compile(r"\.model\s+sky130_fd_pr__nfet_01v8__model\.(\d+)\s+(nmos|pmos)")
        param_pattern = re.compile(r"([\w]+)\s*=\s*(\{?[^\s\}]+\}?)")

        data = {}
        current_bin = None

        with open(file_path, 'r') as file:
            for line in file:
                bin_match = bin_pattern.match(line)
                if bin_match:
                    current_bin = int(bin_match.group(1))
                    data[current_bin] = {}
                    continue

                if current_bin is not None:
                    for param_match in param_pattern.finditer(line):
                        param_name = param_match.group(1)
                        param_value = param_match.group(2)
                        
                        if param_value.startswith('{'):
                            numeric_part = re.search(r'\{([^\+\-]+[eE][\+\-]?\d+)', param_value)
                            if numeric_part:
                                extra_data = param_value.replace(numeric_part.group(1), '').strip('{}')
                                data[current_bin][param_name] = {'value': numeric_part.group(1), 'extra': extra_data}
                        else:
                            data[current_bin][param_name] = {'value': param_value, 'extra': ''}
        return data

    def modify_parameter(self, bin_number, param_name, new_value):
        """
        Modifies the value of a specific parameter in a given bin.

        Parameters
        ----------
        bin_number : int
            The bin number where the parameter is located.
        param_name : str
            The name of the parameter to be modified.
        new_value : str
            The new value to assign to the parameter.
        """
        if bin_number in self.data and param_name in self.data[bin_number]:
            self.data[bin_number][param_name]['value'] = new_value
            self.update_bin_in_file(bin_number)

    def update_bin_in_file(self, bin_number):
        """
        Updates the content of a specific bin in the modified file.

        Parameters
        ----------
        bin_number : int
            The bin number to update in the file.
        """
        temp_file_path = self.modified_file_path + '.tmp'

        with open(self.modified_file_path, 'r') as original, open(temp_file_path, 'w') as temp_file:
            inside_bin = False

            for line in original:
                if f".model sky130_fd_pr__nfet_01v8__model.{bin_number}" in line:
                    inside_bin = True
                    temp_file.write(line)
                    continue

                if inside_bin and line.startswith('.model'):
                    inside_bin = False

                if inside_bin:
                    if re.search(r'\+', line):
                        modified_line = self.modify_line(line, bin_number)
                        temp_file.write(modified_line + "\n")
                    else:
                        temp_file.write(line)
                else:
                    temp_file.write(line)

        os.replace(temp_file_path, self.modified_file_path)

    def modify_line(self, line, bin_number):
        """
        Modifies a line of parameters within a bin and returns the updated line.

        Parameters
        ----------
        line : str
            The line from the SPICE model file to be modified.
        bin_number : int
            The bin number that contains the line.

        Returns
        -------
        str
            The modified line with the updated parameter value.
        """
        param_pattern = re.compile(r"([\w]+)\s*=\s*(\{?[^\s\}]+\}?)")
        modified_parts = []

        for param_match in param_pattern.finditer(line):
            param_name = param_match.group(1)
            if param_name in self.data[bin_number]:
                value_data = self.data[bin_number][param_name]
                new_value = f"{param_name}={{{value_data['value']}{value_data['extra']}}}" if value_data['extra'] else f"{param_name}={value_data['value']}"
                modified_parts.append(new_value)
            else:
                modified_parts.append(param_match.group(0))

        return '+ ' + ' '.join(modified_parts)
        
        
# Uso de ejemplo
#original_file_path = 'sky130_fd_pr__nfet_01v8.pm3.spice'
#modified_file_path = 'sky130_fd_pr__nfet_01v8_modified.pm3.spice'

#modifier = ModelModifier(original_file_path, modified_file_path)

# Modificar parámetros específicos en una línea con múltiples parámetros
#modifier.modify_parameter(0, 'lmin', '1.1123e-07')
#modifier.modify_parameter(0, 'lmax', '1.2134e-06')
#modifier.modify_parameter(1, 'wmin', '2.3145e-07')
#modifier.modify_parameter(1, 'wmax', '3.4156e-06')

# Modificar solo la parte numérica de un parámetro con extra_data en {}
#modifier.modify_parameter(0, 'lint', '2.3145e-008')

