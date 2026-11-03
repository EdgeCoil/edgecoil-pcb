* SPDX-FileCopyrightText: 2026 edgecoil
* SPDX-License-Identifier: CERN-OHL-S-2.0
* buck-ap63203 (rev B): AP63203WU fixed 3.3 V buck (U5) from VBUS, its input capacitors (C40 4.7u 50 V X7R 1206,
* C41 100n 50 V), the output capacitors (C43, C44 22u), with L1 (4.7u, Isat 4 A) and the bootstrap C42 inside the
* averaged model (as in the source board's simulation: the inductor current is a PI-controlled source, input current =
* output power / (VIN x eta); no 1.1 MHz ripple, no PFM). Lumped: FB is tied to 3V3 at the pin, and the block's copper
* (C43 -> FB 18.9 mohm, L1.2 -> C43 0.8 mohm, C43 -> C44 1.3 mohm, C41 -> U5 1.9 mohm, C40 -> C41 2.3 mohm in the
* source board's extraction) is left out. Ports as block.json.
* Parameters (the source board's Monte Carlo): vref (VFB) 3.27-3.33; ilim_b (IPEAK) 2.5-3.1; gp/wi the loop
* (ASSUMED, crossover ~fsw/20; between the 'slow' gp 4 / wi 2e5 and 'nom' 9 / 6e5 fits); cink (C40, C41 tolerance x
* temperature, 0.80-1.10) and vop_bus (their DC-bias point: 5 V before a contract, 12 or 15 V after; 15 V the
* default, rev B's contract); cok (C43, C44: 0.72-1.20).
* U5's UVLO is the model's typical 3.5 V rising / 0.44 V hysteresis (guaranteed rising 3.3-3.7 V), and its dropout is
* ignored: neither matters above the 4.44 V minimum simulated.
* C40's DC-bias curve (c0 4.7u, v0 19.2, m 1.63: 0.90x at 5 V, 0.60x at 15 V) is ASSUMED, as in the source board.
.include ../models.inc
.subckt buck_ap63203 3v3 gnd vbus params: vref=3.3 gp=9 wi=6e5 ilim_b=2.5 cink=1 cok=1 vop_bus=15
XC40 vbus gnd MLCC c0=4.7e-06 v0=19.2 m=1.63 k={cink} esr=10m vop={vop_bus}
XC41 vbus gnd MLCC c0=1e-07 v0=20 m=1.5 k={cink} esr=30m vop={vop_bus}
XC43 3v3 gnd MLCC c0=2.02e-05 v0=5.0 m=1.75 k={cok} esr=4.7m vop=3.3
XC44 3v3 gnd MLCC c0=2.02e-05 v0=5.0 m=1.75 k={cok} esr=4.7m vop=3.3
XU5 vbus 3v3 3v3 gnd AP63203 vref={vref} gp={gp} wi={wi} ilim={ilim_b}
.ends buck_ap63203
