* SPDX-FileCopyrightText: 2026 edgecoil
* SPDX-License-Identifier: CERN-OHL-S-2.0
* buck-ap63203: AP63203WU fixed 3.3 V buck (U5) from VBUS, its input capacitors (C40 4.7u 25 V, C41 100n), the
* output capacitors (C43, C44 22u), with L1 (4.7u, Isat 4 A) and the bootstrap C42 inside the averaged model (as in
* the source board's simulation: the inductor current is a PI-controlled source, input current = output power /
* (VIN x eta); no 1.1 MHz ripple). FB is tied to 3V3 at the pin. Ports as block.json.
* Parameters (the source board's Monte Carlo): vref (VFB) 3.27-3.33; ilim_b (IPEAK) 2.5-3.1; gp/wi the loop
* (ASSUMED, crossover ~fsw/20); cink (C40, C41 tolerance x temperature) and vop_bus (their DC-bias point: 5, 9, 15 V);
* cok (C43, C44).
.include ../models.inc
.subckt buck_ap63203 3v3 gnd vbus params: vref=3.3 gp=9 wi=6e5 ilim_b=2.5 cink=1 cok=1 vop_bus=9
XC40 vbus gnd MLCC c0=4.6e-06 v0=7 m=1.7 k={cink} esr=10m vop={vop_bus}
XC41 vbus gnd MLCC c0=1e-07 v0=20 m=1.5 k={cink} esr=30m vop={vop_bus}
XC43 3v3 gnd MLCC c0=2.02e-05 v0=5.0 m=1.75 k={cok} esr=4.7m vop=3.3
XC44 3v3 gnd MLCC c0=2.02e-05 v0=5.0 m=1.75 k={cok} esr=4.7m vop=3.3
XU5 vbus 3v3 3v3 gnd AP63203 vref={vref} gp={gp} wi={wi} ilim={ilim_b}
.ends buck_ap63203
