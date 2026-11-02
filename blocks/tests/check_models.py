# SPDX-FileCopyrightText: 2026 edgecoil
# SPDX-License-Identifier: MIT
"""Check each block's model.inc is the circuit its block.json describes: the block subcircuit and the
same parts written out flat (as in the board simulation the models were validated in) run side by
side on one stimulus, and their waveforms must agree to 1 uV / 1 nA.

    python3 blocks/tests/check_models.py [block ...]       (needs ngspice)

This proves the wiring and parameters, not the physics: the device models in ../models.inc were
validated against their datasheets in that board simulation. Each case also carries a planted error
(a part value changed in a copy of the block's model.inc), which the comparison must catch: a check
that cannot fail proves nothing.
"""
import os
import re
import shutil
import subprocess
import sys
import tempfile

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)

# Each case: the block instance, the same parts flat (node suffix B), a stimulus driving both copies
# (each copy's nodes end in A or B), and the pairs of signals to compare.
CASES = {
    "ldo-ldl1117": dict(
        block="XA vbusA vddA 0 ldo_ldl1117",
        flat="""XU5 vbusB vddB 0 LDL1117 vr=3.3 rdo=0.36 ilim=2.0 iq=250u gp=7 wi=2e6 tau=0.15u tss=50u rlr=0.0042
XC1 vbusB 0 MLCC c0=1.095e-05 v0=5.0 m=1.75 k=1 esr=8.5m vop=5.0
XC4 vddB c4eB MLCC c0=2.02e-05 v0=5.0 m=1.75 k=1 esr=4.7m vop=3.3
R25 c4eB 0 5m""",
        stim="""XSA vbusA 0 usb_charger_cable t_on=100u rcab=0.2 lcab=0.7u
XSB vbusB 0 usb_charger_cable t_on=100u rcab=0.2 lcab=0.7u
ILA vddA 0 PWL(0 0 1m 25m 2m 25m 2.0005m 345m 2.3m 345m 2.3005m 25m)
ILB vddB 0 PWL(0 0 1m 25m 2m 25m 2.0005m 345m 2.3m 345m 2.3005m 25m)""",
        tran="20n 3m", compare=["v(vbusA) v(vbusB)", "v(vddA) v(vddB)"]),
    "usb-c-power": dict(
        block="XA vddA 0 dnA dpA vbusA usb_c_power",
        flat="XU2 dpB dnB dnB vddB 0 SRV05_4 ilk=0",
        stim="""V3A vddA 0 3.3
V3B vddB 0 3.3
VbA vbusA 0 5
VbB vbusB 0 5
* D+ and D- driven well past both rails through 100 ohm, so the steering diodes conduct both ways
VpA spA 0 SIN(1.65 4 100k)
VpB spB 0 SIN(1.65 4 100k)
RpA spA dpA 100
RpB spB dpB 100
VnA snA 0 SIN(1.65 -4 100k)
VnB snB 0 SIN(1.65 -4 100k)
RnA snA dnA 100
RnB snB dnB 100""",
        tran="10n 20u", compare=["v(dpA) v(dpB)", "v(dnA) v(dnB)", "i(V3A) i(V3B)"]),
    "esp32-c3-wroom-02": dict(
        block="XA vddA 0 enA io2A io8A io9A ilA esp32_c3_wroom_02",
        flat="""XC5 vddB 0 MLCC c0=1.007e-05 v0=2.9 m=1.7 k=1 esr=10.9m vop=3.3
XC6 enB 0 MLCC c0=1.06e-06 v0=7.1 m=1.8 k=1 esr=20m vop=3.3
R6 vddB enB 10000
R7 vddB io8B 10000
R9 vddB io2B 10000
Cmod vddB cmxB 4.5u
Rcm cmxB 0 10m
Cmod2 vddB 0 100n
Besp vddB 0 I = (1u + (V(ilB)-1u)*0.25*(1+tanh((V(enB)-0.75*V(vddB))/0.02))*(1+tanh((V(vddB)-2.5)/0.02)))*max(0,min(1,V(vddB)/0.5))
Rio9 vddB io9B 45k
Cio9 io9B 0 2p
Cio8 io8B 0 2p
Cio2 io2B 0 2p
Cen enB 0 2p
Desden enB vddB DESD
.model DESD D(IS=1e-14 N=1.2 RS=50)""",
        stim="""* 3V3 rising over 1 ms behind 0.1 ohm, then Wi-Fi bursts once EN is up
VsA sA 0 PWL(0 0 1m 3.3)
VsB sB 0 PWL(0 0 1m 3.3)
RsA sA vddA 0.1
RsB sB vddB 0.1
VlA ilA 0 PWL(0 25m 20m 25m 20.0005m 84m 20.1m 84m 20.1005m 345m 20.4m 345m 20.4005m 25m)
VlB ilB 0 PWL(0 25m 20m 25m 20.0005m 84m 20.1m 84m 20.1005m 345m 20.4m 345m 20.4005m 25m)""",
        tran="100n 21m", compare=["v(enA) v(enB)", "v(vddA) v(vddB)", "i(VsA) i(VsB)"],
        planted=("R6 10k -> 11k", "R6 3v3 en 10000", "R6 3v3 en 11000")),
    "usb-c-pd-sink": dict(
        block="XA cc1A cc2A 0 sclA sdaA vbusA vsetA usb_c_pd_sink",
        flat="""XC20 vbusB 0 MLCC c0=1.06e-06 v0=7.1 m=1.8 k=1 esr=20m vop=9
R20 isetB 0 10500
R21 vsetB 0 14000
XU3 vbusB vsetB isetB 0 HUSB238 iset_ua=100
Rlk_iset isetB 0 1e9""",
        stim="""* VBUS 0 -> 5 V at 1 ms, the contract's 9 V at 10 ms, behind 0.1 ohm; the source board's 9 V switch (10.7k across
* VSET) closes at 6 ms; CC and I2C held by 1 Mohm (the model leaves them as ports only)
VsA sA 0 PWL(0 0 1m 0 1.5m 5 10m 5 10.5m 9)
VsB sB 0 PWL(0 0 1m 0 1.5m 5 10m 5 10.5m 9)
RsA sA vbusA 0.1
RsB sB vbusB 0.1
R22A vsetA swA 10700
R22B vsetB swB 10700
BswA swA 0 I = V(swA)*(time > 6m ? 20 : 1e-9)
BswB swB 0 I = V(swB)*(time > 6m ? 20 : 1e-9)
Rc1 cc1A 0 1meg
Rc2 cc2A 0 1meg
Rc3 sclA 0 1meg
Rc4 sdaA 0 1meg""",
        tran="1u 14m", compare=["v(vsetA) v(vsetB)", "v(xa.iset) v(isetB)", "i(VsA) i(VsB)"],
        planted=("R21 14.0k -> 14.7k", "R21 vset gnd {14000*k_r21}", "R21 vset gnd {14700*k_r21}")),
    "efuse-tps25947": dict(
        block="XA 0 ovlA penA vbusA vpoA efuse_tps25947",
        flat="""XC21 vbusB 0 MLCC c0=1e-06 v0=20 m=1.7 k=1 esr=15m vop=9
XC22 vbusB 0 MLCC c0=1e-07 v0=20 m=1.5 k=1 esr=30m vop=9
XC23 efuse_enB 0 MLCC c0=1e-07 v0=20 m=1.5 k=1 esr=30m vop=1.2
XC31 vpoB 0 MLCC c0=1e-06 v0=20 m=1.7 k=1 esr=15m vop=9
XQ1 efuse_enB q1_gB 0 N2N7002 vth=1.75 kp=0.067
XQ2 q1_gB q2_gB 0 N2N7002 vth=1.75 kp=0.067
R23 vbusB efuse_enB 48700
R24 efuse_enB 0 10000
R25 vbusB ovlB 76800
R26 ovlB 0 10000
R29 vbusB q1_gB 100000
R30 penB q2_gB 1000
R34 q1_gB 0 100000
R35 q2_gB 0 100000
XU4 vbusB vpoB efuse_enB ovlB 0 TPS259474 ron=0.0282 ilim=3.34 idvdt=2.21u cdvdt=4.7e-09 citimer=1e-08 iitimer=1.8u dvit=1.51
+ ven_r=1.20 ven_f=1.09 vov_r=1.20 vov_f=1.09
Rlk_efuse_en efuse_enB 0 1e9
Rlk_q1_g q1_gB 0 1e9
Rlk_q2_g q2_gB 0 1e9""",
        stim="""* a 9 V contract at 1 ms behind 50 mohm; PEN (IO10) high at 3 ms; a 10 ohm + 100 uF load; the source steps to
* 12 V at 40 ms (past OVLO's 10.4 V) and back at 50 ms (dVdt restart); PEN low at 75 ms
VsA sA 0 PWL(0 0 1m 0 1.5m 9 40m 9 40.05m 12 50m 12 50.05m 9)
VsB sB 0 PWL(0 0 1m 0 1.5m 9 40m 9 40.05m 12 50m 12 50.05m 9)
RsA sA vbusA 0.05
RsB sB vbusB 0.05
VpA penA 0 PWL(0 0 3m 0 3.01m 3.3 75m 3.3 75.01m 0)
VpB penB 0 PWL(0 0 3m 0 3.01m 3.3 75m 3.3 75.01m 0)
RlA vpoA 0 10
RlB vpoB 0 10
ClA vpoA 0 100u
ClB vpoB 0 100u""",
        tran="1u 90m", compare=["v(vpoA) v(vpoB)", "v(xa.efuse_en) v(efuse_enB)", "v(ovlA) v(ovlB)",
                                "v(xa.q1_g) v(q1_gB)", "i(VsA) i(VsB)"],
        planted=("R26 10k -> 11k (OVLO 10.4 -> 9.6 V)", "R26 ovlo gnd {10000*k_r26}", "R26 ovlo gnd {11000*k_r26}")),
    "buck-ap63203": dict(
        block="XA v3A 0 vbusA buck_ap63203",
        flat="""XC40 vbusB 0 MLCC c0=4.6e-06 v0=7 m=1.7 k=1 esr=10m vop=9
XC41 vbusB 0 MLCC c0=1e-07 v0=20 m=1.5 k=1 esr=30m vop=9
XC43 v3B 0 MLCC c0=2.02e-05 v0=5.0 m=1.75 k=1 esr=4.7m vop=3.3
XC44 v3B 0 MLCC c0=2.02e-05 v0=5.0 m=1.75 k=1 esr=4.7m vop=3.3
XU5 vbusB v3B v3B 0 AP63203 vref=3.3 gp=9 wi=6e5 ilim=2.5""",
        stim="""* VBUS 0 -> 9 V at 0.5 ms behind 0.1 ohm; 3V3 load 25 mA, a 345 mA Wi-Fi burst at 4 ms (0.5 us edges)
VsA sA 0 PWL(0 0 0.5m 0 0.6m 9)
VsB sB 0 PWL(0 0 0.5m 0 0.6m 9)
RsA sA vbusA 0.1
RsB sB vbusB 0.1
ILA v3A 0 PWL(0 0 3m 25m 4m 25m 4.0005m 345m 4.3m 345m 4.3005m 25m)
ILB v3B 0 PWL(0 0 3m 25m 4m 25m 4.0005m 345m 4.3m 345m 4.3005m 25m)""",
        # The averaged loop switches its integrator on a comparison (V(err) > 0), and two copies solved in one
        # matrix cross it a time step apart: their input currents differ by ~0.12 uA in 0.17 A (voltages by 2 nV),
        # so currents are held to 1 uA here. The planted 10 uF error moves them by 15 mA.
        tol_i=1e-6,
        tran="50n 6m", compare=["v(v3A) v(v3B)", "i(VsA) i(VsB)"],
        planted=("C43 22u -> 10u", "XC43 3v3 gnd MLCC c0=2.02e-05", "XC43 3v3 gnd MLCC c0=1.0e-05")),
    "rtc-pcf85063a": dict(
        block="XA v3A 0 sclA sdaA rtc_pcf85063a c51=2m irtc=0.5u",
        flat="""R52 v3B 3v3_rtcB 100
D2a 3v3_rtcB vrtcB DBAV170
D2b 3v3_rtcB vrtcB DBAV170
C51 c51xB 0 2m
Resr51 vrtcB c51xB 1e-3
Bld vrtcB 0 I = (0.5u+0)*min(1, max(0, V(vrtcB)/0.5))
Rlk_3v3_rtc 3v3_rtcB 0 1e9
Rlk_vrtc vrtcB 0 1e9""",
        stim="""* 3V3 up at 1 ms behind 50 mohm (the EDLC empty; 2 mF here so it charges visibly), unplugged at 80 ms
V3A sA 0 PWL(0 0 1m 0 1.2m 3.3 80m 3.3 80.2m 0)
V3B sB 0 PWL(0 0 1m 0 1.2m 3.3 80m 3.3 80.2m 0)
RsA sA v3A 0.05
RsB sB v3B 0.05
Rc3 sclA 0 1meg
Rc4 sdaA 0 1meg""",
        tran="2u 100m", compare=["v(xa.vrtc) v(vrtcB)", "i(V3A) i(V3B)"],
        planted=("R52 100 -> 1k", "R52 3v3 3v3_rtc {100*k_r52}", "R52 3v3 3v3_rtc {1000*k_r52}")),
}
CASES["ldo-ldl1117"]["planted"] = ("C4 22u -> 10u", "XC4 3v3 c4_esr MLCC c0=2.02e-05", "XC4 3v3 c4_esr MLCC c0=1.0e-05")


