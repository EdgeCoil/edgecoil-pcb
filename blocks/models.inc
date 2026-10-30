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
