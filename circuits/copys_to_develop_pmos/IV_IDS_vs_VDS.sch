v {xschem version=3.4.5 file_version=1.2
}
G {}
K {}
V {}
S {}
E {}
N 120 -80 120 -60 {
lab=GND}
N 120 -130 160 -130 {
lab=GND}
N 160 -130 160 -80 {
lab=GND}
N 120 -80 160 -80 {
lab=GND}
N -140 -130 -140 -100 {
lab=VGS}
N -50 -130 -50 -100 {
lab=VDS}
N 120 -100 120 -80 {
lab=GND}
C {sky130_fd_pr/nfet_01v8.sym} 100 -130 0 0 {name=M1
L=0.15
W=1
nf=1 
mult=1
ad="'int((nf+1)/2) * W/nf * 0.29'" 
pd="'2*int((nf+1)/2) * (W/nf + 0.29)'"
as="'int((nf+2)/2) * W/nf * 0.29'" 
ps="'2*int((nf+2)/2) * (W/nf + 0.29)'"
nrd="'0.29 / W'" nrs="'0.29 / W'"
sa=0 sb=0 sd=0
model=nfet_01v8
spiceprefix=X
}
C {devices/vsource.sym} -140 -70 0 0 {name=VGATE value=0 savecurrent=false}
C {devices/vsource.sym} -50 -70 0 0 {name=VDRAIN value=0 savecurrent=false}
C {devices/gnd.sym} -140 -40 0 0 {name=l1 lab=GND}
C {devices/gnd.sym} -50 -40 0 0 {name=l2 lab=GND}
C {devices/gnd.sym} 120 -60 0 0 {name=l3 lab=GND}
C {devices/lab_pin.sym} -140 -130 0 0 {name=p1 sig_type=std_logic lab=VGS
}
C {devices/lab_pin.sym} -50 -130 0 0 {name=p2 sig_type=std_logic lab=VDS
}
C {devices/lab_pin.sym} 80 -130 0 0 {name=p3 sig_type=std_logic lab=VGS
}
C {devices/lab_pin.sym} 120 -220 0 0 {name=p4 sig_type=std_logic lab=VDS}
C {devices/code_shown.sym} 240 -270 0 0 {name=s1 only_toplevel=false value="

*.control
*save all 
*op
    * VDS sweep and VGS sweep
*    dc VDRAIN 0 1.8 0.01 VGATE 0 1.8 0.6
    * Save the results
*    wrdata mosfet_vds_vs_id.csv V(VGS) I(VDRAIN)
*.endc



.control
save all 
op
  * Barrido de VGS de 0V a 1.8V en pasos de 0.6V
  foreach vgs 0 0.6 1.2 1.8
    * Cambiar VGS a $vgs
    alter VGATE dc=$vgs
    * Barrido de VDS de 0V a 1.8V en pasos de 0.1V
    dc VDRAIN 0 1.8 0.1
    * Guardar los resultados en un archivo
    wrdata mosfet_vds_vs_id_\{$vgs\}.csv V(VGS) I(VDRAIN) I(vdsM)
    
  end
write IV_IDS_vs_VDS.raw 
.endc

"


}
C {sky130_fd_pr/corner.sym} 240 -470 0 0 {name=CORNER only_toplevel=true corner=tt}
C {devices/ammeter.sym} 120 -190 0 0 {name=vdsM  current=5.0094e-04}
