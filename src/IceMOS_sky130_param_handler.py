"""Edit selected parameters without changing other bins or model expressions."""

from pathlib import Path

from IceMOS_sky130_model_io import atomic_write, model_blocks, parameters, patch_bin


class ModelModifier:
    def __init__(self, original_file_path, modified_file_path, device_type='nch'):
        self.original_file_path = str(original_file_path)
        self.modified_file_path = str(modified_file_path)
        self.device_type = device_type.lower()
        if Path(original_file_path).resolve() == Path(modified_file_path).resolve():
            raise ValueError('Choose a separate modified model file')
        self.data = self.parse_parameters(original_file_path)
        if not Path(modified_file_path).exists():
            atomic_write(modified_file_path, Path(original_file_path).read_text())

    def parse_parameters(self, file_path):
        text = Path(file_path).read_text()
        return {number: {key: {'value': value, 'extra': ''}
                         for key, value in parameters(text[start:end]).items()}
                for number, (start, end) in model_blocks(text, self.device_type).items()}

    def modify_parameter(self, bin_number, param_name, new_value):
        self.modify_parameters(bin_number, {param_name: new_value})

    def modify_parameters(self, bin_number, updates):
        text = Path(self.modified_file_path).read_text()
        result = patch_bin(text, self.device_type, bin_number, updates)
        atomic_write(self.modified_file_path, result)
        self.data = self.parse_parameters(self.modified_file_path)
