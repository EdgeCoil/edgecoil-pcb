* SPDX-FileCopyrightText: 2026 edgecoil
* SPDX-License-Identifier: CERN-OHL-S-2.0
* ldo-ldl1117: LDL1117S33R with its 10u input (C1) and 22u output (C4) capacitors, C4 returned to ground
* through R25 (0 ohm link fitted; 0.1-0.47 ohm if 3V3 rings). Ports as block.json.
* r25: the link, ASSUMED 5 mohm (no typical given; the sim6 sweep took 50 mohm as its maximum); set it to the fitted swap value.
* Corners (the board simulation's): typ as defaults; worst vr=3.201 rdo=0.50 rlr=0.0125 iq=500u ilim=1.5
* gp=5 wi=1.4e6 tau=0.2u; high vr=3.399. c1v: C1's DC-bias operating point (5 V; 9 V brackets plug-in ringing).
.include ../models.inc
.subckt ldo_ldl1117 vbus 3v3 gnd params: vr=3.3 rdo=0.36 rlr=0.0042 iq=250u ilim=2.0 gp=7 wi=2e6 tau=0.15u
+ tss=50u c1k=1 c4k=1 c1v=5.0 r25=5m
XU5 vbus 3v3 gnd LDL1117 vr={vr} rdo={rdo} ilim={ilim} iq={iq} gp={gp} wi={wi} tau={tau} tss={tss} rlr={rlr}
XC1 vbus gnd MLCC c0=1.095e-05 v0=5.0 m=1.75 k={c1k} esr=8.5m vop={c1v}
XC4 3v3 c4_esr MLCC c0=2.02e-05 v0=5.0 m=1.75 k={c4k} esr=4.7m vop=3.3
R25 c4_esr gnd {r25}
.ends ldo_ldl1117
