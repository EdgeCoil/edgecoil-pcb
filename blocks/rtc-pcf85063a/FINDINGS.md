# rtc-pcf85063a: findings and what the board must do

Anchor U9. **Copper extent: x −19.62 … 5.46 mm, y −2.35 … 5.62 mm**, to the copper's edges (tracks and vias with their widths; parts' pads and courtyards reach further) from U9: the EDLC sits 19.5 mm
to the left (where the source board had room for a 12.5 mm through-hole can), its VRTC run on In2.
Cut from the date-label-printer (four DFM audit rounds, CLEAN; post-layout simulation with routed
copper and a 200 × 9 Monte Carlo, "sim3").

## What is in it

- **U9 PCF85063ATT/AJ** (TSSOP-8, C165608, `lp` footprint): I²C at 0x51, timekeeping from 0.9 V to
  5.5 V, an oscillator-stop flag, **no battery pin**, so the backup sits on VDD behind a diode.
  ESPHome supports it (`pcf85063`). **Its GND pin (4) joins the pour solid** (block.json
  `solid_pads`): the tracks round it leave room for one thermal spoke of the zone's two, and a reflowed
  0.3 mm pin needs no relief.
- **Y1** 32.768 kHz, **7 pF** load (SC-32S, C97604, `lp` footprint), 4 mm from U9.
- **C50** 100 nF on VRTC.
- **The backup**: **C51**, a 0.22 F 5.5 V EDLC footprint (radial, 5.0 mm pitch, Ø ≤ 12.5 mm),
  **hand-fitted, part not chosen**, charged from 3V3 through **R52 100 Ω** and **D2 BAV170** (both
  diodes in parallel, common cathode on VRTC), so the EDLC cannot drain back into a dead 3V3.
- **Ports: 3V3, GND, SDA, SCL.** **INT (pin 3) is not used**, so it is not a port; **CLKOUT (pin 7)
  is open**, and on at power-up until firmware turns it off.
- **The `lp` library** (block.json `local_libs`): U9 and Y1 are LCSC's parts (easyeda2kicad). The
  toolkit ships no third-party library; a board supplies its own copy (`libs=`).

## The open item: C51's part, and the hold-up it gives. **Not met until a part is chosen.**

The requirement is **≥ 48 h of timekeeping without power at 40 °C**. On guaranteed figures (NXP data
sheet rev 7.3): the RTC draws **0.50 µA max at 50 °C** with CLKOUT off (sample-tested, and specified
with a 60 kΩ crystal where the SC-32S is 70 kΩ max); SDA and SCL leak up to ±0.3 µA each while the
bus sits at 0 V; the BAV170 leaks nA. **≈ 1.1 µA, plus the EDLC's own leakage.** The RTC keeps time
to 0.9 V. VRTC starts at 3V3 less the diode: about 2.8 V with a typical drop at µA, but the only
guaranteed drop is VF ≤ 0.9 V at 1 mA, so **on guaranteed figures it starts at ~2.33 V: ΔV ≈ 1.43 V**.

- At −20 % (0.176 F) with no EDLC leakage: 0.176 × 1.43 / 1.1 µA ≈ 63 h.
- At −20 % with 1 µA of EDLC leakage: ≈ 33 h. **48 h allows at most ~0.36 µA of EDLC leakage at
  40 °C, after ageing**; EDLCs commonly lose ~30 % of capacitance by end of life.
- **Choose C51 from a data sheet that states its leakage at temperature**: 0.47 F (at −20 %, 0.376 F,
  the leakage budget becomes ~2.0 µA), or a 0.22 F part guaranteeing ≤ 0.36 µA. 5.5 V, coin-type,
  5.0 mm pitch, Ø ≤ 12.5 mm; record its height. Redo the sum on minimum capacitance, maximum leakage
  and the guaranteed start voltage.
- **The sum assumes a full charge**: a coin EDLC's ESR and charge redistribution take far longer than
  τ = 22 s, and its leakage just after charging is far above the steady-state figure. State a minimum
  powered time before the 48 h applies, and measure the hold-up at bring-up.
