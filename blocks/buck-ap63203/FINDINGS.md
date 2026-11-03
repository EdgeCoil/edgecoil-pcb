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
28 V, 3V3 holds at 3.318 V), and **VBUS rings to 21.2 V on copper (22.47 V lumped)** when the board's eFuse trips on a
hard short at its output (s8; Monte Carlo worst 22.41 / 23.63 V). A 9 V contract (8.55–9.45 V) runs the buck too
(sim4 s7). The block's input limit is now **U5's own 35 V** (VIN and EN alike, no transient rating above it), not a
capacitor: C40 and C41 are 50 V.

The model is averaged (no 1.1 MHz ripple, no PFM, an ASSUMED loop at about fsw/20, soft start 2 ms where the
datasheet gives 4 ms typ, dropout ignored: RDS(on) typ only): it shows the DC and load-step behaviour, not stability
or ripple. It also cannot show what the 19 mΩ / few-nH trunk between the caps and FB does to the loop (below). The
datasheet guarantees VFB 3.27–3.33 V in CCM only; at light load the part runs PFM.

**Rated here for ≤ 0.35 A** (what was validated: 0.1 A average, 345 mA bursts), not the IC's 2 A. The copper no longer
sets that limit (rev A's 0.4 mm on a 0.5 oz inner layer is gone; the narrowest current path is now 0.4–0.5 mm of 1 oz
outer copper, ~1.2–1.4 A at 10 °C rise by IPC-2221), and C40 at 15 V (~2.9 µF with C41) gives ~20 mV p-p input
ripple at 0.35 A and ~0.11 V p-p, ~0.8 A rms at 2 A (estimates, not simulated). Above 0.35 A, re-validate.

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
| **Input, abs max: VBUS worst**: source fault (fixed) / hard-short ring (MC lumped, copper) | 28.0 V / 23.63, 22.41 V | U5 35 V; C40, C41 50 V | **7.0 V** / 11.4, 12.6 V to U5 |

"Copper" for the print and Wi-Fi sets is the R-only deck (checked against R + L on the worst corners); plug-in,
fault and short ran R + L. 3V3 is read at the load's own pin (the source board's module), 37.9 mΩ beyond the trunk's
FB end (−13 mV at 345 mA, not corrected). **3V3's maximum while printing is not reported by sim4** (it records the
minimum only); the Wi-Fi 3.369 V and the fault's 3.318 V are the maxima on record.

**Capacitance after DC bias** (the source board's curves; C40's is ASSUMED: 0.89x at 5 V, 0.60x at 15 V):

| | 5 V | 12 V | 15 V | 21–22.5 V ring | 28 V fault |
|---|---|---|---|---|---|
| C40 4.7 µF 50 V X7R 1206 | 4.23 µF | 3.21 µF | 2.82 µF | 2.16–2.05 µF | 1.65 µF |
| C41 100 nF 50 V | 89 nF | 68 nF | 61 nF | 48–46 nF | 38 nF |
| Input total (rev A at 15 V: ~1.0 µF) | 4.32 µF | 3.28 µF | **2.88 µF** | 2.2 µF | 1.7 µF |

