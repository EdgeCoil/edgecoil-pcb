# rtc-pcf85063a: findings and what the board must do

Anchor U9. **Copper extent: x −11.25 … 2.10 mm, y −4.50 … 6.15 mm**, to the copper's edges (tracks and vias with their widths; parts' pads and courtyards reach further) from U9.
C51's pads and cell reach beyond it (below). Cut from the date-label-printer at **rev B** (board 92af546:
re-placed and re-routed to answer this block's rev A review, re-audited in rounds 5–7 to CLEAN, ERC/DRC
clean; post-layout simulation with routed copper and a 200 × 23 Monte Carlo, "sim4", PASS). All of the
block's copper is on F.Cu (18 items, 5 GND vias down to the ground plane); rev A's VRTC run on In2 is gone.

Datasheets cited: **NXP PCF85063A Rev. 7.3** (14 July 2026), **Seiko SC-32S** (the LCSC C97604 sheet),
**Nexperia BAV170** (1 April 2023). Table and section numbers below are theirs.

## What is in it

- **U9 PCF85063ATT/AJ** (TSSOP-8, C165608, `lp` footprint): I²C at 0x51, timekeeping from 0.9 V
  (Table 40, interface inactive), **I²C from 1.8 V** (Table 40, interface active; production-tested at
  1.8 V, note 2), an oscillator-stop flag, **no battery pin**, so the backup sits on VDD behind a diode.
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
- **TP6** (1 × 1 mm pad) on VRTC: a probe point. It has no GND pad beside it, so it does **not** take a
  discharge resistor by itself (below).
- **Ports: 3V3, GND, SDA, SCL.** **INT (pin 3) is not used**, so it is not a port; **CLKOUT (pin 7)
  is open** (no test pad), and on at every power-up until firmware turns it off.
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
  with CLKOUT off (Table 40, at VDD 3.3 V with SCL/SDA at VDD or VSS; sample-tested, note 4; specified
  with a 60 kΩ crystal where the SC-32S is 70 kΩ max). SDA and SCL leak up to ±0.3 µA each with the bus
  at 0 V (Table 40, ILI; 3V3 off, pull-ups to 3V3). D2 leaks ≤ 80 nA (BAV170 IR at 150 °C; 5 nA at 25 °C).
- **Start voltage, in board terms: ΔV = (3V3's DC minimum − 0.9 V) − 0.9 V.** The first 0.9 V is D2's
  only guaranteed drop (VF ≤ 0.9 V at 1 mA), the second the RTC's timekeeping minimum. On the source
  board (3V3 ≥ 3.23 V): start **≥ 2.33 V**, **ΔV ≈ 1.43 V**. Typically it starts near 2.8 V (ΔV ≈ 1.9 V).
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
- **A simulated hold-up must start C51 at the guaranteed start voltage** (`.ic`), not at the model's
  operating point: the DBAV170 model's VF sits 0.04–0.10 V below the BAV170's maxima, so from 3.3 V it
  settles VRTC at ~2.85 V, which flatters the hold-up (`model.inc`).

## Power-up: the RTC is unreachable for the first minute or so with C51 empty

With C51 empty, VRTC rises with τ = R52 × C51 ≈ 47 s (56 s at +20 %). It passes the RTC's 0.9 V after
~23–27 s and **the 1.8 V where its I²C is specified after ~67 s (80 s at +20 %)** on the block model; the
model's diode drops less than the guaranteed maximum, so allow **~70–85 s**. Until then U9 NACKs or
answers unreliably: **a CLKOUT-off or time write made at boot lands on an unpowered RTC**, which then
comes up with CLKOUT on (costing backup current) and the oscillator-stop flag set, and the first SNTP
time written in that window is lost.

The ramp is also far slower than NXP's recommended power-up (Section 13.1: VDD to its level "within tens
of microseconds", monotonic; a slow ramp can cause a POR failure, a stuck bus or wrong registers). That
is not avoidable with an EDLC on VDD; the firmware rules below are what make it safe.

## Accepted, and carried by the block

- **Charging**: an empty EDLC draws **~23 mA** from 3V3 (sim4: VRTC 19.1 mV 390 ms after power-up with
  0.47 F, `MODE-15_s0`; the block model gives 23.1 mA). Bounds: a silicon junction at ~30 mA drops
  **≥ ~0.6 V**, so with 3V3 at its 3.33 V DC maximum the current is **≤ 27 mA, 75 mW in R52**; the hard
  bound (VF → 0, 3V3 at its 3.37 V simulated peak) is **33.7 mA, 114 mW**, briefly above an 0603's
  100 mW rating at 70 °C, for seconds (it falls as e^(−2t/τ), and a real cell's ESR lowers it). Either is
  far inside the BAV170's 215 mA. sim4 carries the charge as a 3V3 load from plug-in (empty, 0 Ω ESR, the
  heaviest case): every 3V3 limit holds; it is also why 3V3 is still at 1.39 V 5 ms after unplugging
  there (`MODE-15_s5`; the C3 resets either way).
- **One diode element**: rev A paralleled both; one carries the charge current against 215 mA and leaks
  half as much. The BAS416 and 1N4148WS were checked and declined on guaranteed leakage at temperature.
- **Bus levels**: SDA/SCL limiting value 6.5 V whatever VDD is (Table 39; 5.5 V operating, Table 40);
  VIH 0.7 × VDD (1.96 V at 2.8 V). A 3V3 bus over an RTC at 2.8 V is inside its ratings.
- **Polarity**: C51 + (square pad 1) on VRTC, toward U9; D2's cathode (pin 3) on VRTC. The source
  board marks C51's + on both sides (its footprint's own "+" is lost at 180°): a board using the block
  marks it itself.
