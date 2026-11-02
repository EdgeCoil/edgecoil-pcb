# buck-ap63203: findings and what the board must do

Anchor U5. **Copper extent: x −2.45 … 6.80 mm, y −2.80 … 10.08 mm**, to the copper's edges (tracks and vias with their widths; parts' pads and courtyards reach further) from U5. Cut from the
date-label-printer (four DFM audit rounds, CLEAN; post-layout simulation with routed copper and a
200 × 9 Monte Carlo, "sim3"). Four layers: the 3V3 output joins FB on In2 and B.Cu.

## What is in it

- **U5 AP63203WU** (TSOT-23-6, KiCad's own symbol and footprint; C780769): fixed 3.3 V, VIN 3.8–32 V,
  35 V absolute (DC), VFB 3.27–3.33 V, IPEAK limit 2.5–3.1 A, 1.1 MHz, UVLO rising 3.3–3.7 V. EN is
  tied to VIN: it runs whenever VIN is above UVLO.
- **Input**: C41 100 nF 50 V and C40 4.7 µF 25 V X5R 0805 (C1779) straight below VIN (pin 3) and GND
  (pin 4); the loop closes in about 2 × 1.5 mm through **locked 0.5 mm tracks** (VIN → C41 → C40,
  GND → C41 → C40 → two GND vias), as an audit asked (the first layout closed it through two vias
  8 mm apart).
- **L1** 4.7 µH CKCSA4020 (C354583, `lp` footprint): Isat 4 A (above IPEAK's 3.1 A max), Irms 2.85 A,
  110 mΩ. **C42** 100 nF bootstrap. **Output** C43, C44 22 µF 25 V X5R 0805 (CL21A226MAQNNNE, C45783; 13.7 µF each at 3.3 V by the fitted curve).
- **The `lp` library** (block.json `local_libs`): L1's footprint is LCSC's (easyeda2kicad). The toolkit
  ships no third-party library; a board supplies its own copy (`libs=`).

## The VIN range it was validated at

In simulation (sim3, lumped and on copper): **4.75–5.5 V** (USB before a contract, plug-in, Wi-Fi bursts
at 4.75 V on a 2 m cable), **8.55–9.45 V** and **14.25–15.75 V** (9 V and 15 V contracts ± 5 %).
The source board also simulated sources faulting to 20, 24 and 28 V, but those corners checked its
eFuse network; for this block **25 V is the limit**: **C40 is rated 25 V**, so a source above 25 V
exceeds it (U5 itself is 35 V absolute, VIN and EN alike, with no 40 V transient rating on EN). The
source board's requirement was 4.5–25 V, which runs C40 at 100 % of its rating at the top. The
model is averaged (no 1.1 MHz ripple, no PFM, an ASSUMED loop at about fsw/20, soft start 2 ms where
the datasheet gives 4 ms typ): it shows the DC and load-step behaviour, not stability or ripple. The
datasheet guarantees VFB 3.27–3.33 V in CCM only, at −40 … 85 °C; at light load the part runs PFM.

**Rated here for ≤ 0.35 A** (what was validated: 0.1 A average, 345 mA bursts), not the IC's 2 A:
the 3V3 path runs 6.2 mm of 0.4 mm on In2 (0.5 oz: ~0.4 A at 10 °C rise), and C40 at 15 V (~1 µF)
gives ~50 mV p-p at 0.35 A but ~0.3 V p-p and ~0.8 A rms at 2 A.

## Margins (sim3, worst case: routed copper; Monte Carlo)

| What | Worst | Limit | Margin |
|---|---|---|---|
| 3V3 under 345 mA Wi-Fi bursts, 4.75 V source on a 2 m thin cable | 3.211 V (min), 3.364 V (max) | 3.0 / 3.6 V | 0.21 / 0.24 V |
| 3V3 while the source board's printer draws 2.5 A peaks from VBUS | 3.214 V | 3.0 V | 0.21 V |
| 3V3 peak at plug-in | 3.303 V | 3.6 V | 0.30 V |
| VIN at 8.55 V on a 2 m cable while the printer prints | 7.57 V | UVLO 3.7 V max | 3.9 V |

The regulation point is U5's FB pin; on the source board the module's 3V3 pin is 40 mΩ further on
(−13 mV at 345 mA, not corrected). L1.2 → FB 33.4 mΩ; to C43 / C44 29.1 / 36.9 mΩ (through In2).

## Accepted, and carried by the block

- **Input capacitance is below the datasheet's suggestion.** Diodes: "a ceramic capacitor greater than
  10 µF is sufficient for most applications". C40 is 4.7 µF 25 V, chosen so the board stays inside
  USB's 10 µF limit on VBUS before a PD contract (cSnkBulk). After DC bias that is about 2.9 µF at
  5 V, 1.8 µF at 9 V and 1.0 µF at 15 V (the source board's ASSUMED curve for this part), plus C41. The input ripple
  at 1.1 MHz is not simulated, and the board's VBUS bulk is elsewhere. **Measure VIN ripple at 15 V
  and full load at bring-up** (below); if it is too high, C40 becomes a 10 µF 25 V 1206 on a board
  whose attach budget allows it.
- **C40 at 25 V**: the source board's VBUS rule (every part ≥ 25 V) is met exactly, with no margin
  for a source fault above 25 V. **Open: a 35 V or 50 V part for the next revision** (a 10 µF 35 V
  would also lift the input capacitance, inside the attach budget).
- **Output**: 2 × 22 µF nominal, about 27 µF at 3.3 V: inside the datasheet's 22–68 µF.
- **L1**: ripple about 0.40 A at 9 V and 0.50 A at 15 V, below the datasheet's 30–50 % of 2 A (a larger
  inductance than it suggests: less ripple, a slower slew into load steps; the simulated bursts pass).
  DCR 110 mΩ, a little over the 100 mΩ it suggests "for highest efficiency" (load here ~0.1 A average).
- **Copper**: 1 oz outer layers, where the datasheet recommends 2 oz for 2 A; the source board draws
  ~0.1 A average and 0.35 A peaks from 3V3.
- **JLC**: C780769 at +270 and C354583, placed by `jlc_verify` pad by pad.

## Measure at bring-up

- **VIN ripple at C40** at 15 V with a 0.35 A load step, and **3V3 ripple and its step response** (the
  model has neither).
- 3V3 at the load's own pin during its worst bursts, if the load sits far from U5.

## The board's job

- **VBUS to C40.1** (the source board: a locked 0.5 mm run from C40.1 to a VBUS via, fed on the back
  from the USB-C's VBUS join via), and **3V3 from the block's output copper to the loads**.
- A **solid ground plane under the block** (In1 on the source board) and a ground pour round it: the
  input loop's GND vias land in it.
- **Keep VBUS at or below 25 V at C40**, transients included (C40's rating; U5's VIN and EN are 35 V):
  a source fault, a PD transition, an interruption ring. On the source board the eFuse's OVLO protects
  only its output, not this input: a TVS on VBUS, or a 35/50 V C40, is the board's call.
- **Count C40 + C41 (~4.8 µF nominal)** against USB's 10 µF on VBUS before a contract.
- **A front GND pour that reaches C43.2 and U5.4** (neither has a via of its own in the block), In1
  unbroken under L1's SW pad, and room on In2 and B.Cu for the block's 3V3 copper.
- **Load it to ≤ 0.35 A** (above), or re-validate.
- **The block's design rules** (block.json): `min_track_width` 0.18 mm, four copper layers.
- **Keep parts out of the copper extent** (L1's SW node and the input loop are in it).

## Independent review of the block alone (and what was done)

One fresh reviewer, given only this directory and the toolkit's README, with Diodes' DS41326 Rev 3-2:
NOT CLEAN, 1 blocker, 5 should-fix, 4 suggestions. U5, C41, C42 and L1 check out on guaranteed
figures; the schematic is the datasheet's circuit plus a 100 nF input cap. The layout findings are
about the source board's copper, which this block reproduces exactly (the board stays canonically
the same): **declined in this cut, recorded for the next revision**, which gets its own DRC and review.

| # | Finding | Response |
|---|---|---|
| 1 | BLOCKER: C40 is 25 V, yet FINDINGS counted 24 V and 28 V source faults as validated | **Fixed in FINDINGS**: the block is validated to 25 V; the fault corners checked the eFuse, not C40. Keeping VBUS ≤ 25 V at C40 is now the board's job, and a 35/50 V C40 is an open item for the next revision (a part change is a new block, not an edit to this cut). The source board's own rule was ≥ 25 V on VBUS, which C40 meets with no margin |
| 2 | The bootstrap loop is ~8.8 mm; its SW branch runs under U5, 0.7 mm from FB | **Declined in this cut**. Next revision: C42 vertical at ~(2.4, −0.48), beside pins 5/6, the under-body track deleted |
| 3 | Output caps are ~14 / 20 mm of track from L1 (C44 fed through C43); C43.2 and U5.4 have no via of their own | **Declined in this cut**; the pour they rely on is in the board's job now. Next revision: C43/C44 at L1.2, a GND via per cap and at pin 4, FB from the cap node |
| 4 | No stated current rating; the copper and input caps support far less than 2 A | **Fixed**: rated ≤ 0.35 A, with the reasons |
| 5 | Factual errors: C43/C44 are 25 V parts, the extent was on centrelines, tSS is 4 ms typ in the datasheet, VFB is CCM-only | **Fixed** in FINDINGS (the model keeps sim3's 2 ms soft start; noted) |
| 6 | The board's job missed transient protection for C40/U5, the pour at C43.2/U5.4, In1 under SW, In2/B.Cu room, cSnkBulk counting, the rating | **Added** |
| 7 | 3V3 is threaded through the input loop (a via between C41 and C40, a track between C40's pads) | **Declined in this cut**; next revision routes 3V3 round the loop |
| 8 | `min_track_width` 0.12 vs the 0.187 mm narrowest track | **Fixed**: 0.18, all four blocks |
| 9 | Minimum VIN at U5's pin at 4.75 V on a 2 m cable not reported; dropout not guaranteed | **Recorded**: sim3's s3 (4.75 V, 2 m thin cable, Wi-Fi bursts) held 3V3 at 3.211 V min; VIN at the pin there was not tabulated, and the model ignores dropout (RDS(on) typ only) |
| 10 | Minor: worst ripple ~0.66 A p-p; short-circuit overshoot ~3.7 A against Isat 4.0 A; the datasheet's table suggests 3.9 µH | **Recorded**; acceptable |
