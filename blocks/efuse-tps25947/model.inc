* SPDX-FileCopyrightText: 2026 edgecoil
* SPDX-License-Identifier: CERN-OHL-S-2.0
* efuse-tps25947: TPS259474L eFuse (U4) from VBUS to VPO with its IN capacitors (C21 1u, C22 100n), EN/UVLO divider
* 48.7k/10k from VBUS (R23/R24: on at ~7 V, never at 5 V) filtered by C23 100n, OVLO divider 76.8k/10k (R25/R26:
* 10.4 V), ILIM 1.00k (R28: 2.97-3.63 A), dVdt 4.7n (C24), ITIMER 10n (C25), the OUT capacitor C31 1u, and the
* fail-safe enable: Q1 (2N7002) holds EN low while its gate is held up from VBUS (R29/R34 100k/100k); Q2, driven from
* PEN through R30 1k and held off by R35 100k, pulls Q1's gate down. PEN high = on; PEN lost = off. Ports as block.json.
* R28, C24 and C25 are parameters of the TPS259474 model (ILIM = 3340/RILM, cdvdt, citimer), as in the source board's
* simulation; TP3 (ILM) is a test pad. OVLO is a port so a board can add resistance across R26 (the source board's
* 15 V position: 13.0k, 17.5 V).
* Parameters (the source board's Monte Carlo ranges): ron 28.2m typ / 45m max; ilimx 0.888-1.087; idvdt 0.81-3.82u;
* ven_r/vov_r 1.183-1.223, ven_f/vov_f 1.076-1.116; iitimer 1.2-2.5u; dvit 1.286-1.741; q1vth/q2vth 1.0-2.5, qkp the
* weakest 0.067; cink (C21, C22, C31 tolerance x temperature) and vop_bus (their DC-bias point: 5, 9 or 15 V); k_c23,
* k_c25, k_r23..k_r35 tolerances; rk (R23 and R25 together).
.include ../models.inc
.subckt efuse_tps25947 gnd ovlo pen vbus vpo params: ron=0.0282 ilimx=1 idvdt=2.21u ven_r=1.20 ven_f=1.09 vov_r=1.20
+ vov_f=1.09 iitimer=1.8u dvit=1.51 q1vth=1.75 q2vth=1.75 qkp=0.067 cink=1 vop_bus=9 k_c23=1 k_c25=1 rk=1
+ k_r23=1 k_r24=1 k_r25=1 k_r26=1 k_r29=1 k_r30=1 k_r34=1 k_r35=1
XC21 vbus gnd MLCC c0=1e-06 v0=20 m=1.7 k={cink} esr=15m vop={vop_bus}
XC22 vbus gnd MLCC c0=1e-07 v0=20 m=1.5 k={cink} esr=30m vop={vop_bus}
XC23 efuse_en gnd MLCC c0=1e-07 v0=20 m=1.5 k={k_c23} esr=30m vop=1.2
XC31 vpo gnd MLCC c0=1e-06 v0=20 m=1.7 k={cink} esr=15m vop={vop_bus}
XQ1 efuse_en q1_g gnd N2N7002 vth={q1vth} kp={qkp}
XQ2 q1_g q2_g gnd N2N7002 vth={q2vth} kp={qkp}
R23 vbus efuse_en {48700*k_r23*rk}
R24 efuse_en gnd {10000*k_r24}
R25 vbus ovlo {76800*k_r25*rk}
R26 ovlo gnd {10000*k_r26}
R29 vbus q1_g {100000*k_r29}
R30 pen q2_g {1000*k_r30}
R34 q1_g gnd {100000*k_r34}
R35 q2_g gnd {100000*k_r35}
XU4 vbus vpo efuse_en ovlo gnd TPS259474 ron={ron} ilim={3.34*ilimx} idvdt={idvdt} cdvdt=4.7e-09 citimer={1e-08*k_c25}
+ iitimer={iitimer} dvit={dvit} ven_r={ven_r} ven_f={ven_f} vov_r={vov_r} vov_f={vov_f}
Rlk_efuse_en efuse_en gnd 1e9
Rlk_q1_g q1_g gnd 1e9
Rlk_q2_g q2_g gnd 1e9
.ends efuse_tps25947
