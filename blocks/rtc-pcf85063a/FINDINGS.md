# rtc-pcf85063a: findings and what the board must do

Anchor U9. **Copper extent: x −11.25 … 2.10 mm, y −4.50 … 6.15 mm**, to the copper's edges (tracks and vias with their widths; parts' pads and courtyards reach further) from U9.
C51's pads and can reach beyond it (below). Cut from the date-label-printer at **rev B** (board 92af546:
re-placed and re-routed to answer this block's rev A review, re-audited in rounds 5–7 to CLEAN, ERC/DRC
clean; post-layout simulation with routed copper and a 200 × 23 Monte Carlo, "sim4", PASS). All of the
block's copper is on F.Cu (18 items, 5 GND vias down to the ground plane); rev A's VRTC run on In2 is gone.

## What is in it

- **U9 PCF85063ATT/AJ** (TSSOP-8, C165608, `lp` footprint): I²C at 0x51, timekeeping from 0.9 V to
  5.5 V, an oscillator-stop flag, **no battery pin**, so the backup sits on VDD behind a diode.
  ESPHome supports it (`pcf85063`). **Its GND pin (4) joins the pour solid** (block.json
  `solid_pads`) and has its own GND via 1.1 mm away.
- **Y1** 32.768 kHz, **7 pF** load (SC-32S, C97604, `lp` footprint), 2.2 mm below pins 1–2 on two
  equal ≈ 2.45 mm 0.2 mm traces, inside a guard of three GND vias (either end and below) and the pour.
- **C50** 100 nF (C14663) beside pin 8 (VDD): 1.8 mm of track, with its own GND via.
- **The backup**: **D2**, **one BAV170 element** (C109309; pin 1 anode on 3V3_RTC, pin 3 cathode on
  VRTC, **pin 2 open**), and **R52 100 Ω** (C22775) beyond it from 3V3, so the EDLC cannot drain back
  into a dead 3V3. D2's cathode is 3.3 mm from pin 8; 3V3_RTC is a single 2.1 mm track.
- **C51**: a footprint for a **0.47 F 5.5 V V-type coin EDLC** (CP_Radial_D12.5mm_P5.00mm: 5.0 mm
  pitch, + on the square pad 1, toward U9). **Optional, fitted by hand after assembly; no part is
  specified or guaranteed** (no LCSC number, so it is left out of the JLC BOM). Not a 2.7 or 3.3 V cell:
  VRTC sits near 2.8–3.0 V.
- **TP6** (1 × 1 mm pad) on VRTC: a test point and the place for a discharge resistor (below).
- **Ports: 3V3, GND, SDA, SCL.** **INT (pin 3) is not used**, so it is not a port; **CLKOUT (pin 7)
  is open**, and on at every power-up until firmware turns it off.
- **The `lp` library** (block.json `local_libs`): U9 and Y1 are LCSC's parts (easyeda2kicad). The
  toolkit ships no third-party library; a board supplies its own copy (`libs=`).

## The hold-up: a target of ≥ 24 h, measured at bring-up, not guaranteed

The source board decided (its requirements R2/R6) that C51 is **optional** and its hold-up a
**target of ≥ 24 h without power at 40 °C, measured with the fitted cell at bring-up**. It is not a
guarantee because no 0.47 F coin EDLC found states a leakage current at temperature, and the hold-up
turns on exactly that. **The board must work without C51**: then C50 alone holds VRTC for about a
tenth of a second, every power cut sets the oscillator-stop flag, and firmware takes the time from the
network before it trusts the clock (below).

The sum, for whoever fits a cell and measures it. Assumptions, all stated:

- **Loads at 40 °C ≈ 1.2 µA, plus the EDLC's own leakage.** The RTC draws **0.50 µA max at 50 °C**
  with CLKOUT off (NXP data sheet rev 7.3, Table 40; sample-tested, and specified with a 60 kΩ crystal
  where the SC-32S is 70 kΩ max). SDA and SCL leak up to ±0.3 µA each with the bus at 0 V (3V3 off,
  pull-ups to 3V3). D2 leaks ≤ 80 nA (its 150 °C figure; 5 nA at 25 °C).