- (An audit raised the hold-up; it stays open by decision: C51 is bought separately and fitted by
  hand, so it does not hold the board.)

## Accepted, and carried by the block

- **Charging**: R52 100 Ω gives τ ≈ 22 s at 0.22 F. An empty EDLC draws **~24 mA** from 3V3; with
  no guaranteed minimum VF and 3V3 at its top, ~29 mA and 82 mW in R52 (inside its 100 mW, and brief;
  a real coin EDLC's ESR lowers it). It was 1 kΩ (≈ 4 min to a working RTC voltage
  after a deep discharge) until an audit. The source board's simulation counts it as the heaviest load
  on 3V3 at plug-in, and it is why 3V3 falls to 1.28 V 5 ms after unplugging there (the C3 resets
  either way).
- **Bus levels** (R7): SDA/SCL absolute maximum 6.5 V whatever VDD is; VIH 0.7 × VDD (1.96 V at 2.8 V).
  A 3V3 bus over an RTC at 2.8 V is inside its ratings.
- **Polarity** checked in audit: C51 + (square pad) on VRTC, D2's common cathode on VRTC.
- **C51's pins** are hand-soldered: every one is ≥ 0.40 mm from other-net copper on the back; the front
  tracks under its body come to 0.22–0.25 mm (under the can).
- **Not in the model** (as in the source board's simulation): U9, Y1 and C50 (µA, and 100 nF beside
  0.22 F). `model.inc` has `irtc` and `ileak` for a hold-up run (0 by default, as there).
- **JLC**: U9, Y1, D2, R52 and C50 are assembled (`jlc_verify` passes each); C51 carries no LCSC number,
  so it is left out of the JLC BOM.

## Measure at bring-up

- **The hold-up**, with the chosen EDLC, against 48 h (or its decay rate over a day and the sum above).
- **That a low VRTC never holds the I²C bus** (a discharged RTC on the bus with the PD controller and
  anything else): if the bus does not answer, firmware must treat the time and the bus as unknown.
- **The frequency, per unit**, on CLKOUT before firmware turns it off, then write the Offset register.
  CAP_SEL resets to 0 (7 pF), matching Y1; but the RTC's integrated 7 pF load is guaranteed only to
  4.2–9.8 pF, which pulls the frequency by about +76 / −55 ppm, ±90 ppm (~8 s/day) worst case with the
  crystal's ±20 ppm. No accuracy requirement was set for the source board: set one if it matters.

## The board's job

- **3V3** able to give ~26 mA to an empty EDLC at power-up, and **I²C pull-ups** (the source board:
  4.7 kΩ to 3V3).
- **Firmware**: write **COF = 111 (CLKOUT off) on every boot**: it resets to 32.768 kHz after every
  reset, including each time the backup runs out, and the hold-up sum assumes it off. Treat the time
  as **invalid when the oscillator-stop flag is set**, and never act on a guessed time. **Then
  recover the RTC**: NXP requires VDD at 0 V at power-up, else a software reset; with an EDLC,
  re-powering from a residual VRTC is the normal case after a long outage. If the flag is set or the
  registers read implausibly: I²C bus recovery, the software reset (58h to Control_1), STOP, START.
  Nothing on the board can power-cycle U9 (its VDD is the EDLC), so a latched RTC holds the shared
  bus (the PD controller is on it on the source board) until the EDLC drains; a test pad on VRTC for
  a discharge resistor is cheap insurance.
- **3V3 must fall to 0 V and stay there when unpowered**: the RTC's currents are specified with SDA/SCL
  at VDD or VSS, and pull-ups to a rail parked mid-level bias its inputs outside that. NXP recommends
  pull-ups on VDD's supply; here they are on 3V3 while VDD is VRTC: inside the 6.5 V ratings, a
  recorded deviation.
