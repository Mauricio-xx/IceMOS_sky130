"""
IceMOS_sky130_param_extractor.py

This module provides functionality to extract parameter names from a BSIM model .lib file.
All parameter names are assumed to appear immediately before a " =" token.
Any leading '+' characters are ignored.
"""

import re

def extract_parameter_names(lib_file_path):
    """
    Extract a sorted list of unique parameter names from a BSIM model .lib file.

    The function reads the file line by line and uses a regular expression to capture
    all tokens that appear immediately before an equals sign. It ignores any leading '+'.
    This version handles lines with multiple parameter definitions.

    Parameters
    ----------
    lib_file_path : str
        The path to the BSIM model .lib file.

    Returns
    -------
    List[str]
        A sorted list of unique parameter names found in the file.
    """
    param_names = set()
    # Regular expression explanation:
    #   [\+\s]*   : matches optional whitespace and an optional '+' at the beginning.
    #   ([\w]+)   : captures a group of one or more word characters (the parameter name).
    #   \s*=\s*   : matches the '=' sign with optional surrounding whitespace.
    #   ([^\s]+)  : captures one or more non-whitespace characters (the parameter value).
    pattern = re.compile(r"[\+\s]*([\w]+)\s*=\s*([^\s]+)")

    with open(lib_file_path, 'r') as f:
        for line in f:
            # findall returns a list of tuples for all matches in the line
            matches = pattern.findall(line)
            for match in matches:
                param_name = match[0]
                param_names.add(param_name)

    return sorted(param_names)

def extract_parameters_with_values(lib_file_path):
    """
    Extract a dictionary of parameter names and their default values from a BSIM model .lib file.

    Each parameter is expected to be defined as (possibly multiple per line):
      + param_name = value
    The function ignores any leading '+' and returns values as floats when possible.

    Parameters
    ----------
    lib_file_path : str
        Path to the BSIM model .lib file.

    Returns
    -------
    dict
        A dictionary mapping parameter names to their default values.
    """
    param_dict = {}
    # Regular expression:
    # [\+\s]*  : Optional whitespace and '+' at the beginning.
    # ([\w]+)  : Capture one or more word characters (the parameter name).
    # \s*=\s*  : An '=' with optional spaces around.
    # ([^\s]+) : Capture the parameter value (non-whitespace characters).
    pattern = re.compile(r"[\+\s]*([\w]+)\s*=\s*([^\s]+)")
    with open(lib_file_path, 'r') as f:
        for line in f:
            matches = pattern.findall(line)
            for name, value in matches:
                try:
                    val = float(value)
                except ValueError:
                    val = value
                param_dict[name] = val
    return param_dict

# # For testing purposes:
# if __name__ == "__main__":
#     # Replace with the path to your .lib file.
#     test_lib_file = "bin_0_nch_original.lib"  # For instance, the file you provided.
#     names = extract_parameter_names(test_lib_file)
#     print("Extracted parameter names:")
#     for name in names:
#         print(name)
