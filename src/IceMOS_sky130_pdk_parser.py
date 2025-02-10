import re

def parse_parameters(file_path):
    # Expresión regular para identificar el inicio de una sección de bin
    bin_pattern = re.compile(r"\.model\s+sky130_fd_pr__nfet_01v8__model\.(\d+)\s+(nmos|pmos)")
    
    # Expresión regular para capturar los parámetros con valores en diferentes formatos
    param_pattern = re.compile(r"\+?\s*([\w]+)\s*=\s*(\{?[^\s\}]+\}?)")
    
    # Diccionario para almacenar los datos extraídos
    data = {}
    
    current_bin = None
    
    with open(file_path, 'r') as file:
        for line_num, line in enumerate(file, 1):
            # Debug: Imprimir la línea actual
            print(f"Processing line {line_num}: {line.strip()}")
            
            # Verificar si la línea es el inicio de una nueva sección de bin
            bin_match = bin_pattern.match(line)
            if bin_match:
                current_bin = int(bin_match.group(1))
                data[current_bin] = {}
                print(f"Found new bin: {current_bin}")  # Debug: Imprimir el bin encontrado
                continue
            
            if current_bin is not None:
                # Buscar y capturar todos los parámetros en la línea
                params_found = False
                for param_match in param_pattern.finditer(line):
                    params_found = True
                    param_name = param_match.group(1)
                    param_value = param_match.group(2)
                    
                    # Debug: Imprimir el nombre y valor del parámetro encontrado
                    print(f"  Found parameter: {param_name} = {param_value}")
                    
                    # Si el valor está encapsulado dentro de {}, no recortar nada, capturarlo tal cual
                    if param_value.startswith('{'):
                        param_value = param_value.strip('{}')  # Opcional: si quieres quitar las llaves
                    
                    data[current_bin][param_name] = param_value
                
                if not params_found:
                    print(f"  No parameters found in line {line_num}")
    
    # Debug: Imprimir la estructura de datos resultante
    print("Final data structure:", data)
    return data

# Ruta al archivo de texto
file_path = 'sky130_fd_pr__nfet_01v8.pm3.spice'

# Parsear el archivo
parsed_data = parse_parameters(file_path)

# Imprimir los datos extraídos
for bin_id, params in parsed_data.items():
    print(f"Bin {bin_id}:")
    for param, value in params.items():
        print(f"  {param} = {value}")

