v {xschem version=3.4.5 file_version=1.2
}
G {}
K {}
V {}
S {}
E {}
N 130 -120 250 -120 {
lab=#net1}
N 290 -70 290 -60 {
lab=GND}
N 290 -90 290 -70 {
lab=GND}
N 290 -80 330 -80 {
lab=GND}
N 330 -120 330 -90 {
lab=GND}
N 290 -120 330 -120 {
lab=GND}
N 330 -90 330 -80 {
lab=GND}
N 480 -180 490 -180 {
lab=V1}
N 490 -180 490 -150 {
lab=V1}
N 290 -170 290 -150 {
lab=#net2}
C {devices/vsource.sym} 130 -90 0 0 {name=VGATE value=0 savecurrent=false}
C {devices/gnd.sym} 290 -60 0 0 {name=l1 lab=GND}
C {devices/gnd.sym} 130 -60 0 0 {name=l2 lab=GND}
C {devices/code_shown.sym} 0 -470 0 0 {name=s1 only_toplevel=true 
value=".control
save all
*op
*write  IV_nmos.raw

* Perform DC sweep for V1 from 0V to 1.8V in steps of 0.1V
dc VGATE 0 1.8 0.1

*print I(v1)

write IV_nmos.raw
wrdata IV_nmos.csv I(v1)


.endc
"}
C {sky130_fd_pr/nfet_01v8.sym} 270 -120 0 0 {name=M1
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
C {sky130_fd_pr/corner.sym} 570 -320 0 0 {name=CORNER only_toplevel=true corner=tt}
C {devices/vsource.sym} 490 -120 0 0 {name=V1 value=1.8 savecurrent=false}
C {devices/gnd.sym} 490 -90 0 0 {name=l4 lab=GND}
C {devices/lab_pin.sym} 480 -180 0 0 {name=p2 sig_type=std_logic lab=V1
}
C {devices/lab_pin.sym} 290 -230 0 0 {name=p4 sig_type=std_logic lab=V1
}
C {devices/ammeter.sym} 290 -200 0 0 {name=V1_meas savecurrent=true spice_ignore=0}
