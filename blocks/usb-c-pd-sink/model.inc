* SPDX-FileCopyrightText: 2026 edgecoil
* SPDX-License-Identifier: CERN-OHL-S-2.0
* usb-c-pd-sink: HUSB238_002DD PD sink (U3) with its VIN capacitor (C20 1u), ISET 10.5k (R20: 2 A) and VSET 14.0k (R21:
* 15 V on its own). Ports as block.json. As in the source board's simulation: the HUSB238 is its VIN current (3.1 mA)
* and the 100 uA it sources into VSET and ISET once VIN is up; the PD negotiation is not modelled (the bench sets
* VBUS), nor are CC1, CC2, SDA and SCL (signals: ports only, no element here).
* The request is VSET's pin voltage, 100 uA x the resistance the board puts there: 1.400 V = 14.0k = 15 V alone; the
* source board's 10.7k across it (its 9 V switch position) gives 0.606 V = 6.06k, the 9 V code (6.04k).
* cink: C20's tolerance x temperature multiplier (0.8-1.1 in the Monte Carlo); vop_bus: its DC-bias point, the
* contract voltage (5, 9 or 15 V); k_r20/k_r21: resistor tolerance; iset_ua: the pins' source current (+-5 %).
.include ../models.inc
.subckt usb_c_pd_sink cc1 cc2 gnd scl sda vbus vset params: iset_ua=100 cink=1 vop_bus=9 k_r20=1 k_r21=1
XC20 vbus gnd MLCC c0=1.06e-06 v0=7.1 m=1.8 k={cink} esr=20m vop={vop_bus}
R20 iset gnd {10500*k_r20}
R21 vset gnd {14000*k_r21}
XU3 vbus vset iset gnd HUSB238 iset_ua={iset_ua}
Rlk_iset iset gnd 1e9
.ends usb_c_pd_sink
