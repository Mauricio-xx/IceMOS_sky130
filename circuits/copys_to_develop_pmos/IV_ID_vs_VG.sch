v {xschem version=3.4.5 file_version=1.2
}
G {}
K {}
V {}
S {}
E {}
N -40 -70 -40 -50 {
lab=VDRAIN}
N -40 -90 -40 -70 {
lab=VDRAIN}
N -40 -120 10 -120 {lab=#net1}
N -130 -120 -80 -120 {
lab=VGATE}
N -130 -220 -130 -180 {
lab=#net1}
N -130 -220 -40 -220 {
lab=#net1}
N -40 -220 -40 -210 {
lab=#net1}
N 170 -220 170 -160 {
lab=#net1}
N -40 -220 170 -220 {
lab=#net1}
N 170 -100 170 10 {
lab=GND}
N -40 -210 -40 -150 {
lab=#net1}
N 10 -220 10 -120 {
lab=#net1}
C {devices/vsource.sym} -130 -150 0 0 {name=VGATE value=0 savecurrent=false}
C {devices/gnd.sym} 170 10 0 0 {name=l2 lab=GND}
C {devices/lab_pin.sym} -40 -50 0 0 {name=p4 sig_type=std_logic lab=VDRAIN}
C {devices/code_shown.sym} 280 -240 0 0 {name=s1 only_toplevel=false value="

.control
save all 
op
  * Barrido de VGATE de 0V a 1.8V en pasos de 0.01V

    dc VGATE 0 1.8 0.01
    * Guardar los resultados en un archivo
    wrdata p_mosfet_id_vs_vg.csv I(vdsM)
    write IV_ID_vs_VG.raw 
    
.endc

"


}
C {sky130_fd_pr/corner.sym} 280 -440 0 0 {name=CORNER only_toplevel=true corner=tt}
C {devices/ammeter.sym} -40 -20 0 0 {name=vdsM  current=5.0094e-04}
C {sky130_fd_pr/pfet_01v8.sym} -60 -120 0 0 {name=M2
W=0.5
L=0.3
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
C {devices/vsource.sym} 170 -130 0 0 {name=VDD value=1.8 savecurrent=false}
C {devices/lab_pin.sym} -130 -120 0 0 {name=p1 sig_type=std_logic lab=VGATE}
C {devices/gnd.sym} -40 10 0 0 {name=l1 lab=GND}