def run(name, c, model=None, quiet=False):
    deck = f"""* {name}: block subcircuit (A) against the same parts flat (B)
.include {model or os.path.join(ROOT, name, 'model.inc')}
.include {os.path.join(ROOT, 'usb-c-power', 'model.inc')}
{c['block']}
{c['flat']}
{c['stim']}
.options reltol=1e-6 abstol=1e-12 vntol=1e-9
.control
tran {c['tran']}
""" + "".join(f"let d{k} = abs({a.split()[0]} - {a.split()[1]})\nlet s{k} = abs({a.split()[0]})\n"
              f"meas tran m{k} max d{k}\nmeas tran r{k} max s{k}\n"
              for k, a in enumerate(c["compare"])) + """quit
.endc
.end
"""
    with tempfile.TemporaryDirectory() as d:
        path = os.path.join(d, "deck.cir")
        open(path, "w").write(deck)
        out = subprocess.run(["ngspice", "-b", path], capture_output=True, text=True, timeout=600).stdout
    vals = {m.group(1): float(m.group(2)) for m in re.finditer(r"^([mr]\d+)\s*=\s*([-+0-9.eE]+)", out, re.M)}
    ok = True
    for k, a in enumerate(c["compare"]):
        diff, rng = vals.get(f"m{k}"), vals.get(f"r{k}")
        tol = c.get("tol_i", 1e-9) if a.startswith("i(") else 1e-6
        good = diff is not None and diff <= tol and rng and rng > 10 * tol
        ok &= bool(good)
        if not quiet:
            print(f"  {'ok ' if good else 'BAD'} {a:24} max |A-B| {diff!s:>12}  (signal peaks at {rng})")
        elif not good:
            print(f"    differs: {a:24} max |A-B| {diff!s:>12}  (signal peaks at {rng})")
    return ok


def planted(name, c):
    """Run the case on a copy of the block's model.inc with one part value changed: it must fail."""
    what, old, new = c["planted"]
    text = open(os.path.join(ROOT, name, "model.inc")).read()
    if text.count(old) != 1:
        raise SystemExit(f"{name}: planted error {what!r}: {old!r} is not in model.inc exactly once")
    with tempfile.TemporaryDirectory() as d:
        os.makedirs(os.path.join(d, name))
        shutil.copy(os.path.join(ROOT, "models.inc"), d)
        path = os.path.join(d, name, "model.inc")
        open(path, "w").write(text.replace(old, new))
        return not run(name, c, model=path, quiet=True)


def main(names):
    bad = 0
    for name, c in CASES.items():
        if names and name not in names:
            continue
        print(name)
        bad += not run(name, c)
        if "planted" in c:
            caught = planted(name, c)
            print(f"  {'caught' if caught else 'MISSED'} planted error: {c['planted'][0]}")
            bad += not caught
    return 1 if bad else 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