- **C51 is hand-soldered: clean the flux** (residue across a 5 mm pitch can cost tenths of a µA, the
  whole budget), fit it discharged and after reflow, and mark its polarity on silk.
- **INT (pin 3) is open-drain and open**: a board that wants alarm wake routes it itself, with a
  pull-up.
- **Choose C51 and redo the hold-up sum** (above).
- **The block's design rules** (block.json): `solid_pads` (U9.4) through `Block.solid_pads(refs)`,
  `min_track_width` 0.18 mm, four copper layers.
- **Keep parts out of the copper extent and C51's can**: its pads reach x −20.7 mm and the 12.5 mm can
  spans x −23.25 … −10.75, y −0.75 … 11.75 mm from U9.

## Independent review of the block alone (and what was done)

One fresh reviewer, given only this directory and the toolkit's README, with NXP's data sheet rev 7.3:
NOT CLEAN, 1 blocker, 5 should-fix, 4 suggestions. The absolute maxima and the crystal are within
limits; the topology (a diode-OR into an EDLC with a low-leakage diode) suits an RTC with no battery
pin. Layout findings are about the source board's copper, which this block reproduces exactly (the
board stays canonically the same): **declined in this cut, recorded for the next revision**.

| # | Finding | Response |
|---|---|---|
| 1 | BLOCKER: 48 h is unmet on guaranteed figures, and the sum was optimistic (a typical diode drop; 44 h where the guaranteed start gives ~33 h) | **Accepted and fixed in FINDINGS**: the sum redone on the guaranteed start (ΔV 1.43 V), the leakage budget stated (~0.36 µA at 0.22 F; ~2.0 µA at 0.47 F), "≈ 55 h" dropped, the full-charge and ageing caveats added. The requirement stays **open until C51 is chosen** (it was already open by decision; it does not change the cut) |
| 2 | Power-on reset missing; "CLKOUT off at first boot" wrong (COF resets after every reset) | **Fixed**: COF on every boot; bus recovery and software reset; the VRTC discharge pad suggested |
| 3 | Board duties missing: 3V3 falls to 0 V, flux cleaning, fit C51 discharged, pull-ups vs VDD's supply, INT routing | **Added** |
| 4 | CAP_SEL can be closed (resets to 7 pF); frequency accuracy unbounded (±90 ppm worst) | **Fixed**: CAP_SEL closed; per-unit trim at bring-up; an accuracy requirement is the board's to set |
| 5 | C50 is at GND pin 4, ~6.7 mm and two vias from VDD (pin 8) | **Declined in this cut**. Next revision: C50 beside pin 8 with its own GND via |
| 6 | No ground via in the block: U9.4 and C50.2 reach In1 only through the F.Cu pour (one spoke at pin 4) | **Declined in this cut**; the board's pour is listed as the ground path. Next revision: a GND via at C50.2/U9.4 |
| 7 | The backup path accreted: 3V3_RTC detours (8.6 mm vs 3.6 mm), VRTC goes down to In2 and back; two paralleled diodes where one does (26 mA vs 215 mA each) | **Declined in this cut**. Next revision: D2 by pin 8, R52 beyond it, VRTC on F.Cu, one diode |
| 8 | Y1 is 4 mm out with unequal traces (3.5 / 5.7 mm), OSCO under U9, a VRTC via 0.28 mm from OSCI (shielded by In1, so not a defect) | **Declined in this cut**; next revision ~2 mm below pins 1–2, equal ~1 mm traces, a ground guard |
| 9 | From scratch, an RTC with a backup pin (e.g. RV-3028-C7) would make 48 h easy with a reflowable cap | **Recorded as the trade-off**: the PCF85063A was chosen because ESPHome supports it out of the box (the source board's firmware requirement); its I²C inputs stay on the backup supply and leak more than the RTC draws |
| 10 | 26 mA / 68 mW is not a guaranteed bound; the extent excluded C51's pads and can | **Fixed**: ~29 mA / 82 mW worst; the can's outline is now the stated keep-out |
