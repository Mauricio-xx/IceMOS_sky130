import pandas as pd
import matplotlib.pyplot as plt

# Lista de valores de VGS
vgs_values = [0, 0.1, 0.2,0.3,0.4,0.5, 0.6, 1.2, 1.8]

plt.figure()

# Leer y plotear cada archivo CSV
for vgs in vgs_values:
    filename = f'mosfet_vsd_vs_is_{vgs}.csv'
    data = pd.read_csv(filename, sep='\s+')
    plt.plot(data['V(VSD)'], data['I(VSDM)'], label=f'VGS = {vgs}V')

plt.title('VSD vs IS for different VGS values')
plt.xlabel('VSD [V]')
plt.ylabel('IS [A]')
plt.legend()
plt.grid(True)
plt.savefig('vsd_vs_is_for_vgsweep.pdf')
plt.show()
