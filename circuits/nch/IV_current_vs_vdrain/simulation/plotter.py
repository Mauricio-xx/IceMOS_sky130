import pandas as pd
import matplotlib.pyplot as plt

# Lista de valores de VGS
vgs_values = [0, 0.6, 1.2, 1.8]

plt.figure()

# Leer y plotear cada archivo CSV
for vgs in vgs_values:
    filename = f'mosfet_vds_vs_id_{vgs}.csv'
    data = pd.read_csv(filename, sep='\s+')
    plt.plot(data['V(VDS)'], data['I(VDSM)'], label=f'VGS = {vgs}V')

plt.title('VDS vs ID for different VGS values')
plt.xlabel('VDS [V]')
plt.ylabel('ID [A]')
plt.legend()
plt.grid(True)
plt.show()
plt.savefig('modified_vth.pdf')
