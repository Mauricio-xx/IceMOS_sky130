import os

# List of VGS values
vgs_values = [0, 0.1, 0.2, 0.3, 0.4, 0.5, 0.6, 0.7, 0.9, 1, 1.1, 1.2, 1.3, 1.4, 1.5, 1.6, 1.7, 1.8]

# Define column names
# remeber \s\s separator (\s+)
column_names = "V(VSD)  V(VG)  V(VSD)  I(ID)  V(VSD)  I(VSDM)\n"

# Function to add headers to a CSV file
def add_headers(filename, column_names):
    # Read the original file content
    with open(filename, 'r') as file:
        content = file.readlines()
    
    # Insert column names at the beginning of the content
    content.insert(0, column_names)
    
    # Write the modified content back to the file
    with open(filename, 'w') as file:
        file.writelines(content)

# Process each CSV file
for vgs in vgs_values:
    filename = f'p_mosfet_id_vs_vsd_{vgs}.csv'
    if os.path.exists(filename):
        add_headers(filename, column_names)
        print(f"Headers added to {filename}")
    else:
        print(f"File {filename} not found.")

