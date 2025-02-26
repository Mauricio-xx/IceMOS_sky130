# TODO

- we need to fix the netlist generation for PMOS based on new xschem netlist's

## Plotting and Data Analysis
- **IV Simulation Plotting:**
  - [x] Implement interactive IV plotting using PyQtGraph.
  - [ ] Develop interactive plotting for IV VDS simulation results.

## Parameter Modification and Simulation Loop
- **Automated Parameter Modification:**
  - Find bin model to be modified (verify if modifications have already been applied).
  - Modify desired parameters, save, simulate, plot, and repeat.
  - (Optional: Add a GUI for interactive parameter tuning.)

## Netlist Verification
- **Manual Simulation in xschem:**
  - Simulate selected transistor circuits in xschem.
  - Verify that the generated netlists are logically correct.
  - Document any discrepancies and update netlist generation logic accordingly.

## PMOS Support and Testing
- Continue refining and validating PMOS (PCH) netlist generation and simulation.
- Extend test coverage for PMOS scenarios.
