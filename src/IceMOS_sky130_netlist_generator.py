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
        Generates IV simulation netlists (ID vs. VG) using the extracted model.
        The results are written to folder "results_IV_ID_vs_VG".
        For NMOS, the template used is:

            .option verbose=1
            * IV Simulation netlist for device {device_type} using {model_type} model
            * Model: {model_name}
            .param nf=1
            .param w={W_val}
            .param l={L_val}
            VGATE_src net1 GND 0
            M1 net2 net1 0 0 {model_name} L=l W=w nf=1 ad='int((nf+1)/2)*W/nf*0.29' as='int((nf+2)/2)*W/nf*0.29'
            +pd='2*int((nf+1)/2)*(W/nf+0.29)' ps='2*int((nf+2)/2)*(W/nf+0.29)' nrd='0.29/W' nrs='0.29/W' sa=0 sb=0 sd=0
            V1 V1 GND 1.8
            V1_meas V1 net2 0

            .save i(V1_meas)
            .control
              save all
              dc VGATE_src {vgate_start} {vgate_stop} {vgate_step}
              write results_IV_ID_vs_VG/IV_ID_vs_VG.raw
              wrdata results_IV_ID_vs_VG/IV_ID_vs_VG.csv I(V1)
              *showmod M1
            .endc
            ... (includes)
            .GLOBAL GND
            .end

        For PMOS, the template is:

            .option verbose=1
            * IV Simulation netlist for device {device_type} using {model_type} model
            * Model: {model_name}
            .param nf=1
            .param w={W_val}
            .param l={L_val}
            VGATE net1 VGATE 0
            vdsM VDRAIN GND 0
            .save i(vdsm)
            M2 VDRAIN VGATE net1 net1 {model_name} L=l W=w nf=1 ad='int((nf+1)/2)*W/nf*0.29' as='int((nf+2)/2)*W/nf*0.29'
            + pd='2*int((nf+1)/2)*(W/nf+0.29)' ps='2*int((nf+2)/2)*(W/nf+0.29)' nrd='0.29/W' nrs='0.29/W' sa=0 sb=0 sd=0 m=1
            VDD net1 GND 1.8
            .control
              save all
              op
              dc VGATE {vgate_start} {vgate_stop} {vgate_step}
              wrdata results_IV_ID_vs_VG/p_mosfet_id_vs_vg.csv I(vdsM)
              write results_IV_ID_vs_VG/IV_ID_vs_VG.raw
            .endc
            ... (includes)
            .GLOBAL GND
            .end

        :return: Dictionary with paths for 'original' and 'modified' netlists.
        """
        device_type = device_type.lower()
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

        if W is None or L is None:
            dims = ModelExtractor.nmos_bins if device_type == 'nch' else ModelExtractor.pmos_bins
            if bin_number in dims:
                W_val, L_val = dims[bin_number]
            else:
                raise Exception(f"No dimensions found for bin {bin_number}.")
        else:
            W_val, L_val = W, L

        self._ensure_model_extracted(device_type, bin_number)

        if device_type == 'nch':
            model_name = f"sky130_fd_pr__nfet_01v8__model.{bin_number}"
            original_model_filename = f"bin_{bin_number}_nch_original.lib"
            modified_model_filename = f"bin_{bin_number}_nch_modified.lib"
            include_line_original = f'.include "./{original_model_filename}"\n'
            include_line_modified = f'.include "./{modified_model_filename}"\n'
            temp_for_sim = 27
            iv_template = """{include_line}
.option verbose=1

*set temperature for simulation
*if this file is 'ORIGINAL' temp is set to 27C
*if this file is 'MODIFIED' temp is -269C (4K)
.temp {temp_for_sim}

* IV Simulation netlist for device {device_type} using {model_type} model
* Model: {model_name}
.param nf=1
.param w={W_val}
.param l={L_val}

VGATE_src net1 GND 0
M1 net2 net1 0 0 {model_name} L={L_val} W={W_val} nf=1 ad='int((nf+1)/2)*W/nf*0.29' as='int((nf+2)/2)*W/nf*0.29'
+pd='2*int((nf+1)/2)*(W/nf+0.29)' ps='2*int((nf+2)/2)*(W/nf+0.29)' nrd='0.29/W' nrs='0.29/W' sa=0 sb=0 sd=0
V1 V1 GND 1.8
V1_meas V1 net2 0
.save i(V1_meas)

