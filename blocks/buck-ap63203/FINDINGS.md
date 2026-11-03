# buck-ap63203: findings and what the board must do

Anchor U5. **Copper extent: x −1.83 … 9.95 mm, y −2.65 … 6.70 mm**, to the copper's edges (tracks and vias with their
widths; parts' pads and courtyards reach further) from U5. **Rev B**: cut from the date-label-printer at rev B (board
92af546: eight DFM audit rounds, CLEAN; post-layout simulation with routed copper and a 200 × 23 Monte Carlo, "sim4").
Rev A's cut (6f36126) was replaced: its review's layout findings are what rev B changed (last section).
All the block's copper is on F.Cu, plus five GND vias: it no longer uses In2 or B.Cu, but its vias need a ground plane
(In1 on the source board, which stays four-layer).

## What is in it

- **U5 AP63203WU** (TSOT-23-6, KiCad's own symbol and footprint; C780769): fixed 3.3 V, VIN 3.8–32 V,
  35 V absolute (DC), VFB 3.27–3.33 V (CCM, −40 … 85 °C), IPEAK limit 2.5–3.1 A, 1.1 MHz, UVLO rising 3.3–3.7 V.
  EN is tied to VIN: it runs whenever VIN is above UVLO.
- **Input**: C41 100 nF 50 V X7R 0603 (C14663) and **C40 4.7 µF 50 V X7R 1206 (C29823, Basic)**, straight below VIN
  (pin 3) and GND (pin 4): VIN → C41 → C40 and GND → C41 → C40 on locked 0.5 mm F.Cu, the loop through C41 about
  1.9 mm deep. **A GND via at each ground**: U5.4 (1.3 mm from the pin), C41.2 and C40.2. VBUS has no via in the
  block: it enters at C40.1 (the board's job).
- **C42** 100 nF bootstrap, vertical beside pins 5/6: SW leaves pin 5 straight out to C42.1 (1.8 mm) and on to L1.1
  (2.0 mm more), BST from pin 6 to C42.2 (1.8 mm). **Nothing under U5.**
- **L1** 4.7 µH CKCSA4020 (C354583, `lp` footprint): Isat 4 A (above IPEAK's 3.1 A max), Irms 2.85 A, 110 mΩ.
- **Output** C43, C44 22 µF 25 V X5R 0805 (CL21A226MAQNNNE, C45783; 13.6 µF each at 3.3 V by the fitted curve) **at
  L1.2**: C43.1 about 3.7 mm of 0.4 / 0.8 mm track from L1.2 (0.8 mΩ), C44 2.1 mm beyond it on the same 0.8 mm run
  (1.3 mΩ), **a GND via at each cap's ground** (0.25 mm stubs, the block's narrowest track).
- **The 3V3 trunk and FB**: from the cap node a 0.5 mm run goes round the right of L1 and back over the top of U5 to
  FB (pin 1), about 19 mm (18.9 mΩ C43 → FB). **FB is the trunk's far end**, so it senses the trunk, not the cap
  node, and **3V3 crosses neither the input loop nor the SW node**: it passes 1.2 mm above L1's SW pad and 0.45 mm
  above C42's BST pad.
- **The `lp` library** (block.json `local_libs`): L1's footprint is LCSC's (easyeda2kicad). The toolkit
  ships no third-party library; a board supplies its own copy (`libs=`).

## The VIN range it was validated at

In simulation (sim4, lumped and on copper; Monte Carlo on both): **4.44–5.5 V** at VBUS (USB before a contract:
plug-in at 4.75–5.5 V, Wi-Fi bursts at 4.75 V on a 2 m thin cable, which sags VBUS to 4.44 V), **9.15–12.6 V** (the
12 V fallback contract ± 5 %, printing, down to 9.15 V on a 2 m thin cable), **12.03–15.75 V** (the 15 V contract
± 5 %, printing, 12.03 V the thin-cable sag), **20, 24 and 28 V** (a source fault during a print: U5 sees the full
28 V, 3V3 holds at 3.318 V; **28 V is the source board's bench ceiling** (a source behind 220 µF with a 3.6 A limit),
not a bound on what a faulted source can do, and hot-plugging a faulted source is the board's to handle), and **VBUS rings to 21.2 V on copper (22.47 V lumped)** when the board's eFuse trips on a
hard short at its output (s8; Monte Carlo worst 22.41 / 23.63 V). A 9 V contract (8.55–9.45 V) runs the buck too
(sim4 s7).

**Input limits are now U5's, not a capacitor's** (C40 and C41 are 50 V): **operate at ≤ 32 V**, the recommended range
(VFB's 3.27–3.33 V window applies only at 3.8–32 V; the datasheet's Note 7: function is not guaranteed outside it), and
**never exceed 35 V, transients included**. VIN alone is rated 35 V DC and 40 V for 400 ms, but EN is tied to VIN
here and EN has no transient rating, so 35 V is the ceiling. The simulated 28 V fault leaves 4 V of operating margin
and 7 V to the absolute maximum.

The model is averaged (no 1.1 MHz ripple, no PFM, an ASSUMED loop at about fsw/20, soft start 2 ms where the
datasheet gives 4 ms typ, dropout ignored: RDS(on) typ only): it shows the DC and load-step behaviour, not stability
or ripple. It also cannot show what the 19 mΩ / few-nH trunk between the caps and FB does to the loop (below). The
datasheet guarantees VFB 3.27–3.33 V in CCM only; at light load the part runs PFM. The model's UVLO uses typical
figures (3.5 V rising, 0.44 V hysteresis; the guaranteed rising window is 3.3–3.7 V), which is irrelevant above the
4.44 V minimum simulated.

**A loop-independent bound on the burst droop**: ΔV ≈ ΔI / (2π · fc · Cout). With a slow 20 kHz crossover, a 0.32 A
step and the Monte Carlo's lowest 19.6 µF, ΔV ≈ 130 mV, so 3V3 ≥ ~3.13 V from VFB's 3.27 V minimum (and the
load's own −13 mV): 3V3 holds above 3.0 V whatever the ASSUMED loop, as long as it crosses over at 20 kHz or above.

**Current: validated by simulation to 345 mA bursts and 0.1 A average**; the part is rated 2 A. Nothing in the block's
copper limits it near 0.5 A: rev A's 0.4 mm on a 0.5 oz inner layer is gone, and the narrowest current path is now
0.4–0.5 mm of 1 oz outer copper, ~1.2–1.4 A at 10 °C rise by IPC-2221; at 0.5 A the trunk drops ~9.5 mV (18.9 mΩ,
regulated out at FB), and C40 at 15 V (~2.9 µF with C41) gives ~27 mV p-p input ripple (~20 mV at 0.35 A; ~0.11 V
p-p and ~0.8 A rms at 2 A; estimates, not simulated). So a requirement of **0.5 A (the source board's L2, "3.3 V ≥
500 mA") is met by rating and by this arithmetic, not by simulation**; above 0.35 A it has not been simulated.

## Margins (sim4, worst case over fixed corners and Monte Carlo; lumped / routed copper)

| What | Worst | Limit | Margin |
|---|---|---|---|
| 3V3 under 345 mA Wi-Fi bursts, 4.75 V source on a 2 m thin cable (MC) | 3.225 / **3.212 V** min; 3.372 / 3.369 V max | 3.0 / 3.6 V | 0.21 / 0.23 V |
| 3V3 while printing at 15 V (2.5 A strobes from VBUS; MC, 4 sets) | 3.225 / **3.211 V** | 3.0 V | 0.21 V |
| 3V3 while printing at the 12 V fallback (MC, 2 sets) | 3.227 / 3.211 V | 3.0 V | 0.21 V |
| 3V3 through a hard short downstream (VBUS ringing to 22–24 V; MC) | 3.231 / 3.216 V | 3.0 V | 0.22 V |
| 3V3 peak at plug-in (fixed) | 3.304 / 3.303 V | 3.6 V | 0.30 V |
| 3V3 during a 28 V source fault (fixed) | 3.322 / 3.318 V | 3.6 V | 0.28 V |
| Buck VIN min while printing: 15 V / 12 V contracts, 2 m cable (MC) | 13.30 / 10.43 V | UVLO 3.7 V max | 9.6 / 6.7 V |
| VBUS min, thin cable: 4.75 V Wi-Fi / 12 V print / 15 V print (fixed) | 4.44 / 9.15 / 12.03 V | UVLO 3.7 V max; dropout | 0.74 V; ~1.1 V headroom over 3.3 V at 4.44 V |
| **Input, abs max: VBUS worst**: source fault (fixed) / hard-short ring (MC lumped, copper) | 28.0 V (bench ceiling) / 23.63, 22.41 V | U5 32 V operating, 35 V absolute; C40, C41 50 V | **4.0 / 7.0 V**; 8.4, 9.6 V to 32 V |

"Copper" for the print and Wi-Fi sets is the R-only deck (checked against R + L on the worst corners); plug-in,
fault and short ran R + L. Figures not in the source board's `sim/RESULTS.md` sim4 tables (4.44, 13.30, 10.43,
3.227 / 3.211, 3.231 / 3.216, 3.322 / 3.318 V) are in the source board's committed sim4 outputs, traced to file and line in `sim/results/sim4/block-figures-buck-ap63203.txt`. 3V3 is read at the load's own pin (the source board's module), 37.9 mΩ beyond the trunk's
FB end (−13 mV at 345 mA, not corrected). **3V3's maximum while printing is not reported by sim4** (it records the
minimum only); the Wi-Fi 3.369 V and the fault's 3.318 V are the maxima on record.

**Capacitance after DC bias** (the source board's curves; C40's is ASSUMED: 0.89x at 5 V, 0.60x at 15 V):

| | 5 V | 12 V | 15 V | 21–22.5 V ring | 28 V fault |
|---|---|---|---|---|---|
| C40 4.7 µF 50 V X7R 1206 | 4.23 µF | 3.21 µF | 2.82 µF | 2.16–2.05 µF | 1.65 µF |
| C41 100 nF 50 V | 89 nF | 68 nF | 61 nF | 48–46 nF | 38 nF |
| Input total (rev A at 15 V: ~1.0 µF) | 4.32 µF | 3.28 µF | **2.88 µF** | 2.2 µF | 1.7 µF |

Output C43 + C44 at 3.3 V: **27.2 µF** nominal; over the Monte Carlo's 0.72–1.20x, 19.6–32.7 µF; on guaranteed
figures stacked (13.6 µF each × 0.8 for −20 % × 0.85 for temperature × 2) ≈ **18.5 µF**. Both worst cases are below
the datasheet's suggested 22 µF (see *Accepted*).

## Accepted, and carried by the block

- **Input capacitance is still below the datasheet's suggestion.** Diodes: "a ceramic capacitor greater than 10 µF is
  sufficient for most applications". C40 stays 4.7 µF so the source board keeps inside USB's 10 µF on VBUS before a
  PD contract (cSnkBulk: 8.1 µF nominal on that board). Rev B's 50 V X7R nearly triples it at 15 V (2.9 µF against
  rev A's ~1.0 µF). The 1.1 MHz input ripple is not simulated and the board's VBUS bulk is elsewhere: **measure at
  bring-up** (below).
- **Output capacitance can fall below the datasheet's suggestion.** Diodes gives 22–68 µF as "sufficient for most
  applications", not as a hard minimum. 2 × 22 µF nominal is about 27 µF at 3.3 V, but the Monte Carlo's worst is
  19.6 µF and the guaranteed stack (tolerance, temperature, DC bias) ≈ 18.5 µF. Accepted: the simulated bursts pass
  with 19.6 µF and the hand bound above holds; **the bring-up step response is the evidence** for the real parts.
- **L1 under a hard 3V3 short.** The current ratchets up to the low-side valley limit (3.9 A max) plus one minimum
  on-time's rise (≈ 0.26 A at 15 V, 0.48 A at 28 V; tON is given typical only), ≈ **4.2–4.4 A against L1's recorded
  Isat of 4 A**, until hiccup ends it after 2 ms. Accepted: a fault case, brief, a shielded part that saturates
  softly, and the hiccup ends it. The inductor's datasheet is not on file, so whether 4 A is a minimum or a typical
  figure is unknown. **Next revision: an inductor with Isat ≥ 4.5 A.**
- **L1**: ripple about 0.50 A at 15 V (0.56 A at 28 V), below the datasheet's 30–50 % of 2 A (a larger inductance than
  its table's 3.9 µH: less ripple, a slower slew into load steps; the simulated bursts pass). DCR 110 mΩ, a little over
  the 100 mΩ it suggests "for highest efficiency" (load here ~0.1 A average).
- **FB is remote sense at the load tap, deliberately**: the far end of a ~19.2 mm, ~18.9 mΩ, few-nH 3V3 trunk from the
  caps (the rev A review asked for FB at the cap node; rev B reverses that). DC is better for it (the trunk's drop is
  regulated out). The cost is a pole in the sense path: with ~10 µF at the load, ≈ 840 kHz, so ≈ 4° of phase at a
  55 kHz crossover (the review's estimate; not modelled). **Bring-up: the 3V3 step response at the FB end.**
- **Copper**: 1 oz outer layers, where the datasheet recommends 2 oz for 2 A; the source board draws ~0.1 A average and
  0.35 A peaks from 3V3.
- **JLC**: C780769 at +270, C354583 and C29823, placed by `jlc_verify` pad by pad.

## Measure at bring-up

- **VIN ripple at C40** at 15 V with a 0.35 A load step, and **3V3 ripple and its step response** at the FB end of the
  trunk (the model has neither, nor the trunk's effect on the loop).
- 3V3 at the load's own pin during its worst bursts, if the load sits far from the trunk.
- At 5 V on a long thin cable (VBUS ~4.4 V): 3V3 under Wi-Fi bursts (the model ignores dropout).

## The board's job

- **VBUS to C40.1** (the source board: a 0.5 mm F.Cu stub left from C40.1 to its own VBUS via, fed on B.Cu from the
  USB-C's VBUS join via: 21 mΩ, 6.2 nH), and **3V3 from the trunk to the loads**, best at its FB end (the corner
  above pin 1), where the source board takes its module's 3V3; a tap nearer the caps is regulated less exactly.
- A **solid ground plane under the block** (In1 on the source board), unbroken under L1's SW pad and the input loop:
  the block's five GND vias land in it.
- **Keep VBUS at or below 32 V in operation and never above 35 V**, transients included (U5's limits above; C40/C41
  are 50 V now). On the source board the worst simulated is its 28 V bench-ceiling fault and a 22–24 V ring at an
  eFuse trip; a faulted source above that, or hot-plugged, is the board's to bound. Its own rule (every VBUS part
  ≥ 25 V) is the board's, not the block's.
- **Count C40 + C41 (4.8 µF nominal, ~4.3 µF at 5 V)** against USB's 10 µF on VBUS before a contract.
- **Load it to ≤ 0.35 A for the simulated figures**; to 0.5 A on rating and arithmetic (above); beyond that, re-validate.
- **The block's design rules** (block.json): `min_track_width` 0.18 mm (the block's narrowest track is now 0.25 mm).
  It needs a ground plane layer for its vias, not four layers.
- **Keep parts out of the copper extent** (the trunk encloses L1 and runs over U5; the SW node and input loop are in it).

## Rev A review findings and how rev B answers them

Rev A's block was reviewed once, independently (NOT CLEAN: 1 blocker, 5 should-fix, 4 suggestions); its layout
findings were declined in that cut and recorded for the next revision. Rev B is that revision. Rev B's block has had
one independent review round (NOT CLEAN: 0 blockers, 5 should-fix, 5 suggestions), answered in this file: row 3
below, the output capacitance, the current rating against 0.5 A, U5's input limits, L1 under a short, the droop
bound, the 28 V bench ceiling and the model's UVLO.

| # | Rev A finding | Rev B |
|---|---|---|
| 1 | BLOCKER: C40 25 V, with no margin over the 25 V VBUS rule | **Resolved**: C40 is 4.7 µF 50 V X7R 1206 (C29823). U5's limits (≤ 32 V operating, 35 V absolute) now come first; sim4 runs U5 to 28 V (the bench's fault ceiling) and through a 21–24 V ring with margin |
| 2 | Bootstrap loop ~8.8 mm, its SW branch under U5 0.7 mm from FB | **Resolved** as proposed: C42 vertical at (2.9, −0.48) beside pins 5/6, ~1.8 mm each way; no copper under U5 |
| 3 | Output caps 14 / 20 mm of track from L1, C44 fed through C43, no via at C43.2 or U5.4; FB from the cap node | **Partly**: caps and vias resolved (C43/C44 at L1.2, 3.7 mm on 0.8 mm copper; C44 still beyond C43, 2.1 mm on; a GND via at each cap and at U5.4). FB deliberately moved the other way, to remote sense at the load tap, the trunk's far end (see *Accepted*) |
| 4 | No stated current rating | **Carried**: validated by simulation to 345 mA bursts / 0.1 A average; nothing in the copper limits it near 0.5 A (now 1 oz outer copper throughout), so 0.5 A is met by rating, not simulation |
| 5 | Factual errors (C43/C44 25 V, extent on centrelines, tSS 4 ms typ, VFB CCM-only) | **Carried** corrected; the model keeps the source board's 2 ms soft start |
| 6 | Board's job missed transient protection, the pour at C43.2/U5.4, In1 under SW, In2/B.Cu room, cSnkBulk, the rating | **Resolved or carried**: C43.2/C44.2/U5.4 have vias of their own; no In2/B.Cu copper; the plane, the VBUS limit (now U5's 35 V), cSnkBulk and the rating stay in the board's job |
| 7 | 3V3 threaded through the input loop | **Resolved**: the trunk runs right of L1 and over U5 to pin 1; nothing crosses C40/C41 |
| 8 | `min_track_width` 0.12 vs a 0.187 mm track | **Resolved** (0.18 since rev A; narrowest now 0.25 mm) |
| 9 | Minimum VIN at 4.75 V on a 2 m cable not reported; dropout not guaranteed | **Partly**: sim4 reports VBUS 4.44 V min there (3V3 3.211 V); U5's pin is a few mV lower. The model still ignores dropout: bring-up item |
| 10 | Minor: ripple ~0.66 A p-p worst, short-circuit overshoot ~3.7 A vs Isat 4.0 A, the table's 3.9 µH | **Unchanged** (same L1 and U5); the short-circuit bound is now taken as 4.2–4.4 A and accepted (see *Accepted*); Isat ≥ 4.5 A for the next revision |
