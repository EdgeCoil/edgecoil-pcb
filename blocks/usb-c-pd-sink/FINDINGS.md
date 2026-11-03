# usb-c-pd-sink: findings and what the board must do

Anchor U3. **Copper extent: x −3.59 … 0.40 mm, y −8.55 … 1.54 mm**, to the copper's edges (tracks and vias
with their widths; parts' pads and courtyards reach further) from U3. Cut from the date-label-printer **rev B**
(board 92af546: DFM audit CLEAN at round 8; post-layout simulation with routed copper and a 200 × 23 Monte
Carlo, "sim4", PASS with no board change). **Two layers**: every track is on F.Cu, and the three vias are
ground vias to the board's plane. Rev A's cut (6f36126) was four-layer, with ISET on In2; see the last section.

## What is in it, and what is not

- **U3 HUSB238_002DD** (DFN-10 3 × 3, C7471904), **C20** 2.2 µF 50 V X5R 0805 at VIN (C377773),
  **R20 20.0 kΩ** on ISET (the 2.75 or 3 A code, C4184), and **VSET 14.0 kΩ as R21 13 kΩ + R22 1 kΩ in
  series** (the 15 V code; C22797, C21190; both Basic, where a single 14.0 kΩ is Extended).
- **The request is fixed at 15 V.** VSET and the node between R21 and R22 (VSET_M) are internal: the
  source board dropped rev A's 9/15 V slide switch when its load was settled, so nothing outside the block
  touches VSET. **A different voltage is a part change, and so a new block**, not a board option.
- CC1, CC2, SDA, SCL are ports with no copper in the block (their runs are the board's). **GATE, D+ and
  D− (pins 10, 2, 3) are left open**: GATE is not used (it is on at power-up in the _002 variant, so it is
  not a contract signal), and D+/D− carry the part's BC1.2/Apple detection, which would disturb a USB data
  path on the same connector.
- **The block's VBUS copper is C20 → U3 pin 1 only.** The feed from the receptacle to C20's VBUS pad is
  the board's.
- **The `lp` library** (block.json `local_libs`): U3's symbol and footprint are LCSC's, converted with
  easyeda2kicad. The toolkit ships no third-party library; a board supplies its own copy (`libs=`).

## Accepted, and carried by the block

- **Absolute maxima** (Hynetek datasheet rev 2.5): VIN and GATE 30 V, CC1/CC2 25 V, SDA/SCL 6 V; C20 50 V.
  VBUS at a 5 V plug-in rings to **8.19 V on the source board's copper** (8.55 V lumped; Monte Carlo worst
  8.29 V on copper, 8.74 V lumped): 21 V inside VIN's 30 V.
