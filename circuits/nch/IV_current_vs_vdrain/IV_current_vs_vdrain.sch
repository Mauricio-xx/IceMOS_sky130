v {xschem version=3.4.5 file_version=1.2
}
G {}
K {}
V {}
S {}
E {}
N 170 -210 290 -210 {
lab=#net1}
N 330 -160 330 -150 {
lab=GND}
N 330 -180 330 -160 {
lab=GND}
N 330 -170 370 -170 {
lab=GND}
N 370 -210 370 -180 {
lab=GND}
N 330 -210 370 -210 {
lab=GND}
N 370 -180 370 -170 {
lab=GND}
N 520 -270 530 -270 {
lab=V1}
N 530 -270 530 -240 {
lab=V1}
N 330 -260 330 -240 {
lab=#net2}
C {devices/vsource.sym} 170 -180 0 0 {name=VGATE value=0 savecurrent=false}
C {devices/gnd.sym} 330 -150 0 0 {name=l1 lab=GND}
C {devices/gnd.sym} 170 -150 0 0 {name=l2 lab=GND}
C {devices/code_shown.sym} 60 -540 0 0 {name=s1 only_toplevel=true 
value=".control
save all
op

* Perform DC sweep for V1 from 0V to 1.8V in steps of 0.1V
dc VGATE 0 1.8 0.1

*print I(v1)
write IV_nmos.raw
wrdata IV_nmos.csv I(v1)

.endc
"}
C {sky130_fd_pr/nfet_01v8.sym} 310 -210 0 0 {name=M1
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
C {sky130_fd_pr/corner.sym} 610 -410 0 0 {name=CORNER only_toplevel=true corner=tt}
C {devices/vsource.sym} 530 -210 0 0 {name=V1 value=1.8 savecurrent=false}
C {devices/gnd.sym} 530 -180 0 0 {name=l4 lab=GND}
C {devices/lab_pin.sym} 520 -270 0 0 {name=p2 sig_type=std_logic lab=V1
}
C {devices/lab_pin.sym} 330 -320 0 0 {name=p4 sig_type=std_logic lab=V1
}
C {devices/ammeter.sym} 330 -290 0 0 {name=V1_meas savecurrent=true spice_ignore=0}
