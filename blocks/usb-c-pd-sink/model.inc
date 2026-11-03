* SPDX-FileCopyrightText: 2026 edgecoil
* SPDX-License-Identifier: CERN-OHL-S-2.0
* usb-c-pd-sink (rev B): HUSB238_002DD PD sink (U3) with its VIN capacitor (C20 2.2u 50 V X5R 0805), ISET 20.0k
* (R20: the 2.75 or 3 A code) and VSET 14.0k as R21 13k + R22 1k in series (the 15 V code; fixed, no switch).
* Ports as block.json. As in the source board's simulation: the HUSB238 is its VIN current (3.1 mA) and the 100 uA
* it sources into VSET and ISET once VIN is up; the PD negotiation is not modelled (the bench sets VBUS), nor are
* CC1, CC2, SDA and SCL (signals: ports only, no element here).
* The request is the pins' voltage, 100 uA x the resistance there: VSET 1.400 V (14.0k, the 15 V code), ISET 2.00 V
* (20.0k, between the 2.75 A code 1.96 V and the 3 A code 2.26 V).
* cink: C20's tolerance x temperature multiplier (0.8-1.1 in the Monte Carlo); vop_bus: its DC-bias point, the
* contract voltage (5, 12 or 15 V; 15 by default); k_r20/k_r21/k_r22: resistor tolerance; iset_ua: the pins'
* source current (+-5 %).
.include ../models.inc
.subckt usb_c_pd_sink cc1 cc2 gnd scl sda vbus params: iset_ua=100 cink=1 vop_bus=15 k_r20=1 k_r21=1 k_r22=1
XC20 vbus gnd MLCC c0=2.2e-06 v0=13.3 m=1.7 k={cink} esr=15m vop={vop_bus}
R20 iset gnd {20000*k_r20}
R21 vset vset_m {13000*k_r21}
R22 vset_m gnd {1000*k_r22}
XU3 vbus vset iset gnd HUSB238 iset_ua={iset_ua}
Rlk_iset iset gnd 1e9
Rlk_vset vset gnd 1e9
Rlk_vset_m vset_m gnd 1e9
.ends usb_c_pd_sink
