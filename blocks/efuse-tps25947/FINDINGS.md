# efuse-tps25947: findings and what the board must do

Anchor U4. **Copper extent: x −14.04 … 7.70 mm, y −15.20 … 5.90 mm**, to the copper's edges (tracks and vias with their widths; parts' pads and courtyards reach further) from U4 (the fail-safe
enable sits 6–15 mm above U4, as on the source board). Cut from the date-label-printer (four DFM
audit rounds, CLEAN; post-layout simulation with routed copper and a 200 × 9 Monte Carlo, "sim3").
Four layers: ten tracks run on In2.

## What is in it, and what is not

- **U4 TPS259474L** (VQFN-10 2 × 2, C2864845): 2.7–23 V, 28 V absolute, RON 28.2 mΩ typ / 45 mΩ max,
  circuit breaker with latch-off, dVdt restart after an over-voltage (the 470x bypasses it).
- **IN**: C21 1 µF 50 V X7R 0805 (C28323) and C22 100 nF 50 V on U4's IN escape. **OUT**: C31 1 µF
  50 V X7R 0805, about 3 mm below OUT.
- Thresholds below are worst-case stacks of TI's guaranteed windows and 1 % resistors (the source
  board's record had quoted narrower, nominal-ratio figures). **EN/UVLO** R23 48.7 kΩ / R24 10 kΩ from
  VBUS: rising 6.83–7.30 V, falling 6.21–6.66 V (never on at 5 V), filtered by **C23** 100 nF (τ
  0.83 ms). **OVLO** R25 76.8 kΩ / R26 10 kΩ: rising 10.09–10.81 V, falling 9.18–9.86 V. **ILM** R28
  1.00 kΩ 1 %: ILIM 2.94 / 3.34 / 3.67 A; the fast trip near 2 × ILIM is typical behaviour (ISC 201 %
  typ, no min/max); **TP3** on ILM reads 0.163–0.202 V/A (GIMON 165–200 µA/A, 0.182 typ). **dVdt** C24
  4.7 nF ±10 % X7R: 0.156–0.74 V/ms nominal C (9 V in 12–58 ms, 15 V in 20–96 ms). **ITIMER** C25 10 nF
  ±10 %: breaker blanking 4.6–16 ms.
- **The fail-safe enable**: Q1 (2N7002) holds EN low while its gate is held up from VBUS (R29/R34
  100 kΩ/100 kΩ: 2.5 V at 5 V, 14 V at a 28 V fault); Q2, driven from **PEN** through R30 1 kΩ and held
  off by R35 100 kΩ, pulls Q1's gate down. **PEN high = on.** PEN floating, low, or its supply lost
  means off; so does the logic supply dying while VBUS stays.
- **The seven 0.2 mm escapes out of U4's pins** (locked on the source board: the router only knows
  the board's 0.2 mm clearance, and U4's own pads sit 0.15–0.195 mm apart), the 0.6 mm VBUS link from
  the IN escape onto C21.1, and the ground vias at C21/C22 and C31.
- **Left to the board**: the 470 µF bulk (C30), the 10 mΩ Kelvin shunt (R31) and its test pads, the
  printer socket. They are the load's side (bulk at the load, a measurement point for one printer's
  current) and size with the load. **The 1.2 mm VPO bus is the board's too**: on the source board one
  locked segment runs from U4's VPO escape past C31 and C30 to the shunt, and a segment is never
  split, so this block's OUT copper is U4's escape alone (marked `"escape"` in block.json; on the
  block alone it ends on nothing). **The board joins it to C31.1.** Likewise VBUS reaches C21.1
  through the board's power run.
- **OVLO is a port** for the source board's 15 V position: 13.0 kΩ across R26 (17.5 V; 16.9–18.2 V
  rising; falling 15.41–16.59 V).
- **The `lp` library** (block.json `local_libs`): U4's symbol and footprint are LCSC's, converted with
  easyeda2kicad. The toolkit ships no third-party library; a board supplies its own copy (`libs=`).

## Margins (sim3, worst case: routed copper; Monte Carlo over guaranteed windows)