- **Not in the model** (as in sim4): U9, Y1, C50 (µA, and 100 nF beside 0.47 F) and TP6. `model.inc` has
  `irtc` and `ileak` for a hold-up run (0 by default, as in sim4), and `c51` (0.47 F; a tiny value stands
  for "not fitted").
- **JLC**: U9, Y1, D2, R52 and C50 are assembled (`jlc_verify` passes each); TP6 is a bare pad; C51
  carries no LCSC number, so it is left out of the JLC BOM.

## Frequency accuracy, before and after trim

Assumptions: Y1 cut for 7 pF (its part number; the SC-32S sheet lists 6 and 12.5 pF, so confirm the
7 pF grade with the supplier); C0 1.0 pF typ (SC-32S); **C1 ≈ 3.4 fF, ASSUMED** (typical of a 32 kHz
tuning fork; the sheet gives none); pulling Δf/f = (C1/2)·[1/(C0 + CL) − 1/(C0 + 7 pF)]. The load is
the RTC's integrated CL(itg), **4.2–9.8 pF** at the 7 pF setting (Table 40), **plus board stray**:
~0.5–1 pF per pin (pads and 2.45 mm of 0.2 mm track over the ground plane on In1, plus the package),
in series across the crystal, so **+0.25–0.5 pF**.

| Term | Range |
|---|---|
| Load: CL(itg) 4.2 → 9.8 pF with stray | **+99 … −62 ppm** (+114 ppm at 4.2 pF with no stray) |
| Crystal tolerance at 25 °C | ±20 ppm |
| Temperature: −0.030 ppm/°C² ± 10 %, turnover 25 ± 5 °C | 0 … −13 ppm over 10–40 °C |
| Ageing, first year | ±3 ppm |

Untrimmed, worst case ≈ **+122 / −98 ppm (~10 s/day)**. The **Offset register** (Section 7.2.3) spans
**+273 / −278 ppm** in 4.34 ppm steps (MODE 0), so a per-unit trim covers all of it; what is left is the
temperature parabola, ageing and ±2.2 ppm of step. Measure per unit (below). The source board set no
accuracy requirement (it re-syncs over the network): set one if it matters.

## Measure at bring-up

- **The hold-up**, with the fitted EDLC, against the 24 h target (or its decay rate over a day and the
  sum above). Record the cell and its measured leakage.
- **That a low VRTC never holds the I²C bus** (a discharged or slowly rising RTC on the bus with the
  other devices): if the bus does not answer, firmware treats the time and the bus as unknown (below).
  To force the case, drain VRTC with a resistor clipped across C51's pads, or from TP6 to any GND point.
- **The frequency, per unit**: probe U9 pin 7 (CLKOUT) directly, with a bring-up firmware build that
  leaves CLKOUT on, then write the Offset register. CAP_SEL resets to 0 (7 pF), matching Y1.

## The board's job

- **Nothing on the crystal's layer under Y1** (the SC-32S sheet: "no pattern under"), and a ground plane
  between Y1 and any signal on other layers. The source board: only IO7_RX passes Y1's edge, on B.Cu,
  under the solid In1 ground and the In2 pour.
