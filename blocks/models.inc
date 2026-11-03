* SPDX-FileCopyrightText: 2026 edgecoil
* SPDX-License-Identifier: CERN-OHL-S-2.0
* Device models shared by the blocks' model.inc files (ngspice). None is a vendor model: each is
* behavioural, fitted to the datasheet figures quoted with it, and was validated in the simulation
* of the board the blocks were cut from (plug-in ringing, Wi-Fi bursts, ESD leakage, Monte Carlo).

* MLCC with DC-bias derating, LINEAR at its operating point `vop` (a nonlinear C(V) aborted ngspice
* with 'timestep too small' at power-up). Fitted C(V) = c0/(1+(|V|/v0)^m) to Samsung's published
* DC-bias data at 25 C, max error 5 % over 0-12 V; k = tolerance x temperature multiplier:
*   CL21A106KAYNNN 10u 0805 25 V   c0 10.95u v0 5.0 m 1.75  (5.44u at 5.0 V)
*   CL21A226MAQNNN 22u 0805 25 V   c0 20.2u  v0 5.0 m 1.75  (13.7u at 3.3 V)
*   CL10A106KP8NNN 10u 0603 10 V   c0 10.07u v0 2.9 m 1.70  (4.46u at 3.3 V)
*   CL10A105KB8NNN 1u  0603 50 V   c0 1.06u  v0 7.1 m 1.80  (0.87u at 3.3 V)
.subckt MLCC a b params: c0=10u v0=5 m=1.75 k=1 esr=5m vop=3.3
* LINEAR at the DC-bias operating point vop (ngspice's C='expr' nonlinear capacitor aborted with 'timestep too small'
* in the LDO power-up; plug-in runs bracket C1 between its 5 V value and its value at the ringing peak instead)
Cx a x1 {c0*k/(1+pow(vop/v0,m))}
Rx x1 b {esr}
.ends

* LDL1117S33R (ST): 3.3 V +-3 % over -40..125 C, dropout 0.36 V typ / 0.50 V max at 1 A, current limit
* 1.5 A min, load regulation 15 mV max over 1.2 A, Iq 250 uA typ / 500 uA max, VIN abs max 20 V. Loop
* fitted to ST's load-transient figure (gp/wi/tau); tss the soft start.
.subckt LDL1117 vin vout gnd params: vr=3.3 rdo=0.36 ilim=2.0 iq=250u gp=1 wi=1e5 tau=1u tss=50u rlr=0.0042
Benb enb gnd V = 0.5*(1+tanh((V(vin,gnd)-2.3)/0.03))
Bref r0 gnd V = {vr}*V(enb,gnd)
Rss r0 refn 1k
Css refn gnd {tss/1k}
Be nr gnd V = V(refn,gnd)-V(vout,gnd)-{rlr}*V(ip,gnd)
Rf nr ne 1k
Cf ne gnd {tau/1k}
Cint ni gnd 1
Rleak ni gnd {100/wi}
Bint gnd ni I = V(enb,gnd)*{wi}*V(ne,gnd)*(V(ne,gnd) > 0 ? 0.5*(1-tanh((V(ni,gnd)-{ilim*1.05})/0.005)) : 0.5*(1+tanh(V(ni,gnd)/0.005))) - (1-V(enb,gnd))*V(ni,gnd)*1e6
Bpass vin vout I = V(enb,gnd)*max(0, min( min(V(ni,gnd) + {gp}*V(ne,gnd), {ilim}), max(V(vin,vout),0)/{rdo} ))
Bip ip gnd V = V(enb,gnd)*max(0, min( min(V(ni,gnd) + {gp}*V(ne,gnd), {ilim}), max(V(vin,vout),0)/{rdo} ))
Rip ip gnd 1meg
Bgnd vin gnd I = {iq}*0.5*(1+tanh((V(vin,gnd)-1.0)/0.2))
Dbd vout vin DLDO
.model DLDO D(IS=1e-12 N=1 RS=0.3)
Cpin vin gnd 20p
.ends

