# usb-c-pd-sink: findings and what the board must do

Anchor U3. **Copper extent: x −3.59 … 0.40 mm, y −8.55 … 1.54 mm**, to the copper's edges (tracks and vias
with their widths; parts' pads and courtyards reach further) from U3. Cut from the date-label-printer **rev B**
(board 92af546: DFM audit CLEAN at round 8; post-layout simulation with routed copper and a 200 × 23 Monte
Carlo, "sim4", PASS with no board change). **The block's own copper is on F.Cu only** (its three vias are
ground vias), so block.json asks for no inner layers. **But the source board is four-layer, with In1 a solid
ground plane**, and every copper, inductance and ring figure below was extracted or simulated on that stackup
(microstrip over In1). A two-layer board does not inherit them: see the board's job. Rev A's cut (6f36126)
also routed ISET on In2; see the last section.

## What is in it, and what is not

| Ref | Value | Part | LCSC |
|---|---|---|---|
| U3 | HUSB238_002DD | Hynetek, DFN-10 3 × 3 | C7471904 (Extended) |
| C20 | 2.2 µF 50 V X5R 0805, at VIN | Samsung CL21A225KBQNNNE | C377773 (Basic) |
| R20 | 20.0 kΩ 1 % 0603, ISET (the 2.75 or 3 A code) | not recorded in the source board's files | C4184 (Basic) |
| R21 | 13 kΩ 1 % 0603, VSET (upper) | not recorded in the source board's files | C22797 (Basic) |
| R22 | 1 kΩ 1 % 0603, VSET (lower) | not recorded in the source board's files | C21190 (Basic) |

- **VSET is 14.0 kΩ as R21 + R22 in series**, the 15 V code (two Basic parts, where a single 14.0 kΩ is
  Extended; the cost of that choice is under *Faults*).
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

## Datasheet not on file

The Hynetek HUSB238 datasheet (rev 2.5) is not in the repository, and neither this rewrite nor its review
could fetch it. These claims rest on the source board's REQUIREMENTS.md (P1, P3, P6, P8, Part selection
row 1) and on rev A's block review, which checked them against the datasheet: the absolute maxima (VIN and
GATE 30 V, CC1/CC2 25 V, SDA/SCL 6 V); the pins' 95–105 µA source current; the VSET and ISET code tables
(the code voltages below, VSET open = 20 V, ISET open = 3.25 A); the _002 options (next lower PDO on a
mismatch, GATE on at power-up, OTP 150 °C); the 1 µF VIN capacitance it calls for; OVP at 115–125 %
with a 50 µs typical debounce; ±6 kV HBM on CC; I²C address 0x08; and that an I²C PDO request overrides VSET. **Re-check them against the datasheet before
reusing this block for anything new.**

## Accepted, and carried by the block

- **Absolute maxima**: VIN and GATE 30 V, CC1/CC2 25 V, SDA/SCL 6 V; C20 50 V. VBUS at a 5 V plug-in rings
  to **8.19 V** on the source board's (four-layer) copper, 8.55 V lumped; Monte Carlo worst 8.29 V copper,
  8.74 V lumped: 21 V inside VIN's 30 V.
- **The interruption ring at 15 V is simulated** (the source board's s8, four-layer copper): its eFuse
  opening mid-print on its enable rings VBUS to **16.31 V on copper** (16.33 V lumped); a hard short at
  the load, cut by the eFuse's fast trip, rings it to **21.20 V on copper** (22.47 V lumped; Monte Carlo
  worst **22.41 V copper, 23.63 V lumped**). That is 6.4–8.8 V inside VIN's 30 V and 1.4–3.8 V inside the 25 V the source board
  asks of every VBUS part. The figure belongs to that board's downstream (cable, eFuse, bulk) and stackup,
  not to this block.