- **Start voltage.** VRTC starts at 3V3 less D2's drop. The only guaranteed drop is VF ≤ 0.9 V at 1 mA,
  so on guaranteed figures it starts at **≥ 2.33 V** (the source board's figure: 3V3 at ~3.23 V, its simulated minimum under load, less 0.9 V): **ΔV ≈ 1.43 V** to the
  RTC's 0.9 V. Typically it starts near 2.8 V (ΔV ≈ 1.9 V).
- **Capacitance** at −20 % (0.376 F), new, **fully charged** (see the last point).

| EDLC leakage | Hold-up (0.376 F, ΔV 1.43 V) |
|---|---|
| 0 | ≈ 127 h |
| 5 µA | ≈ 24 h |
| 10 µA | ≈ 13 h |

- **24 h allows ~5.0 µA of EDLC leakage at 40 °C** on these figures. EDLCs commonly lose ~30 % of
  capacitance by end of life; at 0.263 F the allowance falls to ~3.2 µA. At the typical start (ΔV 1.9 V)
  it is ~7 µA new.
- **The sum assumes a full charge.** τ = R52 × C51 = 47 s, but a coin EDLC's ESR and charge
  redistribution take far longer, and its leakage just after charging is far above the steady-state
  figure. Give it a few minutes powered for a useful charge; measure the hold-up after a long powered
  spell, or its decay rate over a day and redo the sum above.

## Accepted, and carried by the block

- **Charging**: an empty EDLC draws **~23 mA** from 3V3 (sim4: VRTC 19.1 mV 390 ms after plug-in with
  0.47 F, the model's VF ≈ 1.0 V at that current; `model.inc` gives the same, 23.1 mA). The source board's
  worst case, with 3V3 at its top and no guaranteed minimum VF, is **~29 mA**: ~84 mW in R52 for the first
  seconds (an 0603 rated 100 mW; it falls as e^(−2t/τ), and a real cell's ESR lowers it), against the
  BAV170's 215 mA. It reaches the RTC's 0.9 V in roughly 20 s from empty. sim4 carries it as a 3V3
  load from plug-in (empty, 0 Ω ESR, the heaviest case): every 3V3 limit holds (3V3 3.30 V peak at plug-in;
  3.21 V minimum with copper elsewhere); it is also why 3V3 is still at 1.39 V 5 ms after unplugging there
  (the C3 resets either way).
- **One diode element**: rev A paralleled both; one carries 29 mA against 215 mA and leaks half as
  much. The BAS416 and 1N4148WS were checked and declined on guaranteed leakage at temperature.
- **Bus levels** (R7): SDA/SCL absolute maximum 6.5 V whatever VDD is; VIH 0.7 × VDD (1.96 V at 2.8 V).
  A 3V3 bus over an RTC at 2.8 V is inside its ratings.
- **Polarity**: C51 + (square pad 1) on VRTC, toward U9; D2's cathode (pin 3) on VRTC. The source
  board marks C51's + on both sides (its footprint's own "+" is lost at 180°): a board using the block
  marks it itself.
- **Not in the model** (as in sim4): U9, Y1, C50 (µA, and 100 nF beside 0.47 F) and TP6. `model.inc` has
  `irtc` and `ileak` for a hold-up run (0 by default, as in sim4), and `c51` (0.47 F; a tiny value stands
  for "not fitted").
- **JLC**: U9, Y1, D2, R52 and C50 are assembled (`jlc_verify` passes each); TP6 is a bare pad; C51
  carries no LCSC number, so it is left out of the JLC BOM.

## Measure at bring-up

- **The hold-up**, with the fitted EDLC, against the 24 h target (or its decay rate over a day and the
  sum above). Record the cell and its measured leakage.
- **That a low VRTC never holds the I²C bus** (a discharged RTC on the bus with the other devices): if
  the bus does not answer, firmware treats the time and the bus as unknown (F13, below). TP6 takes a
  discharge resistor to force the case.
- **The frequency, per unit**, on CLKOUT before firmware turns it off, then write the Offset register.
  CAP_SEL resets to 0 (7 pF), matching Y1; but the RTC's integrated 7 pF load is guaranteed only to
  4.2–9.8 pF, which pulls the frequency by about +76 / −55 ppm, ±90 ppm (~8 s/day) worst case with the
  crystal's ±20 ppm. The source board set no accuracy requirement (it re-syncs over the network): set
  one if it matters.

## The board's job

- **3V3** able to give ~29 mA to an empty EDLC at power-up, and **I²C pull-ups** (the source board:
  4.7 kΩ to 3V3).
- **Firmware** (the source board's rules F12, F13, M3):
  - **F12: write COF = 111 (CLKOUT off) on every boot.** It resets to 32.768 kHz after every reset,
    including each time the backup runs out, and the hold-up sum assumes it off.
  - **M3: treat the time as invalid while the oscillator-stop flag is set**, until the network has
    set it, and never act on a guessed time (the source board refuses to print a date until then).
  - **F13: recover the RTC when it reads wrong.** NXP requires VDD at 0 V at power-up, else a software
    reset; with an EDLC, re-powering from a residual VRTC is the normal case after an outage. If the flag
    is set or the registers read implausibly: I²C bus recovery (clock SCL until SDA is released), the
    software reset (58h to Control_1), STOP, START. Nothing on the board can power-cycle U9 (its VDD is the
    EDLC), so a latched RTC would hold the shared bus until the EDLC drains; TP6 is where to drain it.
- **3V3 must fall to 0 V and stay there when unpowered**: the RTC's currents are specified with SDA/SCL
  at VDD or VSS, and pull-ups to a rail parked mid-level bias its inputs outside that. NXP recommends
  pull-ups on VDD's supply; here they are on 3V3 while VDD is VRTC: inside the 6.5 V ratings, a
  recorded deviation.
- **C51 is fitted by hand: after reflow, discharged, + to the square pad, and clean the flux** (residue
  across a 5 mm pitch can cost microamps, the whole budget). Mark its polarity on silk.
- **INT (pin 3) is open-drain and open**: a board that wants alarm wake routes it itself, with a
  pull-up.
- **The block's design rules** (block.json): `solid_pads` (U9.4) through `Block.solid_pads(refs)`,
  `min_track_width` 0.18 mm, and a ground plane under F.Cu for the five GND vias to land on.
- **Keep parts out of the copper extent and out of C51's can.** C51's pad 1 is at (−11.1, 4.3) and
  pad 2 at (−16.1, 4.3) (pads 2.4 mm, reaching x −17.3); the can is centred at (−13.6, 4.3). A 12.5 mm can
  spans x −19.85 … −7.35, y −1.95 … 10.55; **a 13 mm can, which the source board allows, spans
  x −20.1 … −7.1, y −2.2 … 10.8**, exactly the footprint's courtyard, so keep other courtyards out of it
  (the courtyard check does not know the can may be 13 mm). Every block pad is ≥ 1 mm outside a 13 mm can;
  the VRTC track from TP6 to pad 1 runs under it. Keep other-net copper at C51's pins clear for hand
  soldering on both sides.

## Rev A review findings and how rev B answers them

The rev A cut (6f36126) was reviewed alone by one fresh reviewer: NOT CLEAN, 1 blocker, 5 should-fix,
4 suggestions. Rev B (92af546) is the source board's revision for them.

| # | Rev A finding | Rev B |
|---|---|---|
| 1 | BLOCKER: 48 h unmet on guaranteed figures | **Closed by decision, not by design**: the requirement is now a ≥ 24 h *target*, measured at bring-up, with C51 optional and the board working without it (the flag blocks use of the time until the network sets it). C51 is now 0.47 F, which gives ~5 µA of leakage room against 24 h. **No guarantee exists**: that is stated, not solved |
| 2 | Power-on reset missing; CLKOUT off only "at first boot" | **Resolved**: F12 (COF every boot) and F13 (bus recovery, software reset, STOP/START) in the source board's firmware rules; TP6 on VRTC for the discharge resistor |
| 3 | Board duties missing: 3V3 to 0 V, flux, fit discharged, pull-ups vs VDD's supply, INT routing | **Partly**: fitting and flux are in the source board's record (R6 and its ordering notes). 3V3 falling to 0 V, the pull-up deviation and INT stay **board duties carried here** (above); the source board leaves INT unused |
| 4 | CAP_SEL; frequency accuracy unbounded (±90 ppm) | **Still open, as before**: CAP_SEL is closed (resets to 7 pF); the per-unit trim is a bring-up item; no accuracy requirement is set (the source board re-syncs over the network) |
| 5 | C50 6.7 mm and two vias from VDD | **Resolved**: C50 beside pin 8 (1.8 mm of track), its own GND via |
| 6 | No ground via in the block | **Resolved**: GND vias at U9.4, at C50.2 and three round Y1 (five in all) |
| 7 | Backup path accreted; VRTC down to In2 and back; two diodes in parallel | **Resolved**: D2 by pin 8, R52 beyond it (3V3_RTC 2.1 mm), VRTC on F.Cu throughout, one BAV170 element |
| 8 | Y1 4 mm out on unequal traces; OSCO under U9; a VRTC via by OSCI | **Resolved**: Y1 2.2 mm below pins 1–2 on equal traces, nothing under U9, no VRTC near the crystal, a guard of GND vias and pour |
| 9 | From scratch, an RTC with a backup pin (RV-3028-C7) | **Recorded trade-off, unchanged**: the PCF85063A was chosen for ESPHome support |
| 10 | Charging current not a guaranteed bound; extent excluded C51 | **Carried**: ~29 mA / ~84 mW worst at 0.47 F; C51's pads and 13 mm can are stated as the keep-out above |