.control
  save all
  dc VGATE_src {vgate_start} {vgate_stop} {vgate_step}
  write results_IV_ID_vs_VG/IV_ID_vs_VG.raw
  wrdata results_IV_ID_vs_VG/IV_ID_vs_VG.csv I(V1_meas)
  *showmod M1
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
        else:
            # PMOS IV vs VG template:
            model_name = f"sky130_fd_pr__pfet_01v8__model.{bin_number}"
            original_model_filename = f"bin_{bin_number}_pch_original.lib"
            modified_model_filename = f"bin_{bin_number}_pch_modified.lib"
            include_line_original = f'.include "./{original_model_filename}"\n'
            include_line_modified = f'.include "./{modified_model_filename}"\n'
            temp_for_sim = 27
            iv_template = """{include_line}
.option verbose=1

*set temperature for simulation
*if this file is 'ORIGINAL' temp is set to 27C
*if this file is 'MODIFIED' temp is -269C (4K)
.temp {temp_for_sim}

* IV Simulation netlist for device {device_type} using {model_type} model
* Model: {model_name}
.param nf=1
.param w={W_val}
.param l={L_val}

VGATE net1 VGATE 0
vdsM VDRAIN GND 0
.save i(vdsm)

M2 VDRAIN VGATE net1 net1 {model_name} L={L_val} W={W_val} nf=1 ad='int((nf+1)/2)*W/nf*0.29' as='int((nf+2)/2)*W/nf*0.29'
+ pd='2*int((nf+1)/2)*(W/nf+0.29)' ps='2*int((nf+2)/2)*(W/nf+0.29)' nrd='0.29/W' nrs='0.29/W' sa=0 sb=0 sd=0 m=1
VDD net1 GND 1.8

.control
save all
op
  dc VGATE {vgate_start} {vgate_stop} {vgate_step}
  wrdata results_IV_ID_vs_VG/IV_ID_vs_VG.csv I(vdsM)
  write results_IV_ID_vs_VG/IV_ID_vs_VG.raw
  *showmod M2
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
        if device_type == 'nch':
            netlist_original = iv_template.format(
                include_line=include_line_original,
                device_type=device_type,
                model_type="ORIGINAL",
                model_name=model_name,
                W_val=W_val,
                L_val=L_val,
                vgate_start=vgate_start,
                vgate_stop=vgate_stop,
                vgate_step=vgate_step,
                temp_for_sim = 27
            )
            netlist_modified = iv_template.format(
                include_line=include_line_modified,
                device_type=device_type,
                model_type="MODIFIED",
                model_name=model_name,
                W_val=W_val,
                L_val=L_val,
                vgate_start=vgate_start,
                vgate_stop=vgate_stop,
                vgate_step=vgate_step,
                temp_for_sim = -269
            )
        else:
            netlist_original = iv_template.format(
                include_line=include_line_original,
                device_type=device_type,
                model_type="ORIGINAL",
                model_name=model_name,
                W_val=W_val,
                L_val=L_val,
                vgate_start=vgate_start,
                vgate_stop=vgate_stop,
                vgate_step=vgate_step,
                temp_for_sim = 27
            )
            netlist_modified = iv_template.format(
                include_line=include_line_modified,
                device_type=device_type,
                model_type="MODIFIED",
                model_name=model_name,
                W_val=W_val,
                L_val=L_val,
                vgate_start=vgate_start,
                vgate_stop=vgate_stop,
                vgate_step=vgate_step,
                temp_for_sim = -269
            )
        output_dir = os.path.join("circuits", device_type, f"bin_{bin_number}")
        os.makedirs(output_dir, exist_ok=True)
        results_iv_dir = os.path.join(output_dir, "results_IV_ID_vs_VG")
        os.makedirs(results_iv_dir, exist_ok=True)
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
        iv_dict = {"original": netlist_original_filepath, "modified": netlist_modified_filepath}

        return iv_dict

    def generate_iv_vds_netlists(self, device_type, bin_number=None, W=None, L=None,
                                 vgs_start=0, vgs_stop=1.8, vgs_step=0.6,
                                 vds_start=0, vds_stop=1.8, vds_step=1.0,   # todo: extend to vsg
                                 vsd_start=None, vsd_stop=None, vsd_step=None):
        """
        Generates IV VDS simulation netlists for the specified device.
        For NMOS, the simulation is of ID vs. VDS with a VG sweep.
        For PMOS, the simulation is of ID vs. VSD with a VG sweep.
        Results are written into the folder "results_IV_ID_vs_VDS_for_VG_sweep".

        For NMOS, the template uses variables:
          {vgs_start}, {vgs_stop}, {vgs_step} for the VG sweep.
        For PMOS, the template uses:
          {vgs_start}, {vgs_stop}, {vgs_step} for the VG sweep, and
          {vsd_start}, {vsd_stop}, {vsd_step} for the VSD sweep.
        These last three variables must be provided by the user.
        """
        device_type = device_type.lower()
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
        if W is None or L is None:
            dims = ModelExtractor.nmos_bins if device_type == 'nch' else ModelExtractor.pmos_bins
            if bin_number in dims:
                W_val, L_val = dims[bin_number]
            else:
                raise Exception(f"No dimensions defined for bin {bin_number}.")
        else:
            W_val, L_val = W, L
        self._ensure_model_extracted(device_type, bin_number)
        if device_type == 'nch':
            model_name = f"sky130_fd_pr__nfet_01v8__model.{bin_number}"
            original_model_filename = f"bin_{bin_number}_nch_original.lib"
            modified_model_filename = f"bin_{bin_number}_nch_modified.lib"
            include_line_original = f'.include "./{original_model_filename}"\n'
            include_line_modified = f'.include "./{modified_model_filename}"\n'
            vds_prefix = "n_mosfet_id_vs_vsd_"
            temp_for_sim = 27
            vds_template = """{include_line}
