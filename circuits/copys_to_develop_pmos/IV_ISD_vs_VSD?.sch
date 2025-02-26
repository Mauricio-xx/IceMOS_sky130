v {xschem version=3.4.6 file_version=1.2}
G {}
K {}
V {}
S {}
E {}
N 120 -80 120 -60 {
lab=GND}
N -140 -130 -140 -100 {
lab=VGS}
N -50 -130 -50 -100 {
lab=VSD}
N 120 -100 120 -80 {
lab=GND}
N 120 -130 170 -130 {lab=#net1}
N 170 -160 170 -150 {lab=#net1}
N 160 -160 170 -160 {lab=#net1}
N 140 -160 160 -160 {lab=#net1}
N 130 -160 140 -160 {lab=#net1}
N 120 -160 130 -160 {lab=#net1}
N 120 -160 130 -160 {lab=#net1}
N 170 -150 170 -130 {lab=#net1}
C {devices/vsource.sym} -140 -70 0 0 {name=VGATE value=0 savecurrent=false}
C {devices/vsource.sym} -50 -70 0 0 {name=VSOURCE value=0 savecurrent=false}
C {devices/gnd.sym} -140 -40 0 0 {name=l1 lab=GND}
C {devices/gnd.sym} -50 -40 0 0 {name=l2 lab=GND}
C {devices/gnd.sym} 120 -60 0 0 {name=l3 lab=GND}
C {devices/lab_pin.sym} -140 -130 0 0 {name=p1 sig_type=std_logic lab=VGS
}
C {devices/lab_pin.sym} -50 -130 0 0 {name=p2 sig_type=std_logic lab=VSD
}
C {devices/lab_pin.sym} 80 -130 0 0 {name=p3 sig_type=std_logic lab=VGS
}
C {devices/lab_pin.sym} 120 -220 0 0 {name=p4 sig_type=std_logic lab=VSD}
C {devices/code_shown.sym} 240 -270 0 0 {name=s1 only_toplevel=false value="

*.control
*save all 
*op
    * VDS sweep and VGS sweep
*    dc VDRAIN 0 1.8 0.01 VGATE 0 1.8 0.6
    * Save the results
*    wrdata mosfet_vds_vs_is.csv V(VGS) I(VDRAIN)
*.endc



.control
save all 
op
  * Barrido de VGS de 0V a 1.8V en pasos de 0.6V
  foreach vgs 0 0.1 0.2 0.3 0.4 0.5 0.6 1.2 1.8
    * Cambiar VGS a $vgs
    alter VGATE dc=$vgs
    * Barrido de VSD de 0V a 1.8V en pasos de 0.1V
    dc VSOURCE 0 1.8 0.1
    * Guardar los resultados en un archivo
    wrdata mosfet_vsd_vs_is_\{$vgs\}.csv V(VGS) I(VSOURCE) I(vsdM)
    
  end
write IV_ISD_vs_VSD.raw 
.endc

"


}
C {sky130_fd_pr/corner.sym} 240 -470 0 0 {name=CORNER only_toplevel=true corner=tt}
C {devices/ammeter.sym} 120 -190 0 0 {name=vsdM  current=5.0094e-04}
C {sky130_fd_pr/pfet_01v8.sym} 100 -130 0 0 {name=M2
W=1
L=0.15
nf=1
mult=1
ad="'int((nf+1)/2) * W/nf * 0.29'" 
pd="'2*int((nf+1)/2) * (W/nf + 0.29)'"
as="'int((nf+2)/2) * W/nf * 0.29'" 
ps="'2*int((nf+2)/2) * (W/nf + 0.29)'"
nrd="'0.29 / W'" nrs="'0.29 / W'"
sa=0 sb=0 sd=0
model=pfet_01v8
spiceprefix=X
}