- **The codes on guaranteed figures**: the pins source 95–105 µA and the resistors are 1 % (R21 + R22 in
  series: 1 % of 14.0 kΩ at worst), so **VSET reads 1.317–1.485 V** against the 15 V code's neighbours
  1.00 V (12 V) and 1.78 V (18 V), midpoints 1.20 / 1.59 V: margins 0.117 / 0.105 V. **ISET reads
  1.881–2.121 V** against the codes 1.65 V (2.5 A), 1.96 V (2.75 A), 2.26 V (3 A) and open (3.25 A):
  0.076 V above the 2.5/2.75 A midpoint (1.805 V), so never 2.5 A; it straddles the 2.75/3 A midpoint
  (2.11 V), so it reads 2.75 or 3 A, which is the intent (≥ 2.75 A). Its distance from "open" is 0.29 V
  only if the open window starts half a code step above 2.26 V (2.41 V, the source board's assumption):
  **the datasheet gives no decision thresholds**, so every midpoint here is the best evidence there is,
  not a guarantee.
- **Temperature**: thick-film 0603 at ±100 ppm/°C moves the resistors about ±0.45 % over 0–70 °C, so
  VSET reads 1.311–1.491 V (margins 0.111 / 0.099 V) and **ISET's minimum falls to ≈ 1.872 V, still 0.067 V
  above 1.805 V**. Whether the pins' ±5 % covers temperature is unknown without the datasheet.
- **The request, measured in simulation** (source board s0): VSET 1.400 V, ISET 2.00 V at every contract.
- **It asks for ≥ 2.75 A at 15 V.** A source whose 15 V PDO offers less (a 30 W, 15 V 2 A charger) is
  not taken at 15 V: the _002 takes **the next lower PDO that offers the ISET current**, down to 5 V.
  The source board's printer draws source peaks of **≈ 2.61 A** at worst (sim4 Monte Carlo: at the
  12 V fallback 2.612 A lumped / 2.607 A on copper (R only); at 15 V 2.598 / 2.591 A), **≈ 0.14 A below
  the 2.75 A code and ≈ 0.39 A below a 3 A contract**.
- **On a PDO mismatch the _002 takes the next lower PDO**, down to 5 V. Whatever this block feeds must
  tolerate 5, 9 and 12 V or refuse them in hardware (the source board: the eFuse's UVLO divider, on above
  9.87–10.59 V, so off at 5 and 9 V and on at 12 and 15 V).
- **OVP at 115–125 % of the request, 50 µs debounce, typical only (no minimum).**
  - **At a 5 V attach** the ring spends **9.43 µs** above 5.75 V on copper (9.48 µs lumped; Monte Carlo
    6.97 / 7.93 µs): 40 µs inside a typical figure. A part whose real debounce were shorter than that
    would trip at plug-in and fail or restart the negotiation: safe (the load stays off at 5 V), but the
    board would not come up on such a part and source.
  - **At 15 V** (OVP from 17.25 V) a strobe's release peaks at **15.88 V** (Monte Carlo worst, lumped,
    15.75 V source on 2 m; 1.37 V clear); the hard short's
    ring spends **≤ 5.62 µs** above 17.25 V on copper (5.92 µs lumped; Monte Carlo 3.84 / 4.40 µs). A
    part with a debounce that short would act after a downstream short, when the load is already cut:
    a lost contract, not a stress.
- **C20 is 2.2 µF X5R, and its 15 V value is below the HUSB238's 1 µF on part of its band.** On the DC-bias
  curve the simulation uses (**assumed**: Samsung publishes none for this part) it is **≈ 0.99 µF at 15 V
  and ≈ 1.85 µF at 5 V**. Its tolerance band, ±10 % (catalogue) × X5R ±15 % over temperature
  (0.765–1.265), is guaranteed only at 0 V bias; applied to the assumed DC-bias curve it gives
  **0.76–1.25 µF at 15 V** and **1.41–2.34 µF at 5 V**. The Monte Carlo's `cink` 0.8–1.1 is narrower
  than that band. **Accepted for this revision** because VIN is not the
  only capacitance on the bus: on the source board VBUS also carries C21 1 µF + C22 100 nF (the eFuse's
  IN) at **≈ 18.7 mΩ / 6.4 nH** of copper from U3 VIN (≈ 22 mm), and C40 4.7 µF + C41 100 nF (the buck's
  VIN) at **≈ 28.7 mΩ / 8.3 nH** (≈ 19 mm); they hold VBUS through the µs-to-ms events the HUSB238
  sees, though not its local high-frequency decoupling. A board without such parts on VBUS has only C20.
  **Next revision**: 2.2 µF 50 V X7R 1206, or 4.7 µF, re-checking cSnkBulk ≤ 10 µF.
- **Capacitance on VBUS at attach** (USB's cSnkBulk, ≤ 10 µF until the contract): this block adds C20's
  2.2 µF, 1.41–2.34 µF at 5 V on the assumed bias curve (above).
- **CC1/CC2 have no external ESD**: the block relies on the HUSB238's own pins, rated ±6 kV HBM only (a
  handling figure, not a system-level IEC 61000-4-2 rating; the datasheet gives none), with U3's exposed
  pad as their ground return. The source board decided this (its requirement P8): a CC protector must
  stand a CC-to-VBUS short (≥ 20 V working), and every discrete TVS it found stocked clamps at 40–46 V,
  above the CC pins' 25 V. **Integrated USB-C port protectors that tolerate a CC-to-VBUS short
  (TPD4S311A / TPD2S300 class) exist and were not evaluated under P8**: a candidate for the next revision.
  The receptacle's grounded shell makes first contact.