| What | Worst | Limit (guaranteed) | Margin |
|---|---|---|---|
| EN while the load draws 2.5 A peaks, 8.55 V source on a 2 m cable | 1.306 V | 1.116 V (falling max) | 0.19 V |
| OVLO at a 9.45 V source (9 V + 5 %) | 1.107 V | 1.183 V (rising min) | **0.076 V, the tightest** |
| OVLO at 15.75 V, 13.0 kΩ across R26 | 1.097 V | 1.183 V | 0.086 V |
| U4 current peak under 2.5 A strobes | 2.52 A | 2.97 A (ILIM min) | 0.45 A; breaker never started |
| Inrush into the source board's 470 µF + 100 µF | 0.640 A | 0.8 A (own target; 2 A contract) | 0.16 A |
| Output to 90 % after PEN | 58.4 ms (9 V), 94.5 ms (15 V) | F7 waits 70 / 110 ms | 11.6 / 15.5 ms |
| EN during the plug-in ring, PEN not driven, Q1 Vth up to 2.5 V | 0.554 V (MC), 0.79 V settled at 4.75 V | 1.183 V | 0.40 V |
| EN when the contract arrives before firmware drives PEN | ≤ 0.85 V | 1.183 V | 0.33 V |
| Off after the logic supply or PEN is lost while loaded | ≤ 94 µs; on in 0 of 200 after 10 ms | — | — |
| The weakest Q2 (Vth 2.5 V) with PEN at 3.3 V | Q1 gate ≤ 1.7 mV: on | Q1 Vth 1.0 V min | 1.0 V |
| Source fault to 28 V | Q1 VGS 14.0 V, Q2 VDS 14.0 V, EN 4.77 V, OVLO 3.23 V | ±20 V, 60 V, 6.5 V, 6.5 V | 6.0 V; 1.73 V on EN |
| Output at a 9 → 20 V source fault (9 V setting) | 9.38 V | 11 V | 1.62 V |
| U4 IN at plug-in; IN slew of the ring (from 1 µs) | 8.73 V; −2.31 / +4.10 V/µs | 28 V; −10 / +100 V/µs | 19 V; 7.7 V/µs |
| Input stepped 9 → 15 V with the output on | 2.93 A | 2.94 A (ILIM min with R28's 1 %) | **≈ 0**: see F8 |

The Monte Carlo drew CdVdt's ±10 % through IdVdt, so the F7 times above include it (not X7R's
temperature drift); it did not draw R28's 1 %, nor C24/C25 temperature.

Copper on the source board: C21 → U4 IN 3.87 mΩ / 0.8 nH; U4 OUT → C31 4.26 mΩ / 1.0 nH; U4's GND
pin reaches the planes through its 0.2 mm escape, 8.2 mΩ (it carries U4's 0.6 mA; the dividers return
through their own pads). The divider tops tee off VBUS, so EN reads 2 mV low and OVLO 6 mV low at 2.5 A.

## Firmware rules the block needs (from the source board's F7, F8, F9)

- **F7: wait before loading the output.** With 4.7 nF of dVdt the output takes up to 58 ms (9 V) or
  94 ms (15 V) to reach 90 %: wait ≥ 70 ms / ≥ 110 ms after PEN goes high. A load started mid-ramp
  sagged the rail to 6.6 V in simulation.
- **F8: never step the input up with the output on.** Charging the output's bulk by 6 V (9 → 15 V)
  took U4 to 2.93 A against its 2.97 A minimum limit, bounded only by the source's own limit; with a
  stiffer source U4 hits its limit, may time out and latch off. Safe (off), but avoid it: PEN low,
  change the contract, PEN high, wait F7. A latch clears with PEN low then high (Q1 pulls EN below
  VSD, 0.45 V).
- **F9: recover from an over-voltage cut-off.** After the input falls from 15 to 9 V while live, or
  after any real OVLO event at 9 V, the output stays off if the source sits above OVLO's falling
  threshold (9.18–9.86 V worst case; 3 of 18 corners at a 9.45 V source). Ask for 5 V, wait for
  VBUS < 6 V, ask again. **This cannot be designed out with these parts**: meeting both 11 V on the
  output and staying on at 9.45 V needs rising-max / falling-min ≤ 1.164, and this part's hysteresis
  with 1 % resistors gives 1.16 at best. The 15 V position has the same shape (falling 15.41–16.59 V
  against a 15.75 V maximum). **The block gives firmware no signal of an OVLO trip or a breaker
  latch-off** (PG/PGTH are unused): F9 must infer it (the source board: the printer stops answering).

