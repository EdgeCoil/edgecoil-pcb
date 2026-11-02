* SPDX-FileCopyrightText: 2026 edgecoil
* SPDX-License-Identifier: CERN-OHL-S-2.0
* rtc-pcf85063a: PCF85063A RTC (U9) with its crystal (Y1) and backup: C51, a 0.22 F 5.5 V EDLC (hand-fitted; part not
* chosen), charged from 3V3 through R52 100 ohm and a BAV170 (D2, both diodes in parallel), so it cannot drain back
* into a dead rail. Ports as block.json. As in the source board's simulation, the RTC (uA), its crystal and C50
* (100n beside 0.22 F) are not modelled: what matters on 3V3 is the EDLC's charging current (~24 mA when empty,
* tau 22 s), and on VRTC the hold-up.
* c51/c51esr: the EDLC (0 ohm ESR is the heaviest 3V3 load); irtc: the RTC's backup current (0 as in the source
* board's simulation; its datasheet: 0.50 uA max at 50 C, CLKOUT off); ileak: the EDLC's own leakage (unknown until a
* part is chosen); both fold back below 0.5 V. Start C51 empty (uic) for plug-in.
.include ../models.inc
.subckt rtc_pcf85063a 3v3 gnd scl sda params: k_r52=1 c51=0.22 c51esr=0 irtc=0 ileak=0
R52 3v3 3v3_rtc {100*k_r52}
D2a 3v3_rtc vrtc DBAV170
D2b 3v3_rtc vrtc DBAV170
C51 c51x gnd {c51}
Resr51 vrtc c51x {max(c51esr,1e-3)}
Bld vrtc gnd I = ({irtc}+{ileak})*min(1, max(0, V(vrtc,gnd)/0.5))
Rlk_3v3_rtc 3v3_rtc gnd 1e9
Rlk_vrtc vrtc gnd 1e9
.ends rtc_pcf85063a