Output C43 + C44 at 3.3 V: **27.2 µF** (inside the datasheet's 22–68 µF); over the Monte Carlo's 0.72–1.20x,
19.6–32.7 µF.

## Accepted, and carried by the block

- **Input capacitance is still below the datasheet's suggestion.** Diodes: "a ceramic capacitor greater than 10 µF is
  sufficient for most applications". C40 stays 4.7 µF so the source board keeps inside USB's 10 µF on VBUS before a
  PD contract (cSnkBulk: 8.1 µF nominal on that board). Rev B's 50 V X7R nearly triples it at 15 V (2.9 µF against
  rev A's ~1.0 µF). The 1.1 MHz input ripple is not simulated and the board's VBUS bulk is elsewhere: **measure at
  bring-up** (below).
- **Output**: 2 × 22 µF nominal, about 27 µF at 3.3 V: inside the datasheet's 22–68 µF.
- **L1**: ripple about 0.50 A at 15 V (0.56 A at 28 V), below the datasheet's 30–50 % of 2 A (a larger inductance than
  its table's 3.9 µH: less ripple, a slower slew into load steps; the simulated bursts pass). DCR 110 mΩ, a little over
  the 100 mΩ it suggests "for highest efficiency" (load here ~0.1 A average).
- **FB senses the trunk's far end**, ~19 mΩ and a few nH past the caps (the rev A review asked for FB from the cap
  node; rev B takes it from the cap node *through* the trunk, so the load tap beside FB is what is regulated). DC is
  better for it (the trunk's drop is regulated out); the loop's response to that path is not modelled. Step response
  at bring-up.
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
- **Keep VBUS at or below U5's 35 V**, transients included (C40/C41 are 50 V now). On the source board the worst is a
  28 V source fault (simulated) and a 22–24 V ring at an eFuse trip; its own rule (every VBUS part ≥ 25 V) is the
  board's, not the block's.
- **Count C40 + C41 (4.8 µF nominal, ~4.3 µF at 5 V)** against USB's 10 µF on VBUS before a contract.
- **Load it to ≤ 0.35 A** (above), or re-validate.
- **The block's design rules** (block.json): `min_track_width` 0.18 mm (the block's narrowest track is now 0.25 mm).
  It needs a ground plane layer for its vias, not four layers.
- **Keep parts out of the copper extent** (the trunk encloses L1 and runs over U5; the SW node and input loop are in it).

## Rev A review findings and how rev B answers them

Rev A's block was reviewed once, independently (NOT CLEAN: 1 blocker, 5 should-fix, 4 suggestions); its layout
findings were declined in that cut and recorded for the next revision. Rev B is that revision. **Rev B's block has
not been reviewed independently yet**: the source board's DRC and audit round 8 (CLEAN) and sim4 cover it as part of
the board.

| # | Rev A finding | Rev B |
|---|---|---|
| 1 | BLOCKER: C40 25 V, with no margin over the 25 V VBUS rule | **Resolved**: C40 is 4.7 µF 50 V X7R 1206 (C29823). U5's 35 V is now the first limit; sim4 runs U5 to 28 V (source fault) and through a 21–24 V ring with margin |
| 2 | Bootstrap loop ~8.8 mm, its SW branch under U5 0.7 mm from FB | **Resolved** as proposed: C42 vertical at (2.9, −0.48) beside pins 5/6, ~1.8 mm each way; no copper under U5 |
| 3 | Output caps 14 / 20 mm of track from L1, C44 fed through C43, no via at C43.2 or U5.4 | **Resolved**: C43/C44 at L1.2 (3.7 mm, 0.8 mm wide; C44 still beyond C43, 2.1 mm on), a GND via at each cap and at U5.4; FB is taken from the cap node, at the end of the trunk (see *Accepted*) |
| 4 | No stated current rating | **Carried**: still ≤ 0.35 A as validated; the copper no longer limits it (now 1 oz outer copper throughout) |
| 5 | Factual errors (C43/C44 25 V, extent on centrelines, tSS 4 ms typ, VFB CCM-only) | **Carried** corrected; the model keeps the source board's 2 ms soft start |
| 6 | Board's job missed transient protection, the pour at C43.2/U5.4, In1 under SW, In2/B.Cu room, cSnkBulk, the rating | **Resolved or carried**: C43.2/C44.2/U5.4 have vias of their own; no In2/B.Cu copper; the plane, the VBUS limit (now U5's 35 V), cSnkBulk and the rating stay in the board's job |
| 7 | 3V3 threaded through the input loop | **Resolved**: the trunk runs right of L1 and over U5 to pin 1; nothing crosses C40/C41 |
| 8 | `min_track_width` 0.12 vs a 0.187 mm track | **Resolved** (0.18 since rev A; narrowest now 0.25 mm) |
| 9 | Minimum VIN at 4.75 V on a 2 m cable not reported; dropout not guaranteed | **Partly**: sim4 reports VBUS 4.44 V min there (3V3 3.211 V); U5's pin is a few mV lower. The model still ignores dropout: bring-up item |
| 10 | Minor: ripple ~0.66 A p-p worst, short-circuit overshoot ~3.7 A vs Isat 4.0 A, the table's 3.9 µH | **Unchanged** (same L1 and U5); acceptable |