## Accepted, and carried by the block

- **The fail-safe enable** replaced a first design whose Q1 gate was pulled up to the logic rail (a dead
  rail enabled the output). It was the EN network's second fix, so it went to a redesign review; the
  audits since judged it the circuit one would draw from scratch: driving EN from a GPIO alone would
  drop the hardware UVLO interlock (no output at 5 V, whatever firmware does).
- **The 0.2 mm escapes** (about 3 mΩ at 2.5 A) and their 0.4–0.5 mm necks outside the body: accepted.
- **PG and PGTH unused and open**; no test pad (PG means nothing with PGTH floating).
- **No Schottky from OUT to GND** (TI suggests one for inductive loads): the source board's load has
  470 µF of bulk at it. A load with long leads or a motor on its own is the board's to judge.
- **EN and OVLO dividers sit 6–8 mm from U4** (TI asks for them close); EN is filtered by C23 (τ
  0.83 ms) and both nodes are high-impedance DC; the source board passed its audits and simulation so.
- **TP3 on ILM**: TI keeps ILM's parasitic capacitance under 50 pF. A pad is a few pF; a scope probe
  (10–15 pF) is fine, a long lead may not be.
- **JLC**: C2864845 placed by `jlc_verify`, pad by pad; the 2N7002 (C8545) +180 in the toolkit's table.

## Measure at bring-up

- **U4 IN at plug-in on a scope**: falling slew against the 10 V/µs absolute limit. The simulated ring
  falls at 2.3 V/µs; only the bench's idealised contact came near it, and a real plug's bounce is not
  modelled.
- **PEN's GPIO through reset**: the simulation assumes it high-impedance (R35 holds Q2 off); confirm no
  internal pull-up on the chosen pin.
- **TP3** against a known load current, if the current limit's reading is to be used.

## The board's job

- **Join the block's three VBUS pieces**: U4 IN/C21/C22 (the power path); R25.1 and R29.1 (joined to
  each other on In2 in the block); R23.1 (no block copper). The divider tops must tee off VBUS, never
  sit in the power path.
- **Judge the turn-off ring on IN**: U4 interrupting 6–7 A (a fast trip) or an OVLO/breaker cut at
  15 V with ~1.1 µF beside it and a 2 m cable rings IN by roughly I·√(L/C) ≈ 9 V (hand estimate), to
  ~25 V against IN's 28 V; and IN's falling-slew limit (10 V/µs) was checked only at plug-in. Simulate
  these or fit a TVS on VBUS (TI's transient-protection section).
- **VBUS to C21.1 and U4's IN escape** at ≥ 1.2 mm on 1 oz (3 A; TI asks for twice the full-load
  current), with two vias at each layer change; and **U4's VPO escape to C31.1 and on to the load**,
  as wide. On the source board both are locked 1.2 mm runs (`power.PowerCopper`).
- **Bulk at the load**, sized for it (the source board: 470 µF 25 V at the printer socket), and a Kelvin
  shunt if the load current is to be measured.
- **PEN** from a GPIO that is not a strapping pin and idles high-impedance or low through reset.
- **OVLO**: leave it for 10.4 V; add resistance across R26 for a higher cut-off (13.0 kΩ: 17.5 V).
- **Every part on VBUS rated ≥ 25 V**; U4's IN is 28 V absolute.
- **The block's design rules** (block.json): `dru_rules` (U4's own pads 0.14 mm apart; JLC's minimum is
  0.1 mm; everything else at the board's 0.2 mm) through `Block.dru_rules(refs)`, `min_track_width`
  0.18 mm, and four copper layers.
- **The firmware rules F7–F9** above.
- **Keep parts out of the copper extent.**

## Independent review of the block alone (and what was done)

One fresh reviewer, given only this directory and the toolkit's README, with TI's datasheet (SLVSFC9C,
May 2026): NOT CLEAN, 0 blockers, 8 should-fix, 6 suggestions. No absolute maximum is exceeded in
any analysed case; the TPS259474L and the two-FET fail-safe were judged reasonable choices. The
layout findings are about the source board's copper, which this block reproduces exactly; the board
stays canonically the same, so they are **declined in this cut and recorded for the next revision**,
where a re-laid block gets its own DRC and review (as `ldo-ldl1117` did).

