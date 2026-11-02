# usb-c-pd-sink: findings and what the board must do

Anchor U3. **Copper extent: x −4.35 … 3.90 mm, y −3.55 … 4.20 mm**, to the copper's edges (tracks and vias with their widths; parts' pads and courtyards reach further) from U3. Cut from the
date-label-printer (four DFM audit rounds, CLEAN; post-layout simulation with routed copper and a
200 × 9 Monte Carlo, "sim3"). Four layers: two ISET tracks run on In2.

## What is in it, and what is not

- **U3 HUSB238_002DD** (DFN-10 3 × 3, C7471904), **C20** 1 µF 50 V X5R 0603 at VIN,
  **R20 10.5 kΩ** on ISET (2 A), **R21 14.0 kΩ** on VSET (15 V on its own).
- **VSET is a port; the voltage switch and its resistor are the board's.** The source board's 9/15 V
  slide switch is a DPDT whose pole A puts 10.7 kΩ (R22) across R21 (6.06 kΩ, the 9 V code 6.04 kΩ)
  and whose pole B sets the eFuse's over-voltage cut-off. One switch tying the PD request to the
  cut-off is that board's decision (its requirement V1), so it belongs to neither block: R22, the
  switch and the OVLO resistor stay with the board, and this block keeps only what every user needs.
  **R21 is permanent**, so VSET can never be left open (open asks for 20 V), whatever the board does.
- CC1, CC2, SDA, SCL are ports. **GATE, D+ and D− (pins 10, 2, 3) are left open**: GATE is not
  used (it is on at power-up in the _002 variant, so it is not a contract signal), and D+/D− carry the
  part's BC1.2/Apple detection, which would disturb a USB data path on the same connector.
- **The `lp` library** (block.json `local_libs`): U3's symbol and footprint are LCSC's, converted with
  easyeda2kicad. The toolkit ships no third-party library; a board supplies its own copy (`libs=`).

## Accepted, and carried by the block

- **Absolute maxima** (Hynetek datasheet rev 2.5): VIN and GATE 30 V, CC1/CC2 25 V, SDA/SCL 6 V.
  VBUS rings at plug-in: **8.55 V on the source board's copper** (8.92 V lumped; 8.71 V on copper,
  9.02 V lumped, worst of the Monte Carlo): 21 V inside VIN's 30 V. **Not simulated: a current
  interruption at 15 V** (a downstream breaker or fast trip opening at 3–7 A, a hot unplug), which
  rings VBUS up by about I·√(L/C): a hand estimate gives 20–25 V with 0.5–1 µH of cable and ~0.5 µF
  on VBUS. Inside VIN's 30 V, but at the 25 V rating this block asks of every VBUS part (below).
