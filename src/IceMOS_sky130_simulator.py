import subprocess
import os
class IceMOSSky130BatchSimulator:
    def __init__(self, netlist_path):
        """
        Initialize the simulator with the path to the netlist.

        :param netlist_path: Path to the SPICE netlist file (e.g., 'IV_nmos.spice').
        """
        self.netlist_path = netlist_path

    def simulate(self):
        """
        Run the simulation by calling ngspice in batch mode using the command:
        ngspice -b <netlist_path>
        """
        command = ['ngspice', '-b', self.netlist_path]
        print(f"Running simulation with command: {' '.join(command)}")
        try:
            result = subprocess.run(
                command,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                universal_newlines=True,
                check=True
            )
            print("ngspice stdout:")
            print(result.stdout)
            print("ngspice stderr:")
            print(result.stderr)
        except subprocess.CalledProcessError as e:
            print("Error during ngspice simulation:")
            print(e.stderr)
            raise RuntimeError("Simulation failed.")


# Example usage:
if __name__ == '__main__':
    # Path to your netlist file (e.g., 'IV_nmos.spice' or 'IV_nmos.sch')
    netlist_file = '/foss/designs/Endurance_Cryo_ToolBox/src/exp/sky130/Prototype_codes/sky130_custom_model_sim/nch/IV_nmos.spice'

    # Create an instance of the simulator and run the simulation
    simulator = IceMOSSky130BatchSimulator(netlist_file)
    simulator.simulate()
