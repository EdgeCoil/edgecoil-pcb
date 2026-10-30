* SPDX-FileCopyrightText: 2026 edgecoil
* SPDX-License-Identifier: CERN-OHL-S-2.0
* usb-c-power: HRO TYPE-C-31-M-12 receptacle, 5.1k CC pull-downs (R1, R2: a sink, 5 V only), SRV05-4 ESD
* on D+/D- with its rail on 3V3 (U2). Ports as block.json. The receptacle itself is ideal.
* usb_charger_cable is what makes VBUS ring at plug-in: a charger (vsrc behind rsrc, current-limited at
* ilim, 220u/30 mohm output) and a cable (round-trip rcab, loop lcab), the contact closing at t_on over
* 10 ns. Cables simulated: stiff 5m/50n, 0.3 m thick 50m/250n, 1 m 200m/700n, 2 m thick 340m/1.4u,
* 2 m thin 850m/1.4u (ohm/H; 0.7 uH/m loop ASSUMED).
.include ../models.inc
.subckt usb_c_power 3v3 gnd usb_dn usb_dp vbus params: u2ilk=0
R1 cc1 gnd 5100
R2 cc2 gnd 5100
XU2 usb_dp usb_dn usb_dn 3v3 gnd SRV05_4 ilk={u2ilk}
.ends usb_c_power
.subckt usb_charger_cable vbus gnd params: t_on=0 vsrc=5.0 rcab=0.2 lcab=0.7u rsrc=0.02 ilim=3.0
Vusb usbs gnd {vsrc}
Bchg usbs us0 I = {ilim}*tanh(V(usbs,us0)/({ilim}*{rsrc}))
Cchg us0 cq 220u
Rcq cq gnd 0.03
Rcab us0 u1 {rcab}
Lcab u1 u2 {lcab}
Ru2 u2 gnd 1meg
Bsw u2 vbus I = V(u2,vbus)*(1e-9 + 100*min(1, max(0, (time-{t_on})/10n)))
.ends usb_charger_cable
