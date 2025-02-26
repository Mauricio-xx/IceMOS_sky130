import pandas as pd
import matplotlib.pyplot as plt

# Lista de valores de VGS
vgs_values = [0, 0.1, 0.2, 0.3, 0.4, 0.5, 0.6, 0.7, 0.9, 1, 1.1, 1.2, 1.3, 1.4, 1.5, 1.6, 1.7, 1.8]

plt.figure()

# Leer y plotear cada archivo CSV
for vgs in vgs_values:
    filename = f'p_mosfet_id_vs_vsd_{vgs}.csv'
    data = pd.read_csv(filename, sep='\s+')
    plt.plot(data['V(VSD)'], data['I(VSDM)'], label=f'VGS = {vgs}V')

plt.title('ID vs VSD for different VG values')
plt.xlabel('VSD [V]')
plt.ylabel('ID [A]')
plt.legend()
plt.grid(True)
plt.savefig('id_vs_vsd_for_vgsweep.pdf')
plt.show()