- **It asks for 2 A** (R20, inside the block). The HUSB238 takes the first PDO at or below the VSET
  voltage that offers at least the ISET current, so a source offering 15 V at 2 A is accepted. A load
  whose peaks exceed 2 A (the source board's printer: 2.5 A strobes, carried partly by its 470 µF) runs
  past its contract; for a 3 A request R20 is 22.6 kΩ (the datasheet's table).
- **The codes on guaranteed figures**: the pins source 95–105 µA and the resistors are 1 %, so VSET
  alone reads 1.317–1.485 V (neighbouring codes 1.0 V and 1.78 V, midpoints 1.20 / 1.59 V), VSET with
  the board's 10.7 kΩ 0.570–0.643 V (midpoints 0.30 / 0.80 V), ISET 0.987–1.113 V (midpoints 0.90 /
  1.21 V). The datasheet gives no decision thresholds, so the midpoints are the best evidence there is.
- **The request, measured in simulation**: VSET 1.400 V alone (15 V), 0.606 V with the board's 10.7 kΩ
  (9 V). The pins source 100 µA ± 5 %; with 1 % resistors the pin voltage moves ± 6 % around those
  codes (above).
- **On a PDO mismatch the _002 takes the next lower PDO**, down to 5 V. Whatever this block feeds must
  tolerate 5 V or refuse it in hardware (the source board: the eFuse's UVLO divider, on at ~7 V).
- **OVP at 115–125 % of the request, 50 µs debounce, typical only (no minimum).** At a 5 V attach the
  ring spends 7.95 µs above 5.75 V on the source board's copper (8.07 µs lumped): 42 µs inside a
  typical figure, which is all the datasheet gives.
- **Capacitance on VBUS at attach** (USB's cSnkBulk, ≤ 10 µF until the contract): this block adds
  C20's 1 µF (≈ 0.69 µF at 5 V after DC bias).
- **CC1/CC2 have no external ESD on the source board**: the block relies on the HUSB238's own pins,
  rated ±6 kV HBM only (a handling figure, not a system-level IEC 61000-4-2 rating; the datasheet
  gives none). The CC pins must also survive a CC-to-VBUS short, so a 5 V array such as the SRV05-4 is
  not a drop-in protector here.
- **JLC**: C7471904 placed by `jlc_verify`, pad by pad.
- **Copper (source board)**: J1 → U3 VIN 16.6 mΩ / 3.7 nH, 13 mΩ of it a thin In2 track (3.1 mA).
  One 0.25 mm CC2 stub lies inside U3.5's pad (the router's entry); the rest of CC2 is the board's.

## The relation to `usb-c-power`

`usb-c-power` is a **5 V-only sink**: J1 with **5.1 kΩ CC pull-downs (R1, R2)** and the SRV05-4 on
D+/D−. Its pull-downs would sit in parallel with the HUSB238's own CC termination and fight its
signalling, so **the two blocks never go on one board**. This block wants the same receptacle without
R1/R2, CC1/CC2 as ports. On the source board J1 and its SRV05-4 sit exactly as in `usb-c-power` (the
ESD array 8.41 mm above J1, at 90°), less R1/R2, and the toolkit lays the D+/D− crossover and VBUS pad
joins on any USB-C footprint. A `usb-c-power` variant with CC1/CC2 as ports (the `usb-c-pd` block
the source board's requirements ask for) is the natural next cut from it; it is not made here.

## The board's job

- **A USB-C receptacle with no CC pull-downs**, CC1/CC2 from it to this block's CC ports, and VBUS to
  C20/U3 VIN. Keep the CC runs short and away from switching nodes.
- **Every part on VBUS rated ≥ 25 V** (a PD source may legally sit at 20 V, firmware can ask the
  HUSB238 for 20 V over I²C whatever VSET says, and plug-in rings to ~9 V at 5 V). **Judge the
  interruption ring at the contract voltage** (above): simulate it, or fit a VBUS TVS.
- **ESD on CC1/CC2 if the connector faces users**: a low-capacitance TVS with a working voltage of
  20–22 V or more (it must stand a CC-to-VBUS short) and capacitance inside USB-C's CC limit; or state
  the omission as a decision.
- **R20's ground pad has no copper in the block**: it relies on the board's front pour reaching it.
- **VSET**: leave it alone for 15 V; put a resistor to GND across R21 for a lower request (10.7 kΩ:
  9 V). VSET is a high-impedance node: keep the run to the board's switch short (1–10 nF to GND is
  harmless beside the part's debounce).
- **I²C pull-ups** on SDA/SCL (the source board: 4.7 kΩ to 3V3); the HUSB238 is at 0x08. It is
  powered only from VBUS, and its pins' behaviour unpowered is not specified: on the source board 3V3
  comes from VBUS, so the bus is never pulled up with the HUSB238 dead; a board with another 3V3
  source must look at that. Firmware may
  override VSET over I²C (the source board's rule F8 does: it asks for 9 V first to identify the load).
- **A hardware interlock downstream** that keeps the load off at 5 V (see the PDO fallback above).
- **Match ISET to the load** (above): a 2 A request admits a 2 A charger. The source board documents
  a 45 W (15 V 3 A) charger for its printer while asking for 2 A: the charger must be specified by the
  load's real peak, not by the contract the block asks for.
- Give the block the board's **4-layer stackup** (block.json `copper_layers`) and **`min_track_width`
  0.18 mm** (the router necked tracks to 0.187 mm into the DFN's pads).
- **Keep parts out of the copper extent.**

## Independent review of the block alone (and what was done)

One fresh reviewer, given only this directory and the toolkit's README: NOT CLEAN, 0 blockers,
5 should-fix, 5 suggestions. It found the circuit to be the datasheet's application circuit (less
the optional GATE PMOS) and confirmed the pinout, absolute maxima, VSET/ISET tables, 0x08 and the
_002 options against the datasheet.

| # | Finding | Response |
|---|---|---|
| 1 | R20 (ISET) and R21 (VSET) sit on the wrong sides of U3: ISET (pin 9, left of VSET) crosses 4.8 mm under the exposed pad on In2 through two vias (9.9 mm on a 10.5 kΩ node), which alone makes the block four-layer and keeps vias out of the pad | **Accepted as a finding, declined in this cut**: the block is the reviewed board's copper, and the board must stay canonically the same. **For the next revision**: R20 under pin 9 and R21 under pin 8 on F.Cu, their grounds to the exposed pad; the block becomes two-layer. A reworked layout is a new block that needs its own DRC and review (as `ldo-ldl1117` was), not an edit to this cut |
| 2 | C20 is 1.8 mm (pad edge) / 2.7 mm (track) from VIN, and its ground loop closes only through the board's pour (the exposed pad has no via in the block; CC1/CC2 leave between C20 and U3) | **Accepted as a finding, declined in this cut** (as 1). Next revision: C20 at 90° left of pin 1 (~(−2.4, 1.25)), its ground on the track to the exposed pad, 2–4 vias in the pad once In2 is clear. Meanwhile the board's job lists the front pour as part of the decoupling path |
| 3 | ISET is 2 A while FINDINGS spoke of a 3 A charger | **Fixed in FINDINGS**: the block asks 2 A, a board must match ISET to its load (22.6 kΩ for 3 A). ISET stays inside the block: making it a port would change the cut's partition, and the source board chose 2 A deliberately |
| 4 | The absolute-maximum check covered only the 5 V plug-in ring; a 15 V interruption may ring VBUS to 20–25 V | **Recorded** above, with the right limit (VIN 30 V) and the hand estimate; added to the board's job (simulate it or fit a TVS). Not simulated here: the source board's simulation has no such corner |
| 5 | No system-level ESD on CC1/CC2 | **Added to the board's job**, with the CC-to-VBUS short that rules out a 5 V array |
| 6 | R20's ground pad has no block copper | **Added to the board's job** (it relies on the pour); goes away with 1 |
| 7 | `min_track_width` 0.12 does not match the narrowest track (0.187 mm) | **Fixed**: 0.18 mm, in all four blocks cut from this board |
| 8 | The copper extent was measured on centrelines | **Fixed**: to the copper's edges, in all four |
| 9 | C20 is ~0.22 µF at 15 V (0603 1 µF X5R); a 1–2.2 µF 50 V X7R 0805 keeps the datasheet's 1 µF | **Declined in this cut** (a part change is a new block); recorded for the next revision, inside USB's 10 µF attach limit |
| 10 | Two more board items: I²C pull-ups from a rail live without VBUS; VSET's switch run is high-impedance | **Added to the board's job** |