| # | Finding | Response |
|---|---|---|
| 1 | IN and OUT copper inside the block is 0.6 mm then 0.2 mm for the last 2 mm, with no vias, against TI's "twice full load" and IN/OUT as the heat path (RθJA 41.7 °C/W with 8 vias, 74.5 with none) | **Declined in this cut** (the source board's audits accepted the 0.4–0.5 mm necks as thermally negligible at ~3 mΩ). **Next revision**: flare both escapes to ≥ 1.2 mm from ~0.2 mm past the pad ends, 2–4 vias on each |
| 2 | C22 (100 nF) is 4.9 mm from IN, further than C21; both behind the neck; U4's GND pin has no via (it reaches ground through the F.Cu pour) | **Declined in this cut**; the board's job now says the front pour is U4's ground. **Next revision**: the 100 nF at the IN pad end with its ground by pin 8, a via at pin 8's escape |
| 3 | The fail-safe's grounds (R24.2, Q1 and Q2 sources, R34.2) have no via, only the pour; R35 runs 6.5 mm to a remote via | **Declined in this cut**, with the risk stated: a broken pour neck would float Q1's source and enable the output. The source board's DRC and pour checks passed (every island anchored). **Next revision**: GND vias at R24.2/Q2.S and Q1.S/R34.2, R35 local |
| 4 | OVLO's hysteresis band holds the 9 V contract; firmware cannot see an OVLO trip; the falling window was quoted too narrow | **Fixed in FINDINGS**: worst-case stacks quoted (EN, OVLO both positions), the 1.164 vs 1.16 bound recorded, F9 states firmware gets no signal. **PG** (PGTH divider on OUT, PG to a GPIO) is the right fix: next revision (the source board had no spare GPIO) |
| 5 | F7 and timing margins omit CdVdt and RILM tolerance | **Partly declined**: sim3's Monte Carlo drew CdVdt ±10 % through IdVdt, so F7's 58.4 / 94.5 ms include it (stated above). **Fixed**: ILIM with R28's 1 % (2.94–3.67 A) and ITIMER with C25 ±10 % (4.6–16 ms); the F8 margin is now ≈ 0, which only strengthens F8 |
| 6 | The dividers sit 6–8 mm from their pins; OVLO crosses under the IC on In2, unfiltered, with 76 mV of margin | **Declined in this cut** (recorded in Accepted). **Next revision**: R25/R26 by pin 2 and R23/R24/C23 by pin 1; optionally ≤ 1 nF on OVLO |
| 7 | The board's job missed two VBUS joins and the turn-off ring on IN | **Added to the board's job** |
| 8 | The 2N7002 drive is not shown on guaranteed figures: Q2 at 3.3 V and Q1 at 3.4–4.5 V across the UVLO window are below the 4.5 V RDS(on) guarantee; the margin rests on an ASSUMED kp | **Recorded**: only Vth ≤ 2.5 V at 250 µA is guaranteed below 4.5 V; the currents needed are ≤ 0.3 mA, and the source board's s7 "on" check used the weakest kp. **Next revision**: R34 → 200 kΩ (VGS = ⅔ VBUS, 18.7 V at 28 V) or a FET with RDS(on) guaranteed at 2.5 V |
| 9 | The fast trip at 2 × ILIM is typical only | **Fixed** (stated above) |
| 10 | models.inc says tOVLO is ASSUMED 5 µs; the datasheet gives 1.2 µs typ | **Recorded, model unchanged** (the ported model must stay sim3's): the model cuts OVLO slower than the part, which overstates the output's overshoot at a fault, the pessimistic side. Noted in models.inc |
| 11 | TP3's and EN's figures should be guaranteed ranges | **Fixed** above |
| 12 | TI recommends ≥ 350 kΩ pull-ups on EN/OVLO against reverse polarity; R23/R25 are 48.7/76.8 kΩ | **Recorded**: fine behind USB-C (no reverse polarity); a board behind a barrel jack must revisit it |
| 13 | 21 × 21 mm of copper for a 2 × 2 mm IC; R35 7 mm from Q2's gate leaves a high-impedance gate run | **Declined in this cut** (the source board's placement); next revision fits in ~8 × 10 mm with R35 at Q2's gate |
| 14 | A second OUT capacitor at the pad end (C31 loses ~half under DC bias at 15 V) | **Declined in this cut**; next revision with finding 1 |
