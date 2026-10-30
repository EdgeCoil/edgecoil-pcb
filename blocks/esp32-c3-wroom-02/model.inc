* SPDX-FileCopyrightText: 2026 edgecoil
* SPDX-License-Identifier: CERN-OHL-S-2.0
* esp32-c3-wroom-02: the module's supply and reset side: C5 10u at its 3V3 pin, the EN RC (R6 10k, C6 1u),
* the IO8 and IO2 pull-ups (R7, R9 10k), the module's own decoupling (datasheet: 10u + 100n on VDD33;
* its 10u taken as 3.0-5u at 3.3 V, cmod) and its supply current. Ports as block.json; the GPIO ports
* other than the straps are signals and carry only 2 pF here.
* iload: a voltage source between iload and gnd whose value is the module's current in amps (e.g. a PWL
* of Wi-Fi bursts: 84 mA RX shoulder, 345 mA TX peak, 0.5 us edges, datasheet Table 6-4). gate=1: the chip
* draws ~1 uA until EN > 0.75 VDD and VDD > 2.5 V (an assumed brown-out level; the spec minimum is 3.0 V);
* gate=0 draws it regardless (pessimistic for sag tests). IO9 has its 45k internal pull-up.
.include ../models.inc
.subckt esp32_c3_wroom_02 3v3 gnd en io2 io8 io9 iload params: c5k=1 c6k=1 cmod=4.5u gate=1
XC5 3v3 gnd MLCC c0=1.007e-05 v0=2.9 m=1.7 k={c5k} esr=10.9m vop=3.3
XC6 en gnd MLCC c0=1.06e-06 v0=7.1 m=1.8 k={c6k} esr=20m vop=3.3
R6 3v3 en 10000
R7 3v3 io8 10000
R9 3v3 io2 10000
Cmod 3v3 cmx {cmod}
Rcm cmx gnd 10m
Cmod2 3v3 gnd 100n
Besp 3v3 gnd I = ({gate} > 0.5 ? (1u + (V(iload,gnd)-1u)*0.25*(1+tanh((V(en,gnd)-0.75*V(3v3,gnd))/0.02))*(1+tanh((V(3v3,gnd)-2.5)/0.02))) : V(iload,gnd))*max(0,min(1,V(3v3,gnd)/0.5))
Rio9 3v3 io9 45k
Cio9 io9 gnd 2p
Cio8 io8 gnd 2p
Cio2 io2 gnd 2p
Cen en gnd 2p
Desden en 3v3 DESD
.model DESD D(IS=1e-14 N=1.2 RS=50)
.ends esp32_c3_wroom_02
