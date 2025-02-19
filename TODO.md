# TODO

## Plotter and Data Processing
- **Create a Plotter Module:**
  - Develop scripts to format the raw simulation output data.
  - Implement data processing functions to handle IV and IV_VDS results.
  - Integrate these scripts into the simulator for automatic plotting of simulation results.

## Parameter Modification and Simulation Loop
- **Automated Parameter Modification:**
  - Implement functionality to identify the target bin model for modifications.
    - (e.g., check if "big bang" modifications are already applied for the bin)
  - Develop a workflow to:
    - Modify desired parameters.
    - Save the updated model.
    - Run the simulation.
    - Plot and analyze the simulation results.
    - Loop the process for iterative optimization.
  - (Optional: Develop a GUI for interactive parameter tuning.)

