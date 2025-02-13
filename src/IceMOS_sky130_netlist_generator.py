import os
import re
from IceMOS_sky130_circuit_model_extractor import ModelExtractor

class NetlistGeneratorSky130:
    def __init__(self, original_model_file):
        """
        Initialize the netlist generator with the path to the original SPICE model file.

        :param original_model_file: Path to the original SPICE model file.
        """
        self.original_model_file = original_model_file

    def _find_bin_by_dimensions(self, W, L, device_type, tol=1e-6):
        """
        Look up the bin number for the given W and L (in µm) based on the internal dictionaries.

        :param W: Desired transistor width (µm).
        :param L: Desired transistor length (µm).
        :param device_type: 'nch' for NMOS or 'pch' for PMOS.
        :param tol: Tolerance for floating-point comparison.
        :return: The matching bin number, or None if not found.
        """
        if device_type.lower() == 'nch':
            dims = ModelExtractor.nmos_bins
        else:
            dims = ModelExtractor.pmos_bins

        for bin_number, (w_val, l_val) in dims.items():
            if abs(w_val - W) < tol and abs(l_val - L) < tol:
                return bin_number
        return None

    def _ensure_model_extracted(self, device_type, bin_number):
        """
        Ensure that the modified model file for the given bin exists.
        If not, call the ModelExtractor to extract the bin.

        :param device_type: 'nch' or 'pch'.
        :param bin_number: The bin number.
        """
        folder = os.path.join("circuits", device_type, f"bin_{bin_number}")
        model_filename = f"bin_{bin_number}_{device_type}_modified.lib"
        model_filepath = os.path.join(folder, model_filename)
        if not os.path.exists(model_filepath):
            print(f"Model file {model_filepath} not found. Extracting bin {bin_number}...")
            extractor = ModelExtractor(self.original_model_file, device_type=device_type)
            extractor.extract_bin_parameters(bin_number)
        else:
            print(f"Model file {model_filepath} exists.")

    def generate_iv_netlists(self, device_type, bin_number=None, W=None, L=None,
                             vgate_start=0, vgate_stop=1.8, vgate_step=0.1):
        """
        Generates two IV simulation netlists (IDRAIN vs. VGATE): one that uses the ORIGINAL model and
        one that uses the MODIFIED model.

        The netlists are generated based on a provided bin number or dimensions (W and L).
        If the bin number is not provided, the appropriate bin is determined from the dimensions.

        The generated netlists are saved as:
            circuits/<device_type>/bin_<bin_number>/netlist_IV_bin_<bin_number>_original.spice
            circuits/<device_type>/bin_<bin_number>/netlist_IV_bin_<bin_number>_modified.spice

        :param device_type: 'nch' for NMOS or 'pch' for PMOS.
        :param bin_number: (Optional) The bin number to use.
        :param W: (Optional) Transistor width in µm (if bin_number is not provided).
        :param L: (Optional) Transistor length in µm (if bin_number is not provided).
        :param vgate_start: Start voltage for VGATE sweep.
        :param vgate_stop: End voltage for VGATE sweep.
        :param vgate_step: Step voltage for VGATE sweep.
        :return: A dictionary with keys 'original' and 'modified' containing the file paths of the generated netlists.
        """
        device_type = device_type.lower()
        # Determine the bin number based on dimensions if not provided.
        if bin_number is None:
            if W is None or L is None:
                raise ValueError("Either bin_number or both W and L must be provided.")
            bin_number = self._find_bin_by_dimensions(W, L, device_type)
            if bin_number is None:
                raise ValueError(f"No bin found for dimensions W={W} µm, L={L} µm for device {device_type}.")
            else:
                print(f"Found bin {bin_number} for dimensions W={W} µm, L={L} µm.")
        else:
            print(f"Using provided bin number: {bin_number}")

        # Ensure the model file for this bin exists; if not, extract it.
        self._ensure_model_extracted(device_type, bin_number)

        # Determine the model name and filenames for both original and modified models.
        if device_type == 'nch':
            model_name = f"sky130_fd_pr__nfet_01v8__model.{bin_number}"
            original_model_filename = f"bin_{bin_number}_nch_original.lib"
            modified_model_filename = f"bin_{bin_number}_nch_modified.lib"
        else:
            model_name = f"sky130_fd_pr__pfet_01v8__model.{bin_number}"
            original_model_filename = f"bin_{bin_number}_pch_original.lib"
            modified_model_filename = f"bin_{bin_number}_pch_modified.lib"

        # Prepare include lines for both netlists.
        include_line_original = f'.include "./{original_model_filename}"\n'
        include_line_modified = f'.include "./{modified_model_filename}"\n'

        # Netlist template with a header comment indicating the model type.
        template = """{include_line}
.option verbose=1

* IV Simulation netlist for device {device_type} using {model_type} model
* Model: {model_name}
* Parameter definitions for device dimensions
.param nf=1
.param w=1
.param l=0.15

* Voltage source for gate bias (VGATE)
VGATE_src net1 GND 0

* MOSFET instance using the defined parameters
M1 net2 net1 0 0 {model_name} L={{l}} W={{w}} nf={{nf}}
+ad={{int((nf+1)/2)*w/nf*0.29}} as={{int((nf+2)/2)*w/nf*0.29}}
+pd={{2*int((nf+1)/2)*(w/nf+0.29)}} ps={{2*int((nf+2)/2)*(w/nf+0.29)}}
+nrd={{0.29/w}} nrs={{0.29/w}} sa=0 sb=0 sd=0 m=1

* Voltage source for the drain (V1) and measurement element
V1 V1 GND 1.8
V1_meas V1 net2 0

.save i(V1_meas)

.control
  save all
  * Perform DC sweep for VGATE_src from {vgate_start} V to {vgate_stop} V in steps of {vgate_step} V
  dc VGATE_src {vgate_start} {vgate_stop} {vgate_step}
  write IV_nmos.raw
  wrdata IV_nmos.csv I(V1)
  showmod M1
.endc

.param mc_mm_switch=0
.param mc_pr_switch=0
.include /foss/pdks/sky130A/libs.tech/ngspice/corners/tt.spice
.include /foss/pdks/sky130A/libs.tech/ngspice/r+c/res_typical__cap_typical.spice
.include /foss/pdks/sky130A/libs.tech/ngspice/r+c/res_typical__cap_typical__lin.spice
.include /foss/pdks/sky130A/libs.tech/ngspice/corners/tt/specialized_cells.spice

.GLOBAL GND
.end
"""
        # Generate netlist contents for both original and modified.
        netlist_original = template.format(
            include_line=include_line_original,
            device_type=device_type,
            model_type="ORIGINAL",
            model_name=model_name,
            vgate_start=vgate_start,
            vgate_stop=vgate_stop,
            vgate_step=vgate_step
        )

        netlist_modified = template.format(
            include_line=include_line_modified,
            device_type=device_type,
            model_type="MODIFIED",
            model_name=model_name,
            vgate_start=vgate_start,
            vgate_stop=vgate_stop,
            vgate_step=vgate_step
        )

        # Prepare the output directory and filenames.
        output_dir = os.path.join("circuits", device_type, f"bin_{bin_number}")
        os.makedirs(output_dir, exist_ok=True)
        netlist_original_filename = f"netlist_IV_bin_{bin_number}_original.spice"
        netlist_modified_filename = f"netlist_IV_bin_{bin_number}_modified.spice"
        netlist_original_filepath = os.path.join(output_dir, netlist_original_filename)
        netlist_modified_filepath = os.path.join(output_dir, netlist_modified_filename)

        with open(netlist_original_filepath, 'w') as f:
            f.write(netlist_original)
        with open(netlist_modified_filepath, 'w') as f:
            f.write(netlist_modified)

        print(f"IV netlists generated and saved to:")
        print(f"  Original netlist: {netlist_original_filepath}")
        print(f"  Modified netlist: {netlist_modified_filepath}")

        return {"original": netlist_original_filepath, "modified": netlist_modified_filepath}

    def generate_iv_vds_netlists(self, device_type, bin_number=None, W=None, L=None,
                                 vgs_start=0, vgs_stop=1.8, vgs_step=0.6,
                                 vds_start=0, vds_stop=1.8, vds_step=0.1):
        """
        Generates two IV simulation netlists (IDRAIN vs. VDRAIN with a VGATE sweep) for the specified device.
        The netlist uses a control loop that sweeps VGATE (alias VGS) from vgs_start to vgs_stop in steps of vgs_step.
        For each VGATE value, it performs a DC sweep on VDRAIN from vds_start to vds_stop in steps of vds_step,
        and saves the measurement data to a CSV file.

        The netlists are generated based on either a provided bin number or dimensions (W and L).
        If the bin number is not provided, it is determined from the dimensions.

        The generated netlists are saved as:
            circuits/<device_type>/bin_<bin_number>/netlist_IV_VDS_bin_<bin_number>_original.spice
            circuits/<device_type>/bin_<bin_number>/netlist_IV_VDS_bin_<bin_number>_modified.spice

        :param device_type: 'nch' for NMOS or 'pch' for PMOS.
        :param bin_number: (Optional) The bin number to use.
        :param W: (Optional) Transistor width in µm (if bin_number is not provided).
        :param L: (Optional) Transistor length in µm (if bin_number is not provided).
        :param vgs_start: Starting value for VGS (in V) sweep.
        :param vgs_stop: Ending value for VGS (in V) sweep.
        :param vgs_step: Step increment for VGS sweep.
        :param vds_start: Starting value for VDS (in V) sweep (inside the loop).
        :param vds_stop: Ending value for VDS (in V) sweep.
        :param vds_step: Step increment for VDS sweep.
        :return: A dictionary with keys 'original' and 'modified' containing the file paths of the generated netlists.
        """
        device_type = device_type.lower()
        # Determine the bin number based on dimensions if not provided
        if bin_number is None:
            if W is None or L is None:
                raise ValueError("Either bin_number or both W and L must be provided.")
            bin_number = self._find_bin_by_dimensions(W, L, device_type)
            if bin_number is None:
                raise ValueError(f"No bin found for dimensions W={W} µm, L={L} µm for device {device_type}.")
            else:
                print(f"Found bin {bin_number} for dimensions W={W} µm, L={L} µm.")
        else:
            print(f"Using provided bin number: {bin_number}")

        # Ensure the model file for this bin exists; if not, extract it.
        self._ensure_model_extracted(device_type, bin_number)

        # Determine the model name and filenames for both original and modified models.
        if device_type == 'nch':
            model_name = f"sky130_fd_pr__nfet_01v8__model.{bin_number}"
            original_model_filename = f"bin_{bin_number}_nch_original.lib"
            modified_model_filename = f"bin_{bin_number}_nch_modified.lib"
        else:
            model_name = f"sky130_fd_pr__pfet_01v8__model.{bin_number}"
            original_model_filename = f"bin_{bin_number}_pch_original.lib"
            modified_model_filename = f"bin_{bin_number}_pch_modified.lib"

        # Prepare include lines for both netlists (assumes netlist is saved in same folder as model file).
        include_line_original = f'.include "./{original_model_filename}"\n'
        include_line_modified = f'.include "./{modified_model_filename}"\n'

        # Ensure that the sweep_IV_results folder exists in the output directory.
        output_dir = os.path.join("circuits", device_type, f"bin_{bin_number}")
        os.makedirs(output_dir, exist_ok=True)
        sweep_results_dir = os.path.join(output_dir, "sweep_IV_results")
        os.makedirs(sweep_results_dir, exist_ok=True)

        # Template for IV vs VDS simulation netlist.
        # Note: Removed 'mult=1' from the MOSFET instance.
        vds_template = """{include_line}
.option verbose=1

* IV VDS Simulation netlist for device {device_type} using {model_type} model
* Model: {model_name}
* Parameter definitions for device dimensions
.param nf=1
.param w=1
.param l=0.15

* MOSFET instance using the defined parameters
M1 net1 VGS GND GND {model_name} L=1 W=1 nf=1 ad='int((nf+1)/2)*W/nf*0.29' as='int((nf+2)/2)*W/nf*0.29' pd='2*int((nf+1)/2)*(W/nf+0.29)' 
+ ps='2*int((nf+2)/2)*(W/nf+0.29)' nrd='0.29/W' nrs='0.29/W' sa=0 sb=0 sd=0 m=1

VGATE VGS GND 0
VDRAIN VDS GND 0
vdsM VDS net1 0

.save i(vdsm)

.control
save all
* op
  * Initialize VGS and step
let vgsval = {vgs_start}
let step = {vgs_step}

* Sweep VGS from {vgs_start}V to {vgs_stop}V in steps of {vgs_step}V
while vgsval <= {vgs_stop}
    echo Sweeping VGS = $&vgsval
    alter VGATE = $&vgsval
    dc VDRAIN {vds_start} {vds_stop} {vds_step}
    wrdata sweep_IV_results/mosfet_vds_vs_id_{{$&vgsval}}.csv V(VDS) I(VDRAIN) I(VDSM)
    let vgsval = $&vgsval + $&step
end
write IV_IDS_vs_VDS.raw
.endc

.param mc_mm_switch=0
.param mc_pr_switch=0
.include /foss/pdks/sky130A/libs.tech/ngspice/corners/tt.spice
.include /foss/pdks/sky130A/libs.tech/ngspice/r+c/res_typical__cap_typical.spice
.include /foss/pdks/sky130A/libs.tech/ngspice/r+c/res_typical__cap_typical__lin.spice
.include /foss/pdks/sky130A/libs.tech/ngspice/corners/tt/specialized_cells.spice

.GLOBAL GND
.end
"""

        # Generate netlist contents for both original and modified models.
        netlist_original = vds_template.format(
            include_line=include_line_original,
            device_type=device_type,
            model_type="ORIGINAL",
            model_name=model_name,
            vgs_start=vgs_start,
            vgs_stop=vgs_stop,
            vgs_step=vgs_step,
            vds_start=vds_start,
            vds_stop=vds_stop,
            vds_step=vds_step
        )

        netlist_modified = vds_template.format(
            include_line=include_line_modified,
            device_type=device_type,
            model_type="MODIFIED",
            model_name=model_name,
            vgs_start=vgs_start,
            vgs_stop=vgs_stop,
            vgs_step=vgs_step,
            vds_start=vds_start,
            vds_stop=vds_stop,
            vds_step=vds_step
        )

        # Prepare the output directory and filenames.
        output_dir = os.path.join("circuits", device_type, f"bin_{bin_number}")
        os.makedirs(output_dir, exist_ok=True)
        netlist_original_filename = f"netlist_IV_VDS_bin_{bin_number}_original.spice"
        netlist_modified_filename = f"netlist_IV_VDS_bin_{bin_number}_modified.spice"
        netlist_original_filepath = os.path.join(output_dir, netlist_original_filename)
        netlist_modified_filepath = os.path.join(output_dir, netlist_modified_filename)

        with open(netlist_original_filepath, 'w') as f:
            f.write(netlist_original)
        with open(netlist_modified_filepath, 'w') as f:
            f.write(netlist_modified)

        print(f"IV VDS netlists generated and saved to:")
        print(f"  Original netlist: {netlist_original_filepath}")
        print(f"  Modified netlist: {netlist_modified_filepath}")

        return {"original": netlist_original_filepath, "modified": netlist_modified_filepath}


# Example usage:
# if __name__ == '__main__':
#     # Path to the original model file (without "modified" in its name)
#     original_model_file = "sky130_fd_pr__nfet_01v8.pm3.spice"
#
#     # Create an instance of the netlist generator.
#     generator = NetlistGeneratorSky130(original_model_file)
#
#     # Option 1: Generate netlists by providing a bin number.
#     generator.generate_iv_netlists(device_type='nch', bin_number=0, vgate_start=0, vgate_stop=1.8, vgate_step=0.1)
#
#     # Option 2: Generate netlists by providing dimensions.
#     # For example, for NMOS with W=1.26 µm, L=0.15 µm:
#     # generator.generate_iv_netlists(device_type='nch', W=1.26, L=0.15, vgate_start=0, vgate_stop=1.8, vgate_step=0.1)
#
#     # Similarly, for PMOS, use device_type='pch' and appropriate dimensions.
#
