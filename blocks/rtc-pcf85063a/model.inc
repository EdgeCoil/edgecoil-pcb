* SPDX-FileCopyrightText: 2026 edgecoil
* SPDX-License-Identifier: CERN-OHL-S-2.0
* rtc-pcf85063a (rev B): PCF85063A RTC (U9) with its crystal (Y1) and backup: C51, a 0.47 F 5.5 V coin EDLC (optional,
* fitted by hand; no part guaranteed), charged from 3V3 through R52 100 ohm and ONE BAV170 element (D2 pin 1 -> common
* cathode; pin 2 open), so it cannot drain back into a dead rail. Ports as block.json. As in the source board's
* simulation (sim4), the RTC (uA), its crystal and C50 (100n beside 0.47 F) are not modelled, and neither is TP6 (a
* pad): what matters on 3V3 is the EDLC's charging current (~23 mA when empty, tau 47 s), and on VRTC the hold-up.
* c51/c51esr: the EDLC (0 ohm ESR is the heaviest 3V3 load; c51=1e-9 stands for "not fitted"); irtc: the RTC's backup
* current (0 as in the source board's simulation; its datasheet: 0.50 uA max at 50 C, CLKOUT off); ileak: the EDLC's
* own leakage (no generic coin cell guarantees one); both fold back below 0.5 V. Start C51 empty (uic) for plug-in.
.include ../models.inc
.subckt rtc_pcf85063a 3v3 gnd scl sda params: k_r52=1 c51=0.47 c51esr=0 irtc=0 ileak=0
R52 3v3 3v3_rtc {100*k_r52}
D2a 3v3_rtc vrtc DBAV170
C51 c51x gnd {c51}
Resr51 vrtc c51x {max(c51esr,1e-3)}
Bld vrtc gnd I = ({irtc}+{ileak})*min(1, max(0, V(vrtc,gnd)/0.5))
Rlk_3v3_rtc 3v3_rtc gnd 1e9
Rlk_vrtc vrtc gnd 1e9
.ends rtc_pcf85063a