.option verbose=1

*set temperature for simulation
*if this file is 'ORIGINAL' temp is set to 27C
*if this file is 'MODIFIED' temp is -269C (4K)
.temp {temp_for_sim}

* IV VDS Simulation netlist for NMOS using {model_type} model
* Model: {model_name}
.param nf=1
.param w={W_val}
.param l={L_val}

M1 net1 VGS GND GND {model_name} L={L_val} W={W_val} nf=1 ad='int((nf+1)/2)*w/nf*0.29' as='int((nf+2)/2)*w/nf*0.29'
+pd='2*int((nf+1)/2)*(w/nf+0.29)' ps='2*int((nf+2)/2)*(w/nf+0.29)' nrd='0.29/w' nrs='0.29/w' sa=0 sb=0 sd=0
VGATE VGS GND 0
VDRAIN VDS GND 0
vdsM VDS net1 0

.save i(vdsm)

.control
save all
let vgsval = {vgs_start}
let step = {vgs_step}
while vgsval <= {vgs_stop}
    echo Sweeping VGS = $&vgsval
    alter VGATE = $&vgsval
    dc VDRAIN {vds_start} {vds_stop} {vds_step}
    wrdata results_IV_IDS_vs_VDS_for_VG_sweep/{vds_prefix}{{$&vgsval}}.csv V(VDS) I(VDRAIN) I(VDSM)
    write results_IV_IDS_vs_VDS_for_VG_sweep/{vds_prefix}{{$&vgsval}}.raw
    let vgsval = $&vgsval + $&step