- **JLC**: C7471904 placed by `jlc_verify`, pad by pad; C377773, C4184, C22797 and C21190 likewise.
- **Copper (source board, four-layer, sim4's `cu.py`)**: C20 → U3 VIN **2.44 mΩ / 0.48 nH** (1.23 mm,
  0.25 mm wide); C20's ground → U3's exposed pad 0.20 mΩ with the front pour (1.07 mΩ for the track alone) / 0.24 nH
  (0.4 mm wide), plus C20's own ground
  via. Board side: J1 → C20 4.33 mΩ / 1.11 nH, J1 → U3 VIN 6.77 mΩ / 1.58 nH (rev A: 16.6 mΩ / 3.7 nH,
  through In2). ISET leaves pin 9 straight out to R20 in 1.8 mm, VSET pin 8 to R21 in 1.4 mm, both 0.2 mm
  on F.Cu; R20 and R22 each end on their own ground via.
- **U3's exposed pad has no via, because on the source board it cannot**: that board's CC2 runs on In2
  directly under U3 ((20.53, 48.07) → (17.06, 44.59), passing ≈ 0.4 mm from the pad's centre), so rev A's
  condition for pad vias ("once In2 is clear") never held. The pad is grounded by C20's track (and
  C20's via) and by the board's front pour, from both sides. The HUSB238 draws ~3 mA, so the pad carries
  no heat to speak of; it is, though, the ground return for an ESD strike on CC. **A re-cut with pad vias
  is declined**: it needs a board change (CC2 off In2 under U3), not a block edit.

## Faults

- **An open in the VSET string asks for 20 V.** VSET open is the 20 V code, and R21 + R22 put four solder
  joints in series where one resistor has two. A 20 V contract (19.0–21.0 V) reaches whatever the block
  feeds; on the source board OVLO cuts it only above 18.56–19.95 V, so part of that band passes, and its
  printer is rated to 24 V, so there it is a fault to refuse rather than a damage limit. **A single
  14.0 kΩ 1 % (Extended) halves the opens**: a cost trade, not taken in rev B.
- **Firmware could also ask for 20 V over I²C** whatever VSET says (the source board's F8 forbids it).

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
- **The stackup**: the figures here are four-layer (In1 solid ground). **A two-layer board re-extracts
  its copper**, or at least re-judges the VIN loop (C20 → pin 1 → exposed pad → C20) and the plug-in and
  interruption rings, without a plane under them.
- **Ground under the block**: the front pour joined to U3's exposed pad **from both sides** (CC and I²C
  leaving pins 4–7 can cut the right-hand connection off), and a ground plane or pour on another layer for
  the three vias (C20, R20, R22) to land on; on a two-layer board, a back pour under the block. **A board
  whose inner and back layers are clear under U3 adds 2–3 tented 0.3 mm vias in the exposed pad**, and
  keeps other nets off the inner layers under it.
- **Keep I²C and other switching edges off VSET, VSET_M and ISET** (high-impedance, 100 µA nodes). On the
  source board SCL runs on F.Cu 0.20 mm (edge to edge) beside both of R21's pads for about 2 mm.
- **Every part on VBUS rated ≥ 25 V** (a PD source may legally sit at 20 V, a fault can make this block
  ask for it (above), and plug-in rings to ~9 V at 5 V). **Judge the interruption ring at 15 V with the
  board's own downstream and stackup** (simulate it, as the source board's s8 does, or fit a VBUS TVS).