- **The interruption ring at 15 V is now simulated** (the source board's s8): its eFuse opening mid-print on
  its enable rings VBUS to **16.33 V**; a hard short at the load, cut by the eFuse's fast trip, rings it to
  **21.20 V on copper** (22.47 V lumped; Monte Carlo worst **22.41 V copper, 23.63 V lumped**). That is
  6.4–8.8 V inside VIN's 30 V and 1.4–3.8 V inside the 25 V the source board asks of every VBUS part.
  The figure belongs to that board's downstream (cable, eFuse, bulk), not to this block.
- **The codes on guaranteed figures**: the pins source 95–105 µA and the resistors are 1 % (R21 + R22 in
  series: 1 % of 14.0 kΩ at worst), so **VSET reads 1.317–1.485 V** against the 15 V code's neighbours
  1.00 V (12 V) and 1.78 V (18 V), midpoints 1.20 / 1.59 V: margins 0.117 / 0.105 V. **ISET reads
  1.881–2.121 V** against the codes 1.65 V (2.5 A), 1.96 V (2.75 A), 2.26 V (3 A) and open (3.25 A):
  0.076 V above the 2.5/2.75 A midpoint (1.805 V), so never 2.5 A; it straddles the 2.75/3 A midpoint
  (2.11 V), so it reads 2.75 or 3 A, which is the intent (≥ 2.75 A). Its distance from "open" is 0.29 V
  only if the open window starts half a code step above 2.26 V (2.41 V, the source board's assumption):
  **the datasheet gives no decision thresholds**, so every midpoint here is the best evidence there is,
  not a guarantee.
- **The request, measured in simulation** (source board s0): VSET 1.400 V, ISET 2.00 V at every contract.
- **It asks for ≥ 2.75 A at 15 V.** A source whose 15 V PDO offers less (a 30 W, 15 V 2 A charger) is
  not taken at 15 V: the _002 takes **the next lower PDO that offers the ISET current**, down to 5 V.
  The source board's printer draws source peaks of **2.58 A** lumped / **2.56 A** on copper at 15 V
  (sim4 s2), 0.17–0.19 A below the 2.75 A code and 0.42 A below a 3 A contract.
- **On a PDO mismatch the _002 takes the next lower PDO**, down to 5 V. Whatever this block feeds must
  tolerate 5, 9 and 12 V or refuse them in hardware (the source board: the eFuse's UVLO divider, on above
  9.87–10.59 V, so off at 5 and 9 V and on at 12 and 15 V).
- **OVP at 115–125 % of the request, 50 µs debounce, typical only (no minimum).** At a 5 V attach the ring
  spends **9.43 µs** above 5.75 V on copper (9.48 µs lumped; Monte Carlo 6.97 / 7.93 µs): 40 µs inside a
  typical figure. At 15 V (OVP from 17.25 V): a strobe's release peaks at 15.8 V (1.45 V clear); the hard
  short's ring spends **≤ 5.62 µs** above 17.25 V on copper (5.92 µs lumped; Monte Carlo 3.84 / 4.40 µs).
  If a part's real debounce were that short, it would act on the ring after a downstream short, when the
  load is already cut: the consequence is a lost contract, not a stress.
- **Capacitance on VBUS at attach** (USB's cSnkBulk, ≤ 10 µF until the contract): this block adds C20's
  2.2 µF, **≈ 1.85 µF at 5 V** after DC bias (1.48–2.03 µF over tolerance and temperature, 0.8–1.1).
  At 15 V it is **≈ 0.99 µF** (0.79–1.09 µF): the datasheet's 1 µF at VIN nominally, not on every part.
- **CC1/CC2 have no external ESD**: the block relies on the HUSB238's own pins, rated ±6 kV HBM only (a
  handling figure, not a system-level IEC 61000-4-2 rating; the datasheet gives none). The source board
  decided this (its requirement P8): a CC protector must stand a CC-to-VBUS short (≥ 20 V working), and
  every such TVS it found stocked clamps at 40–46 V, above the CC pins' 25 V, so it would share a strike
  without bounding the pin. The receptacle's grounded shell makes first contact.
- **JLC**: C7471904 placed by `jlc_verify`, pad by pad; C377773, C4184, C22797 and C21190 likewise.
- **Copper (source board, sim4 extraction)**: C20 → U3 VIN 2.45 mΩ / 0.48 nH (1.23 mm, 0.25 mm wide);
  C20's ground → U3's exposed pad 0.20 mΩ / 0.24 nH (0.4 mm wide), plus C20's own ground via. Board side:
  J1 → C20 4.33 mΩ / 1.24 nH, J1 → U3 VIN 6.78 mΩ / 1.72 nH (rev A: 16.6 mΩ / 3.7 nH, through In2).
  ISET leaves pin 9 straight out to R20 in 1.8 mm, VSET pin 8 to R21 in 1.4 mm, both 0.2 mm on F.Cu;
  R20 and R22 each end on their own ground via.
- **U3's exposed pad has no via in the block**: it is grounded by C20's track (and C20's via) and by the
  board's front pour. The HUSB238 draws ~3 mA, so the pad carries no heat to speak of.

## The relation to `usb-c-power`

`usb-c-power` is a **5 V-only sink**: J1 with **5.1 kΩ CC pull-downs (R1, R2)** and the SRV05-4 on
D+/D−. Its pull-downs would sit in parallel with the HUSB238's own CC termination and fight its
signalling, so **the two blocks never go on one board**. This block wants the same receptacle without
R1/R2, CC1/CC2 as ports. On the source board J1 and its SRV05-4 sit as in `usb-c-power`, less R1/R2, and
the toolkit lays the D+/D− crossover and VBUS pad joins on any USB-C footprint. A `usb-c-power` variant
with CC1/CC2 as ports (the `usb-c-pd` block the source board's requirements ask for) is the natural next
cut from it; it is not made here.

## The board's job

- **A USB-C receptacle with no CC pull-downs**, CC1/CC2 from it to this block's CC ports, and **VBUS to
  C20's VBUS pad** (the source board: 0.4 mm on F.Cu from a via at J1's A9/B4). Keep the CC runs short and
  away from switching nodes.
- **Ground under the block**: a front pour reaching U3's exposed pad, and a ground plane or pour on
  another layer for the three vias (C20, R20, R22) to land on. On a two-layer board that is a back pour
  under the block.
- **Every part on VBUS rated ≥ 25 V** (a PD source may legally sit at 20 V, firmware could ask the
  HUSB238 for 20 V over I²C whatever VSET says, and plug-in rings to ~9 V at 5 V). **Judge the
  interruption ring at 15 V with the board's own downstream** (simulate it, as the source board's s8
  does, or fit a VBUS TVS): the source board's 21–24 V is not a property of this block.
- **ESD on CC1/CC2 if the connector faces users**, or state the omission as a decision (the source
  board's P8, above).
- **I²C pull-ups** on SDA/SCL (the source board: 4.7 kΩ to 3V3); the HUSB238 is at 0x08. It is
  powered only from VBUS, and its pins' behaviour unpowered is not specified: on the source board 3V3
  comes from VBUS, so the bus is never pulled up with the HUSB238 dead; a board with another 3V3 source
  must look at that.
- **Firmware reads, never requests** (the source board's rule F8, rev B): the HUSB238 obeys an I²C PDO
  request over VSET, so firmware may read the status and PDO list but never write a request. If the bus
  does not answer, the contract is unknown: keep the load off.
- **A hardware interlock downstream** that keeps the load off at any fallback contract it cannot use
  (the source board: off at 5 and 9 V, on at 12 and 15 V).
- **Specify the charger by the load's real peak**: this block admits only a 15 V source rated for
  ≥ 2.75 A at 15 V; a weaker one is taken at a lower voltage (above). The source board documents a 45 W
  (15 V 3 A) charger.
- `min_track_width` 0.18 mm in block.json allows the block's narrowest tracks (0.20 mm, ISET and VSET).
  No inner layers are needed.
- **Keep parts out of the copper extent.**

## Rev A review findings and how rev B answers them

Rev A's cut (6f36126) had one independent review of the block alone: NOT CLEAN, 0 blockers, 5 should-fix,
5 suggestions, with findings 1, 2 and 9 declined in that cut for the next revision. Rev B (the source
board's REQUIREMENTS, *Rev B*) is that revision; this block is re-cut from it.

| # | Rev A finding | Rev B |
|---|---|---|
| 1 | R20 (ISET) and R21 (VSET) on the wrong sides of U3; ISET crossed 4.8 mm under the exposed pad on In2 through two vias (9.9 mm on its node), making the block four-layer | **Resolved.** R20 sits beyond pin 9 and R21 + R22 beyond pin 8, all on F.Cu; ISET is 1.8 mm and VSET 1.4 mm. The block is two-layer |
| 2 | C20 1.8 mm (pad edge) / 2.7 mm (track) from VIN; its ground loop closed only through the pour; the review asked for 2–4 vias in the exposed pad once In2 was clear | **Resolved, except the pad vias.** C20 at 90° left of pin 1, 1.23 mm of track to VIN (0.48 nH); its ground on a 0.4 mm locked track into the exposed pad (0.24 nH) and its own via. **Still open:** no via in the exposed pad (above); it rests on C20's via and the front pour |
| 3 | ISET 2 A against a 3 A charger | **Resolved.** ISET 20.0 kΩ: 2.75 or 3 A on guaranteed figures, above the printer's 2.56–2.58 A source peaks |
| 4 | The interruption ring at 15 V was not simulated (hand estimate 20–25 V) | **Resolved on the source board** (s8): 16.33 V on an enable cut, 21.20 V on copper after a hard short (Monte Carlo worst 22.41 V copper, 23.63 V lumped). A different board must still judge its own (board's job) |
| 5 | No system-level ESD on CC1/CC2 | **Open, as a decision.** The source board declined a CC TVS (P8: none stocked stands a CC-to-VBUS short and clamps below 25 V); the board's job keeps it |
| 6 | R20's ground pad had no block copper | **Resolved.** R20's ground runs 1.1 mm to its own via |
| 7 | `min_track_width` did not match the narrowest track | **Resolved.** The block's tracks are generator-locked at 0.20 mm or wider (no router necking); 0.18 mm allows them |
| 8 | The copper extent was measured on centrelines | **Resolved** (since rev A's cut): measured to the copper's edges, above |
| 9 | C20 0603 1 µF X5R was ≈ 0.22 µF at 15 V; the review suggested 1–2.2 µF 50 V X7R 0805 | **Resolved, with a different dielectric.** C20 is 2.2 µF 50 V **X5R** 0805 (Basic): ≈ 0.99 µF at 15 V nominal, 0.79–1.09 µF over tolerance and temperature; ≈ 1.85 µF at 5 V, inside USB's 10 µF |
| 10 | Board items: I²C pull-ups from a rail live without VBUS; VSET's switch run high-impedance | **Pull-ups: open, in the board's job.** **VSET: resolved**, there is no switch and VSET is internal (1.4 mm to R21) |