- **3V3** able to give ~27 mA (33.7 mA hard bound) to an empty EDLC at power-up, and **I²C pull-ups**
  (the source board: 4.7 kΩ to 3V3).
- **Firmware** (the source board's rules F12, F13, M3), written for the power-up above:
  - **F12: CLKOUT off whenever the RTC needs it, not only at boot.** Poll U9 **every 10 s until it
    answers with COF = 111 and the time set**, and after that **on every SNTP sync**. Whenever it NACKs,
    has the oscillator-stop flag set, or COF ≠ 111: apply F13, write COF = 111, and write the time once
    synced. COF resets to 32.768 kHz after every reset, including each time the backup runs out, and the
    hold-up sum assumes it off.
  - **M3: treat the time as invalid while the oscillator-stop flag is set**, until the network has
    set it, and never act on a guessed time (the source board refuses to print a date until then).
  - **F13: recover the RTC when it reads wrong.** NXP requires VDD from 0 V at power-up, else a
    software reset (Sections 7.2, 7.2.1.3, 13.1); with an EDLC, a residual or slowly rising VRTC is the
    normal case. I²C bus recovery (clock SCL until SDA is released), the software reset (58h to
    Control_1), STOP, START. Nothing on the board can power-cycle U9 (its VDD is the EDLC), so a latched
    RTC would hold the shared bus until the EDLC drains.
- **3V3 must fall to 0 V and stay there when unpowered**: the RTC's currents are specified with SDA/SCL
  at VDD or VSS, and pull-ups to a rail parked mid-level bias its inputs outside that. NXP recommends
  pull-ups on VDD's supply; here they are on 3V3 while VDD is VRTC: inside the 6.5 V ratings, a
  recorded deviation.
- **C51 is fitted by hand: after reflow, discharged, + to the square pad, and clean the flux** (residue
  across a 5 mm pitch can cost microamps, the whole budget). Mark its polarity on silk.
- **C51's real outline is not its footprint's.** A V-type cell stands on its edge with both leads in the
  disc's plane, so its plan shadow is a **~13 × 5–7 mm rectangle along the pad line**, centred on the pad
  midpoint (−13.6, 4.3) from U9: x −20.1 … −7.1, y 0.8 … 7.8 for 13 × 7 mm. Its corners sit at
  r ≈ 7.0–7.4 mm, **outside the footprint's 6.5 mm courtyard circle**, so a courtyard check does not
  see them. **Keep a 13 × 7 mm rectangle about the pad midpoint clear** (both orientations if unsure:
  turned 90° it spans x −17.1 … −10.1, y −2.2 … 10.8), **or fit the cell 1–2 mm proud of the board**. On
  the source board a 13 × 7 mm shadow pressed flat overlaps a neighbouring resistor pad's corner by
  ~0.1 × 0.3 mm, so its fitting note says 1–2 mm proud. Every block pad is clear of both rectangles.
- **Height for an enclosure**: the cell stands **≈ 14–15 mm** above the board, ~16–17 mm fitted proud.
- **INT (pin 3) is open-drain and open**: a board that wants alarm wake routes it itself, with a
  pull-up.
- **The block's design rules** (block.json): `solid_pads` (U9.4) through `Block.solid_pads(refs)`,
  `min_track_width` 0.18 mm, and a ground plane under F.Cu for the five GND vias to land on.
- **Keep parts out of the copper extent** and of C51's outline (above); C51's pads (2.4 mm) are at
  (−11.1, 4.3) and (−16.1, 4.3); the VRTC track from TP6 to pad 1 runs under the cell. Keep other-net
  copper at C51's pins clear for hand soldering on both sides.

## Rev A review findings and how rev B answers them

The rev A cut (6f36126) was reviewed alone by one fresh reviewer: NOT CLEAN, 1 blocker, 5 should-fix,
4 suggestions. Rev B (92af546) is the source board's revision for them.

| # | Rev A finding | Rev B |
|---|---|---|
| 1 | BLOCKER: 48 h unmet on guaranteed figures | **Closed by decision, not by design**: the requirement is now a ≥ 24 h *target*, measured at bring-up, with C51 optional and the board working without it (the flag blocks use of the time until the network sets it). C51 is now 0.47 F, which gives ~5 µA of leakage room against 24 h. **No guarantee exists**: that is stated, not solved |
| 2 | Power-on reset missing; CLKOUT off only "at first boot" | **Resolved, after a correction**: rev B first moved the write to "every boot", which the rev B review (B1, below) showed still lands on an unpowered RTC; F12 now polls every 10 s until COF = 111 and the time are set, then on every SNTP sync, with F13 (bus recovery, software reset, STOP/START) whenever U9 NACKs or reads wrong |
| 3 | Board duties missing: 3V3 to 0 V, flux, fit discharged, pull-ups vs VDD's supply, INT routing | **Partly**: fitting and flux are in the source board's record (R6 and its ordering notes). 3V3 falling to 0 V, the pull-up deviation and INT stay **board duties carried here** (above); the source board leaves INT unused |
| 4 | CAP_SEL; frequency accuracy unbounded | **Recomputed** (above: ≈ +122 / −98 ppm untrimmed, inside the Offset register's range); the per-unit trim is a bring-up item; no accuracy requirement is set |
| 5 | C50 6.7 mm and two vias from VDD | **Resolved**: C50 beside pin 8 (1.8 mm of track), its own GND via |
| 6 | No ground via in the block | **Resolved**: GND vias at U9.4, at C50.2 and three round Y1 (five in all) |
| 7 | Backup path accreted; VRTC down to In2 and back; two diodes in parallel | **Resolved**: D2 by pin 8, R52 beyond it (3V3_RTC 2.1 mm), VRTC on F.Cu throughout, one BAV170 element |
| 8 | Y1 4 mm out on unequal traces; OSCO under U9; a VRTC via by OSCI | **Resolved**: Y1 2.2 mm below pins 1–2 on equal traces, nothing under U9, no VRTC near the crystal, a guard of GND vias and pour |
| 9 | From scratch, an RTC with a backup pin (RV-3028-C7) | **Recorded trade-off, unchanged**: the PCF85063A was chosen for ESPHome support |
| 10 | Charging current not a guaranteed bound; extent excluded C51 | **Carried**: ≤ 27 mA on a stated VF, 33.7 mA hard bound; C51's outline is stated above |

## Independent review of the rev B block (round 1) and what was done

NOT CLEAN: 1 blocker, 5 should-fix, 4 suggestions.

| # | Finding | Response |
|---|---|---|
| B1 | With C51 empty, VRTC needs ~70–85 s to reach I²C's 1.8 V; a boot-time CLKOUT-off (and the first SNTP write) lands on an unpowered RTC | **Fixed at the source board** (F12: poll every 10 s, then on every SNTP sync, F13 on any fault); stated here (Power-up, The board's job) |
| S1 | Datasheets not on file | **Fixed**: the PCF85063A, SC-32S and BAV170 sheets are on file for the audit; figures cite their tables and sections |
| S2 | A V-type cell's shadow is a 13 × 5–7 mm rectangle, outside the courtyard circle; ~14–15 mm tall; on the source board it can touch a neighbouring pad flush | **Stated** (The board's job); the source board fits it 1–2 mm proud. **Footprint change declined for this cut** (it needs a re-cut); next revision: a courtyard rectangle for the vertical cell |
| S3 | The rev A ±ppm figures could not be reproduced; stray and temperature missing | **Recomputed** with stated assumptions, stray and the parabola; the Offset register covers it |
| S4 | Two sim figures not in the source board's results | **Traced** to the sim4 outputs (`MODE-15_s0`, `MODE-15_s5`) and handed on for the results record |
| S5 | DBAV170 sits 0.04–0.10 V below the maxima it claims to fit | **Fixed** in the shared model's comment; a hold-up run starts C51 at the guaranteed start voltage (here, `model.inc`) |
| G1 | TP6 cannot take a discharge resistor (no GND pad beside it) | **Declined for this revision**: clip a resistor across C51's pads, or from TP6 to any GND; wording fixed. Next revision: a DNP 0603 from VRTC to GND |
| G2 | No CLKOUT test pad | **Declined**: probe U9 pin 7 directly, with a bring-up build that leaves CLKOUT on. Next revision: a pad |
| G3 | Start voltage and the charging bound not in board terms | **Fixed**: ΔV = (3V3 DC min − 0.9 V) − 0.9 V; ≤ 27 mA at VF ≥ 0.6 V, 33.7 mA / 114 mW hard bound |
| G4 | Source-board wording ("Schottky"; Monte Carlo) | Fixed at the source board / in the README |