- **Tolerate a 20 V contract or refuse it**, and **enable the load only when the contract read back over
  I²C is the expected one** (the source board's F8: only at 12 or 15 V).
- **Firmware reads, never requests** (F8): the HUSB238 obeys an I²C PDO request over VSET, so firmware
  may read the status and PDO list but never write a request. If the bus does not answer, the contract
  is unknown: keep the load off.
- **ESD on CC1/CC2 if the connector faces users**, or state the omission as a decision (P8, above).
- **I²C pull-ups** on SDA/SCL (the source board: 4.7 kΩ to 3V3); the HUSB238 is at 0x08. It is
  powered only from VBUS, and its pins' behaviour unpowered is not specified: on the source board 3V3
  comes from VBUS, so the bus is never pulled up with the HUSB238 dead; a board with another 3V3 source
  must look at that.
- **A hardware interlock downstream** that keeps the load off at any fallback contract it cannot use
  (the source board: off at 5 and 9 V, on at 12 and 15 V).
- **Bulk on VBUS near the block** if the board has none (C20 alone is ≈ 0.76–1.25 µF at 15 V, above).
- **Specify the charger by the load's real peak**: this block admits only a 15 V source rated for
  ≥ 2.75 A at 15 V; a weaker one is taken at a lower voltage (above). The source board documents a 45 W
  (15 V 3 A) charger.
- `min_track_width` 0.18 mm in block.json allows the block's narrowest tracks (0.20 mm, ISET and VSET).
- **Keep parts out of the copper extent.**

## Rev A review findings and how rev B answers them

Rev A's cut (6f36126) had one independent review of the block alone: NOT CLEAN, 0 blockers, 5 should-fix,
5 suggestions, with findings 1, 2 and 9 declined in that cut for the next revision. Rev B (the source
board's REQUIREMENTS, *Rev B*) is that revision; this block is re-cut from it.

| # | Rev A finding | Rev B |
|---|---|---|
| 1 | R20 (ISET) and R21 (VSET) on the wrong sides of U3; ISET crossed 4.8 mm under the exposed pad on In2 through two vias (9.9 mm on its node), making the block four-layer | **Resolved.** R20 sits beyond pin 9 and R21 + R22 beyond pin 8, all on F.Cu; ISET is 1.8 mm and VSET 1.4 mm. The block's copper needs no inner layer (its figures are still four-layer: header) |
| 2 | C20 1.8 mm (pad edge) / 2.7 mm (track) from VIN; its ground loop closed only through the pour; the review asked for 2–4 vias in the exposed pad once In2 was clear | **Resolved, except the pad vias.** C20 at 90° left of pin 1, 1.23 mm of track to VIN (0.48 nH); its ground on a 0.4 mm locked track into the exposed pad (0.24 nH) and its own via. **Still open, declined:** no via in the exposed pad, because CC2 runs on In2 under it on the source board (above); the board's job covers a board that is clear there |
| 3 | ISET 2 A against a 3 A charger | **Resolved.** ISET 20.0 kΩ: 2.75 or 3 A on guaranteed figures, ≈ 0.14 A above the printer's ≈ 2.61 A worst source peak (12 V MC) |
| 4 | The interruption ring at 15 V was not simulated (hand estimate 20–25 V) | **Resolved on the source board** (s8, four-layer copper): 16.31 V on an enable cut, 21.20 V after a hard short (Monte Carlo worst 22.41 V copper, 23.63 V lumped). A different board must still judge its own (board's job) |
| 5 | No system-level ESD on CC1/CC2 | **Open, as a decision.** The source board declined a discrete CC TVS (P8); integrated port protectors were not evaluated (next revision); the board's job keeps it |
| 6 | R20's ground pad had no block copper | **Resolved.** R20's ground runs 1.1 mm to its own via |
| 7 | `min_track_width` did not match the narrowest track | **Resolved.** The block's tracks are generator-locked at 0.20 mm or wider (no router necking); 0.18 mm allows them |
| 8 | The copper extent was measured on centrelines | **Resolved** (since rev A's cut): measured to the copper's edges, above |
| 9 | C20 0603 1 µF X5R was ≈ 0.22 µF at 15 V; the review suggested 1–2.2 µF 50 V X7R 0805 | **Partly resolved.** C20 is 2.2 µF 50 V **X5R** 0805 (CL21A225KBQNNNE): 0.76–1.25 µF at 15 V (its tolerance band on an assumed bias curve; ≈ 0.99 µF nominal), below 1 µF in the low half. Accepted for this revision with the eFuse's and buck's capacitors on the same bus; next revision X7R 1206 or 4.7 µF (above) |
| 10 | Board items: I²C pull-ups from a rail live without VBUS; VSET's switch run high-impedance | **Pull-ups: open, in the board's job.** **VSET: resolved**, there is no switch and VSET is internal (1.4 mm to R21); keeping switching edges off it stays in the board's job |

## Independent review round 2 (rev B cut)

NOT CLEAN, 0 blockers, 1 should-fix, 6 suggestions, all on figure labelling and wording; applied above:
the source-peak margin now cites the Monte Carlo worst (≈ 2.60 A: ≈ 0.15 A to the 2.75 A code, ≈ 0.40 A
to 3 A); the enable-cut ring is 16.31 V on copper (16.33 V lumped); the strobe-release peak is the
simulated 15.88 V; C20's ground figure says the pour carries it (1.07 mΩ for the track alone); C20's
15 V band is labelled as its tolerance band on an assumed bias curve; and the HUSB238's 1 µF VIN figure is
listed under *Datasheet not on file*. **Declined:** putting C20's MPN into block.json, which changes only
by a re-cut; the MPN is in this file and in model.inc. Round 1 (5 should-fix, 6 suggestions) added the
stackup caveat, the exposed-pad reasoning, C20's band and next-revision part, the VSET-open fault, the
temperature term, the parts table and the datasheet note.

## Independent review round 3 (rev B cut)

NOT CLEAN: 0 / 1 / 2, all applied: the worst source peak is the 12 V Monte Carlo's (≈ 2.61 A; margins
≈ 0.14 / 0.39 A), "copper" for print checks labelled R only, and a stale path in the source board's trace file.
