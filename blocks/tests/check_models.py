# SPDX-FileCopyrightText: 2026 edgecoil
# SPDX-License-Identifier: MIT
"""Check each block's model.inc is the circuit its block.json describes: the block subcircuit and the
same parts written out flat (as in the board simulation the models were validated in) run side by
side on one stimulus, and their waveforms must agree to 1 uV / 1 nA.

    python3 blocks/tests/check_models.py        (needs ngspice)

This proves the wiring and parameters, not the physics: the device models in ../models.inc were
validated against their datasheets in that board simulation.
"""
import os
import re
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
XC4 vddB 0 MLCC c0=2.02e-05 v0=5.0 m=1.75 k=1 esr=4.7m vop=3.3""",
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
        tran="100n 21m", compare=["v(enA) v(enB)", "v(vddA) v(vddB)", "i(VsA) i(VsB)"]),
}


def run(name, c):
    deck = f"""* {name}: block subcircuit (A) against the same parts flat (B)
.include {os.path.join(ROOT, name, 'model.inc')}
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
        tol = 1e-9 if a.startswith("i(") else 1e-6
        good = diff is not None and diff <= tol and rng and rng > 10 * tol
        ok &= bool(good)
        print(f"  {'ok ' if good else 'BAD'} {a:24} max |A-B| {diff!s:>12}  (signal peaks at {rng})")
    return ok


def main():
    bad = 0
    for name, c in CASES.items():
        print(name)
        bad += not run(name, c)
    return 1 if bad else 0


if __name__ == "__main__":
    sys.exit(main())