* SRV05-4 (ProTek's parameter table, the one vendor figure available): steering diodes to vp and gnd per
* line, a 6 V avalanche diode vp-gnd; ilk/ilkio leakage (5 uA max at 5 V on the datasheet).
.subckt SRV05_4 io1 io2 io3 vp gnd params: ilk=0 ilkio=0
D1p io1 vp LCRD
D1n gnd io1 LCRD
D2p io2 vp LCRD
D2n gnd io2 LCRD
D3p io3 vp LCRD
D3n gnd io3 LCRD
Dz gnd vp ABD
Blk vp gnd I = {ilk}*V(vp,gnd)/5
Blk1 io1 gnd I = {ilkio}*V(io1,gnd)/5
Blk2 io2 gnd I = {ilkio}*V(io2,gnd)/5
Blk3 io3 gnd I = {ilkio}*V(io3,gnd)/5
.model LCRD D(BV=200 IBV=0.01u CJO=3p IS=1e-13 VJ=0.6 M=0.33 N=1 RS=0.31 TT=1n)
.model ABD D(BV=6.0 IBV=1u CJO=230p IS=1e-11 VJ=0.6 M=0.33 N=1 RS=0.014 TT=1n)
.ends

* ==== From the date-label-printer simulation (sim3 at rev A; rev B's sim4: post-layout, routed copper, 200 x 23 Monte
* Carlo, which added the eFuse latch fix and the AO3400A below), for the
* usb-c-pd-sink, efuse-tps25947, buck-ap63203 and rtc-pcf85063a blocks. Each is that harness's model with its ground
* made a pin (gnd) in place of node 0; otherwise unchanged. ngspice treats a node named gnd as ground, so in use that
* pin is node 0 (as for LDL1117 above); renamed and held 2 V above node 0 in a check, the ports matched the originals
* (eFuse network to 1e-10 V, HUSB238 to 1e-14 V, AP63203 to 1 uV). Behavioural, fitted to the guaranteed
* datasheet figures quoted with each; ASSUMED marks a number no datasheet
* gives.

* ---------------- Schmitt state: V(st) -> 1 when V(x) > vr, -> 0 when V(x) < vf ----------------
* (a state capacitor driven to the comparator's target, which reads the state itself: hysteresis without chatter)
.subckt SCHMITT x st gnd params: vr=1.2 vf=1.09 w=0.005 tau=200n
Bst gnd st I = (( V(st,gnd) > 0.5 ? 0.5*(1+tanh((V(x,gnd)-{vf})/{w})) : 0.5*(1+tanh((V(x,gnd)-{vr})/{w})) ) - V(st,gnd)) * 1e-6/{tau}
Cst st gnd 1u
Rst st gnd 1e9
.ends SCHMITT

* ---------------- TPS259474L eFuse (TI SLVSFC9C, May 2026) ----------------
* IN 2.7-23 V operating, 28 V abs max (Table 6.1); RON 28.2 mohm typ (12 V, 3 A, 25 C), 45 max (-40..125 C).
* EN/UVLO rising 1.183/1.20/1.223, falling 1.076/1.09/1.116 V; OVLO the same thresholds (TPS259470x/4x).
* IN UVP rising 2.44-2.64 V. dVdt: SR[V/ms] = 2000 / CdVdt[pF] (Eq. 4) at IdVdt 2.21 uA typ (0.81..3.82 uA):
*   scaled here by idvdt/2.21u. 474x restarts with dVdt after OVLO (Fig 7-7), unlike 470x.
* Circuit breaker (474x): IOUT > ILIM starts ITIMER discharge (1.8 uA typ, 1.2..2.5) of CITIMER from ~2.57 V
*   through dV 1.51 V (1.286..1.741); expiry -> off, latched (L variant) until EN < VSD(F) (0.45 V) or IN cycled.
*   Fast trip at 2 x ILIM (scalable) after 500 ns (tFT is for IFT; ASSUMED the same for the scalable trip).
* ILIM = 3340/RILM A typ (1.65 k -> 2.028, 750 -> 4.452 A); min x0.888, max x1.087 (Table 6.5 rows).
* tOVLO: ASSUMED 5 us (tOVC is 5 us; the OVLO time is in the switching table).
*   (Kept as sim3 and sim4 ran it. The datasheet's timing table gives tOVLO 1.2 us typ: the model cuts later, the
*   pessimistic side.)
.subckt TPS259474 in out en ovlo gnd params: ron=0.0282 ilim=3.34 idvdt=2.21u cdvdt=3.3n citimer=10n iitimer=1.8u dvit=1.51
+ ven_r=1.20 ven_f=1.09 vov_r=1.20 vov_f=1.09
Xen en enst gnd SCHMITT vr={ven_r} vf={ven_f}
Xov ovlo ovst gnd SCHMITT vr={vov_r} vf={vov_f}
Xuv in uvst gnd SCHMITT vr=2.53 vf=2.42 w=0.01
* shutdown below VSD(F) clears the latch
Bsd sdn gnd V = 0.5*(1+tanh((V(en,gnd)-0.6)/0.02))
* on = enabled & not OV & IN above UVP & not latched
Bon on gnd V = V(enst,gnd)*(1-V(ovst,gnd))*V(uvst,gnd)*(1-V(lat,gnd))
Ron0 on gnd 1e9
* slew-limited gate reference: rises at SR, follows IN when on; discharges at once when off
Bramp gnd rmp I = V(on,gnd) > 0.5 ? min({idvdt/2.21u*2000/(cdvdt*1e12)*1e3}, max(-1e6, (V(in,gnd)-V(rmp,gnd))*1e6))*1e-6 : -V(rmp,gnd)*1e-3
Crmp rmp gnd 1u
Rrmp rmp gnd 1e9
* pass FET: source follower on the ramp, limited by RON
Bsw in out I = V(on,gnd)*max(0, min((V(in,gnd)-V(out,gnd))/{ron}, 50*(V(rmp,gnd)-V(out,gnd))))
* circuit-breaker timer: V(tmr) falls from 0 while over ILIM at iitimer/citimer, recovers fast below it (ASSUMED)
Bi isns gnd V = V(on,gnd)*max(0, min((V(in,gnd)-V(out,gnd))/{ron}, 50*(V(rmp,gnd)-V(out,gnd))))
Risns isns gnd 1e9
Btm gnd tmr I = (V(isns,gnd) > {ilim} ? {iitimer/citimer} : -V(tmr,gnd)*1e3) * 1u
Ctm tmr gnd 1u
Rtm tmr gnd 1e9
* latch: set by timer expiry or by > 2 x ILIM for 500 ns; reset when EN < VSD
* NOT MODELLED: after the fast trip the real part retries after a ~30 us de-glitch into current limit (ILIM) and stays
* there until ITIMER expires or thermal shutdown, then latches (SLVSFC9C 7.3.5.4, Fig. 7-11). This model latches off at
* the fast trip itself, so a hard output short's ILIM phase (up to ~16 ms with ITIMER 10 nF) is missing.
Bft gnd ftc I = (V(isns,gnd) > {2*ilim} ? 2e6 : -V(ftc,gnd)*1e7) * 1u
Cft ftc gnd 1u
Rft ftc gnd 1e9
* rev B: the latch settles in ~100 ns (it was 1e3 x 1u: 1 V/ms, so the '500 ns' fast trip took ~0.5 ms to open the
* switch; found by the source board's s8, the first check to short the output. Normal checks never set it).
* sim4: and it now holds itself once past 0.5. Before, its hold branch was 0, so a fast trip that ended ~100 ns into the
* opening (the current below 2 x ILIM, ftc discharging) froze the latch near 0.99: U4 stayed ~1 % on and fed ~6 A into a
* short for good, loading VBUS through the ring (found by sim4's s8 waveforms). EN below VSD still clears it.
Blat gnd lat I = ( (V(tmr,gnd) > {dvit} || V(ftc,gnd) > 1) ? (1-V(lat,gnd))*1e7 : (V(sdn,gnd) < 0.5 ? -V(lat,gnd)*1e3 : (V(lat,gnd) > 0.5 ? (1-V(lat,gnd))*1e7 : 0)) ) * 1u
Clat lat gnd 1u
Rlat lat gnd 1e12
* quiescent 610 uA max on IN
Bq in gnd I = 610u * min(1, max(0, V(in,gnd)/0.5))
.ends TPS259474

* ---------------- AP63203 buck, fixed 3.3 V (Diodes DS41300) ----------------
* VIN 3.8-32 V operating, 35 V abs max DC (40 V 400 ms); UVLO rising 3.30/3.50/3.70 V, hysteresis 440 mV typ;
* VFB (output) 3.27/3.30/3.33 V CCM; IPEAK limit 2.5/2.8/3.1 A; fSW 1.1 MHz; Iq 22 uA typ.
* Averaged model: the inductor current is a PI-controlled source (crossover ~fsw/20 ASSUMED, gp/wi below),
* clamped to [0, ilim]; input current = output power / (VIN x eta). Soft start tss ASSUMED 2 ms (not in the
* datasheet's tables). Not cycle-accurate: input ripple at 1.1 MHz is not modelled.
.subckt AP63203 vin vout fb gnd params: vref=3.3 gp=9 wi=6e5 ilim=2.5 eta=0.85 tss=2m vuv=3.5 vhys=0.44
Xuv vin uvst gnd SCHMITT vr={vuv} vf={vuv-vhys} w=0.01
Bss gnd ss I = V(uvst,gnd) > 0.5 ? (V(ss,gnd) < {vref} ? {vref/tss}*1u : 0) : -V(ss,gnd)*1e-3
Css ss gnd 1u
Rss ss gnd 1e9
* sim3: the loop regulates FB (U5 pin 1), which the board ties to 3V3 at the pin; the current goes into vout (L1.2).
* Lumped, vout = fb. With copper they are separate nodes (cu.py).
Be err gnd V = V(ss,gnd) - V(fb,gnd)
Rfb fb gnd 1e9
Bint gnd int I = V(uvst,gnd) > 0.5 ? ( (V(err,gnd) > 0 ? (V(int,gnd) < {ilim}) : (V(int,gnd) > 0)) ? {wi}*V(err,gnd)*1u : 0 ) : -V(int,gnd)*1e-3
Cint int gnd 1u
Rint int gnd 1e9
* headroom: the high-side switch can't deliver above VIN (dropout ~ IL x 0.125 ohm, ignored)
Bil il gnd V = V(uvst,gnd)*max(0, min({ilim}, {gp}*V(err,gnd) + V(int,gnd))) * min(1, max(0, (V(vin,gnd)-V(vout,gnd))/0.2))
Ril il gnd 1e9
Bout gnd vout I = V(il,gnd)
Bin vin gnd I = (V(vout,gnd)*V(il,gnd)/(max(V(vin,gnd),1)*{eta}) + 22u) * min(1, max(0, V(vin,gnd)/0.5))
.ends AP63203

* ---------------- HUSB238 VIN load (Hynetek DS rev 2.5): 3.1 mA operating ----------------
* OVP: 120 % (115..125) of the requested voltage, 50 us debounce typ (no min given); UVP disabled by default
* (002 variant); VIN 30 V abs max, CC1/CC2 25 V. Measured, not modelled: the harness reports VBUS's time
* above each threshold for comparison with the debounce.
* sim3: VSET and ISET pins: each sources 100 uA (+-5 %, [H]) into its resistor once VIN is up (ASSUMED above 3 V);
* the pin voltage is the request the board makes (VSET 0.606 V = 6.06 k = 9 V code; 1.40 V = 14.0 k = 15 V).
.subckt HUSB238 vin vset iset gnd params: iset_ua=100
Bop vin gnd I = 3.1m * min(1, max(0, V(vin,gnd)/0.5))
Bvs gnd vset I = {iset_ua}*1e-6 * 0.5*(1+tanh((V(vin,gnd)-3)/0.1))
Bis gnd iset I = {iset_ua}*1e-6 * 0.5*(1+tanh((V(vin,gnd)-3)/0.1))
.ends HUSB238

* ---------------- 2N7002 (CJ C8545; guaranteed: VDS 60 V, VGS +-20 V abs max; VGS(th) 1.0-2.5 V at 250 uA;
* RDS(on) <= 5 ohm at VGS 10 V / 500 mA and <= 7 ohm at VGS 5 V / 50 mA (CJ's table; it has NO 4.5 V row); Ciss
* <= 50 pF, Coss <= 25 pF, Crss <= 5 pF) -- level 1, kp set so RDS(on) at VGS 4.5 V, Vth 2.5 V is 7.5 ohm (kp =
* 1/(7.5 x 2.0) = 0.067; the 7.5 ohm at 4.5 V is ASSUMED, the usual 2N7002 table, not CJ's). At VGS 5 V, Vth 2.5 V
* this gives 6.0 ohm, slightly stronger than CJ's 7 ohm row; where it is used (a fail-safe pull-down sinking < 1 mA)
* only the on/off state matters. Kept as sim3/sim4 ran it. Body diode S->D. Nodes d g s.
.subckt N2N7002 d g s params: vth=1.75 kp=0.067
M1 d g s s NM L=1u W=1u
.model NM NMOS(LEVEL=1 VTO={vth} KP={kp} LAMBDA=0.01)
Cgs g s 40p
Cgd g d 5p
Cds d s 20p
Dbd s d DBODY
.model DBODY D(IS=1e-12 N=1.5 RS=0.5 CJO=10p)
Rgs g s 1e12
.ends N2N7002

* ---------------- AO3400A (AOS; JLC C20917), the efuse block's Q2 since rev B: VDS 30 V, VGS +-12 V abs max;
* VGS(th) 0.65-1.45 V at 250 uA; RDS(on) <= 48 mohm at VGS 2.5 V (3 A) -- level 1, kp so the weakest guaranteed
* device (Vth 1.45 V) has 48 mohm at VGS 2.5 V: kp = 1/(0.048 x 1.05) = 19.8 (it sinks <= 0.16 mA there, so only the
* on/off state matters). Ciss 630 pF, Coss 75 pF, Crss 50 pF typ. Body diode S->D. Nodes d g s.
.subckt NAO3400 d g s params: vth=1.05 kp=19.8
M1 d g s s NMA L=1u W=1u
.model NMA NMOS(LEVEL=1 VTO={vth} KP={kp} LAMBDA=0.01)
Cgs g s 580p
Cgd g d 50p
Cds d s 25p
Dbd s d DBODYA
.model DBODYA D(IS=1e-12 N=1.5 RS=0.05 CJO=50p)
Rgs g s 1e12
.ends NAO3400


* BAV170, one element of the dual (rtc-pcf85063a uses one): low-leakage switching diode (silicon, not Schottky).
* VF sits BETWEEN typical and Nexperia's maxima (0.9 V at 1 mA, 1.0 V at 10 mA, 1.1 V at 50 mA): the model gives
* 0.80 / 0.93 / 1.05 V there, 0.04-0.10 V below them (curve shape ASSUMED). Conservative for charging current,
* optimistic for hold-up (from 3.3 V at ~1 uA it settles VRTC at ~2.85 V): a hold-up run must start the EDLC at the
* guaranteed start voltage, not at this model's operating point. Reverse leakage (nA) not modelled.
.model DBAV170 D(IS=2e-10 N=2.0 RS=1.0 CJO=2p)
