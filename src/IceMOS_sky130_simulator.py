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
        Run the simulation by calling ngspice in batch mode with the working directory set
        to the directory where the netlist is located.
        """
        # Determine the directory of the netlist
        netlist_dir = os.path.dirname(os.path.abspath(self.netlist_path))
        command = ['ngspice', '-b', self.netlist_path]
        print(f"Running simulation with command: {' '.join(command)}")
        print(f"Working directory: {netlist_dir}")
        try:
            result = subprocess.run(
                command,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                universal_newlines=True,
                check=True,
                cwd=netlist_dir  # Set the working directory to the netlist directory
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
    netlist_file = '/foss/designs/IceMOS_sky130/test/sky130_custom_model_sim/nch/IV_nmos.spice'
    
    # Create an instance of the simulator and run the simulation
    simulator = IceMOSSky130BatchSimulator(netlist_file)
    simulator.simulate()