end

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
        else:
            # For PMOS:
            model_name = f"sky130_fd_pr__pfet_01v8__model.{bin_number}"
            original_model_filename = f"bin_{bin_number}_pch_original.lib"
            modified_model_filename = f"bin_{bin_number}_pch_modified.lib"
            include_line_original = f'.include "./{original_model_filename}"\n'
            include_line_modified = f'.include "./{modified_model_filename}"\n'
            vds_prefix = "p_mosfet_id_vs_vsd_"
            temp_for_sim = 27
            vds_template = """{include_line}
.option verbose=1

*set temperature for simulation
*if this file is 'ORIGINAL' temp is set to 27C
*if this file is 'MODIFIED' temp is -269C (4K)
.temp {temp_for_sim}


* IV VSD with VG sweep simulation netlist for device {device_type} using {model_type} model
* Model: {model_name}
.param nf=1
.param w={W_val}
.param l={L_val}

VGATE net1 VGATE 0
VSOURCE net1 net2 0
vdsM VDRAIN net2 0
.save i(vdsm)
M2 VDRAIN VGATE net1 net1 {model_name} L={L_val} W={W_val} nf=1 ad='int((nf+1)/2)*W/nf*0.29' as='int((nf+2)/2)*W/nf*0.29'
+ pd='2*int((nf+1)/2)*(W/nf+0.29)' ps='2*int((nf+2)/2)*(W/nf+0.29)' nrd='0.29/W' nrs='0.29/W' sa=0 sb=0 sd=0 m=1
VDD net1 GND 1.8

.control
save all
let vgsval = {vgs_start}
let step = {vgs_step}
while vgsval <= {vgs_stop}
    echo Sweeping VGS = $&vgsval
    alter VGATE dc=$&vgsval
    dc VSOURCE {vsd_start} {vsd_stop} {vsd_step}
    wrdata results_IV_ISD_vs_VSD_for_VG_sweep/{vds_prefix}{{$&vgsval}}.csv V(VGATE) I(VSOURCE) I(vdsM)
    write results_IV_ISD_vs_VSD_for_VG_sweep/{vds_prefix}{{$&vgsval}}.raw
    let vgsval = $&vgsval + $&step
end
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
        if device_type == 'nch':
            netlist_original = vds_template.format(
                include_line=include_line_original,
                model_type="ORIGINAL",
                model_name=model_name,
                W_val=W_val,
                L_val=L_val,
                vgs_start=vgs_start,
                vgs_stop=vgs_stop,
                vgs_step=vgs_step,
                vds_start=vds_start,
                vds_stop=vds_stop,
                vds_step=vds_step,
                vds_prefix=vds_prefix,
                temp_for_sim = 27
            )
            netlist_modified = vds_template.format(
                include_line=include_line_modified,
                model_type="MODIFIED",
                model_name=model_name,
                W_val=W_val,
                L_val=L_val,
                vgs_start=vgs_start,
                vgs_stop=vgs_stop,
                vgs_step=vgs_step,
                vds_start=vds_start,
                vds_stop=vds_stop,
                vds_step=vds_step,
                vds_prefix=vds_prefix,
                temp_for_sim = -269,
            )
        else:
            netlist_original = vds_template.format(
                include_line=include_line_original,
                device_type=device_type,
                model_type="ORIGINAL",
                model_name=model_name,
                W_val=W_val,
                L_val=L_val,
                vgs_start=vgs_start,
                vgs_stop=vgs_stop,
                vgs_step=vgs_step,
                vsd_start=vsd_start,
                vsd_stop=vsd_stop,
                vsd_step=vsd_step,
                vds_prefix=vds_prefix,
                temp_for_sim = 27
            )
            netlist_modified = vds_template.format(
                include_line=include_line_modified,
                device_type=device_type,
                model_type="MODIFIED",
                model_name=model_name,
                W_val=W_val,
                L_val=L_val,
                vgs_start=vgs_start,
                vgs_stop=vgs_stop,
                vgs_step=vgs_step,
                vsd_start=vsd_start,
                vsd_stop=vsd_stop,
                vsd_step=vsd_step,
                vds_prefix=vds_prefix,
                temp_for_sim = -269
            )
        output_dir = os.path.join("circuits", device_type, f"bin_{bin_number}")
        os.makedirs(output_dir, exist_ok=True)

        # results dir will be different for or nmos

        if device_type == 'nch': results_vds_dir = os.path.join(output_dir, "results_IV_IDS_vs_VDS_for_VG_sweep")
        else: results_vds_dir = os.path.join(output_dir, "results_IV_ISD_vs_VSD_for_VG_sweep")
        os.makedirs(results_vds_dir, exist_ok=True)

        if device_type == 'nch':
            netlist_original_filename = f"netlist_IV_VDS_bin_{bin_number}_original.spice"
            netlist_modified_filename = f"netlist_IV_VDS_bin_{bin_number}_modified.spice"
        else:
            netlist_original_filename = f"netlist_IV_VSD_bin_{bin_number}_original.spice"
            netlist_modified_filename = f"netlist_IV_VSD_bin_{bin_number}_modified.spice"

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
