// sch_path: /foss/designs/IceMOS_sky130/circuits/copys_to_develop_pmos/IV_ISD_vs_VSD?.sch
module IV_ISD_vs_VSD?
(

);
wire VSD ;
wire net1 ;
wire net2 ;
wire GND ;

vsource
#(
.value ( 0 ) ,
.savecurrent ( false )
)
VGATE ( 
 .p( net2 ),
 .m( GND )
);


vsource
#(
.value ( 0 ) ,
.savecurrent ( false )
)
VSOURCE ( 
 .p( VSD ),
 .m( GND )
);


ammeter
vsdM ( 
 .plus( VSD ),
 .minus( net1 )
);


pfet_01v8
#(
.W ( 1 ) ,
.L ( 0.15 ) ,
.nf ( 1 ) ,
.mult ( 1 ) ,
.ad ( "'int((nf+1)/2) ) ,
.pd ( "'2*int((nf+1)/2) ) ,
.as ( "'int((nf+2)/2) ) ,
.ps ( "'2*int((nf+2)/2) ) ,
.nrd ( "'0.29 ) ,
.nrs ( "'0.29 ) ,
.sa ( 0 ) ,
.sb ( 0 ) ,
.sd ( 0 ) ,
.model ( pfet_01v8 ) ,
.spiceprefix ( X )
)
M2 ( 
 .D( GND ),
 .G( net2 ),
 .S( net1 ),
 .B( net1 )
);



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
    wrdata mosfet_vsd_vs_is_{$vgs}.csv V(VGS) I(VSOURCE) I(vsdM)
    write IV_ISD_vs_VSD_{$vgs}.raw 
    
  end
write IV_ISD_vs_VSD.raw 
.endc


endmodule
