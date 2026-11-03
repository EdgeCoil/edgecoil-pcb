# efuse-tps25947: findings and what the board must do

Anchor U4. **Copper extent: x −12.70 … 7.33 mm, y −7.93 … 6.05 mm**, to the copper's edges (tracks and vias with
their widths; parts' pads and courtyards reach further) from U4. Cut from the date-label-printer at **rev B** (board
92af546: re-placed and re-routed after the review of the rev A cut below; DFM audit rounds 5–8, CLEAN at round 8;
post-layout simulation with routed copper and a 200 × 23 Monte Carlo, "sim4", PASS). 88 copper items, 15 of them
vias; four layers: two EN tracks run on In2 and one VBUS link on B.Cu.

## What is in it, and what is not

- **U4 TPS259474L** (VQFN-10 2 × 2, C2864845): 2.7–23 V, 28 V absolute, RON 28.2 mΩ typ / 45 mΩ max,
  circuit breaker with latch-off, dVdt restart after an over-voltage (the 470x bypasses it).
- **IN**: C22 100 nF 50 V X7R 0603 at the pad end of IN's widened copper, then C21 1 µF 50 V X7R 0805 (C28323).
  **OUT**: C32 1 µF 50 V X7R 0805 at the pad end of OUT's widened copper, and C31, the same part, beside it
  (each ≈ 0.62 µF at 15 V on the DC-bias curve).
- **This block runs only from a 12 V or 15 V input.** Thresholds are worst-case stacks of TI's guaranteed windows,
  1 % resistors and ±0.1 µA pin leakage. **EN/UVLO** R23 75 kΩ / R24 10 kΩ from VBUS: on at 9.87–10.59 V, off below
  8.98–9.66 V, so **never on at 5 V or 9 V** (9.45 V max), on at 12 V (11.4 V min) and 15 V; filtered by **C23**
  100 nF (τ 0.88 ms; "on at 12 V" depends on it: see the 12 V note under Margins). **OVLO** R25 150 kΩ / R26 10 kΩ: cuts at 18.56–19.95 V, back on below 16.88–18.21 V, so above
  a 15 V contract's worst VBUS (16.0 V on a load release at 15.75 V): **it recovers by itself** through dVdt. A 20 V
  source (19.0–21.0 V) may run or be cut. **ILM** R28 1.00 kΩ 1 %: ILIM 2.94 / 3.34 / 3.67 A; the fast trip near
  2 × ILIM is typical behaviour (ISC 201 % typ, no min/max); **TP3** on ILM reads 0.163–0.202 V/A (GIMON
  165–200 µA/A, 0.182 typ). **dVdt** C24 4.7 nF ±10 % X7R: 0.142–0.82 V/ms (0.156–0.74 at nominal C), so 0 → 90 %
  of 15.75 V in 17–100 ms and of 12.6 V in 14–80 ms, **after U4's turn-on delay tD,ON** (SLVSFC9C 6.7: tON =
  tD,ON + tR; tD,ON 1.32 ms at 1.8 nF, 2.35 ms at 3.3 nF and 12 V, 3.69 ms at 3.3 nF and 23 V, **typical only**):
  ≈ 3.3 ms (12 V) / 3.9 ms (15 V) typical at 4.7 nF, ≈ 10 / 11.7 ms scaled to IdVdt's minimum and C24 +10 %. **The
  model has no tD,ON**, so every simulated rise time below omits it. **ITIMER** C25 10 nF ±10 %: breaker blanking
  4.6–16 ms. **C24** is C53987 (0603B472K500NT, 4.7 nF 50 V X7R ±10 %, JLC catalogue): 50 V against TI's ≥ VIN
  + 5 V for the dVdt capacitor, 33 V at the 28 V fault.
- **The fail-safe enable**: Q1 (2N7002) holds EN low while its gate is held up from VBUS (R29/R34 100 kΩ/100 kΩ:
  VBUS/2, ≥ 4.84 V wherever EN could reach its rising threshold; 14 V at a 28 V fault). The fitted part (CJ, C8545)
  guarantees RDS(on) ≤ 7 Ω only at VGS 5 V / 50 mA (and ≤ 5 Ω at 10 V); it has no 4.5 V row, so 4.84 V is not on a
  guaranteed row. **The argument is from need**: Q1 sinks only VBUS/75 kΩ (0.13 mA at 10 V, 0.2 mA at 15 V) and must
  hold EN well under VSD (0.45 V), i.e. RDS(on) up to the kΩ range, which a part with Vth ≤ 2.5 V (guaranteed) driven
  at ≥ 4.84 V meets by a wide margin. Next revision option: R34 150 kΩ (gate 0.6 × VBUS: 5.92 V at 9.87 V, onto the
  5 V row; 16.8 V at 28 V, inside ±20 V). Q2 (**AO3400A**, C20917: RDS(on) ≤ 48 mΩ guaranteed at VGS 2.5 V), driven from **PEN**
  through R30 1 kΩ and held off by R35 100 kΩ at its gate, pulls Q1's gate down. **PEN high = on.** PEN floating,
  low, or its supply lost means off; so does the logic supply dying while VBUS stays.
- **U4's seven 0.2 mm escapes** (locked on the source board: the router only knows the board's 0.2 mm clearance,
  and U4's own pads sit 0.15–0.195 mm apart). **IN and OUT** stay 0.2 mm only until they clear the corner pads
  (0.86 mm), then widen to 0.6 mm and, 0.34 mm on, to 1.2 mm: IN runs up through C22.1 to C21.1 with two VBUS vias
  beside it, (−1.2, −2.6) and (−1.2, −3.8), joined on F.Cu and B.Cu; OUT runs down to y 2.8 and left onto C32.1.
  **GND (pin 8)** runs on to its own via at (2.9, 0.23).
- **Ground vias** at C21, C22, C31, C32, U4.8 and in the fail-safe (R24, C23/R26, Q1.S, Q2.S, R34, R35): 11 in
  all. R28, C24 and C25 return on F.Cu to the C21 and U4.8 vias.
- **The dividers sit by their pins**: R23, R24, C23, R26, R25 in a column at x −3.7, 2–3 mm from pins 1–2, all on
  F.Cu (OVLO no longer crosses under U4). EN reaches Q1's drain on In2.
- **Left to the board**: the 470 µF bulk (C30), the 10 mΩ Kelvin shunt (R31) and its test pads, the printer
  socket: the load's side, sized with the load. **The 1.2 mm VPO run is the board's too**: on the source board one
  locked segment runs from (0.24, 2.8), where the block's OUT copper turns onto C32, east along y 2.8 past C31, C30
  and the shunt. A segment is never split, so it stayed with the board, with C31.1's 1.2 mm stub off it and the two
  VPO vias on it at (1.4, 2.8) and (4.6, 2.8) that join a B.Cu copy of the run. **On the block alone C31.1 is
  joined to nothing.** That run, its stub and its vias lie inside the block's copper extent, by design.
- **OVLO is internal since rev B** (it was a port, for rev A's 9/15 V switch). A board wanting another cut-off
  changes R25 or R26, which leaves the verified state below.
- **The `lp` library** (block.json `local_libs`): U4's symbol and footprint are LCSC's, converted with
  easyeda2kicad. The toolkit ships no third-party library; a board supplies its own copy (`libs=`).

## Margins (sim4, worst case: lumped and routed copper over fixed corners; Monte Carlo over guaranteed windows)

| What | Worst | Limit (guaranteed) | Margin |
|---|---|---|---|
| EN at a 9 V source (9.45 V), PEN high: the output must stay off | 1.112 V nominal (sim); **1.132 V worst stack** (9.45 V / 8.3515 + 0.88 mV pin leakage, 0.1 µA × 8.82 kΩ) | 1.183 V (rising min) | **0.051 V, the tightest** (0.42 V at VBUS) |
| EN while printing 2.5 A peaks, 15 V source at 14.25 V, 2 m cable at 0.85 Ω (VBUS 12.03 V) | 1.470 V (MC, in-spec cables: 1.56 V) | 1.116 V (falling max) | 0.35 V |
| EN while printing, 12 V source at 11.4 V: 2 m in-spec (MC) / 2 m at 0.85 Ω (fixed) | 1.232 / 1.133 V | 1.116 V | 0.116 / **0.017 V**: see below |
| OVLO while printing at 15.75 V (strobe release) | 0.988 V (MC 1.004 V) | 1.183 V (rising min) | 0.18 V (≈ 2.9 V at VBUS) |
| OVLO when PEN cuts U4 at full current (VBUS rings to 16.33 V lumped / 16.31 V copper) | 1.021 / 1.019 V | 1.183 V | 0.16 V |
| U4 current peak under 2.5 A strobes | 2.67 A lumped / 2.50 A copper (MC 2.52 / 2.52 A, 12 V sets) | 2.94 A (ILIM min with R28's 1 %) | 0.27 A; breaker timer never started |
| Inrush into the source board's 470 µF + its printer | 0.588 A (MC 0.624 A) | 0.8 A (own target; 3 A contract) | 0.18 A |
| Output to 90 % after PEN, 15 V (15.75 V) / 12 V (12.6 V) | simulated (no tD,ON) 91.9 / 74.2 ms, MC with C24 ±10 % 96.2 / 76.6 ms; **+ tD,ON** 3.9–11.7 / 3.3–10 ms: **100–108 / 80–87 ms** (hand stack 112 / 90 ms) | F7 waits 130 / 110 ms | ≥ 22 / 23 ms (18 / 20 ms on the hand stack) |
| EN during the plug-in ring, PEN not driven, Q1 Vth up to 2.5 V | 0.539 V copper (MC 0.372 V) | 1.183 V | 0.64 V |
| EN when the 15 V contract arrives before firmware drives PEN | 0.588 V | 1.183 V | 0.59 V |
| Off after the logic supply or PEN is lost while loaded | ≤ 212 µs (MC ≤ 120 µs); on in 0 of 200 after 10 ms | — | — |
| The weakest Q2 (Vth 1.45 V) with PEN at 3.3 V | on: the load sees 14.64 V while printing | — | — |
| Source fault to 28 V | Q1 VGS 14.0 V, Q2 VDS 14.0 V, Q2 VGS 3.29 V, EN 3.32 V (MC 3.35 V), OVLO 1.77 V | ±20, 30, ±12, 6.5, 6.5 V | 6.0, 16, 8.7, 3.15, 4.7 V |
| Output at a 15 → 20…28 V source fault | 15.25 V lumped / 15.21 V copper (MC 15.59 / 15.57 V) | the load's own (source board: 24 V, C30 25 V) | 8.4 V |
| U4 IN at plug-in; IN slew of the ring | 8.55 V lumped / 8.19 V copper (MC 8.74 / 8.30 V); +7.5 V/µs, −5.1 V/µs from 1 µs after contact | 28 V; +100 / −10 V/µs | 19 V; 4.9 V/µs |
| Hard short at the load (10 mΩ): U4's fast trip, the IN ring (the model then latches off; the real part does not: below) | fast trip in 0.6 µs; U4 IN 22.47 V lumped / 21.22 V copper (MC 23.63 / 22.43 V; VBUS MC 23.63 / 22.41 V) | 28 V (U4 IN); 25 V (the board's VBUS parts) | 4.4 V on U4, 1.37 V on 25 V parts (MC lumped) |
| Unplug while printing: IN falling slew | −0.27 V/µs | −10 V/µs | 9.7 V/µs |

**The 12 V fallback on a bad cable.** On a 2 m cable at 0.85 Ω (well outside USB-C's IR-drop budget) EN's minimum
while printing at 11.4 V was 1.133 V with nominal resistors, 17 mV above UVLO's falling maximum; R23/R24 at their 1 %
worst (ratio 8.65 against 8.50) take that to ≈ 1.113 V, through it. The failure is benign: U4 turns off mid-print and
restarts through dVdt when VBUS recovers (a spoiled print, no overstress). In-spec cables keep 0.116 V. A board that
must print reliably at 12 V on poor cables would trade some of the 9 V margin above for it (R23 lower).

**"On at 12 V" rests on C23.** In sim4's 12 V print VBUS dips to 9.15 V (2 m at 0.85 Ω), below EN's falling maximum
at VBUS (9.66 V); EN stays up only because C23 (τ 0.88 ms) averages the printer's strobes, which are ASSUMED (1 kHz,
60 %). A sag longer than about 1 ms drops the output at 12 V. A board reusing the block with another load simulates
its own load at 12 V.

**9 V is a real case**, not a corner: the HUSB238 falls back to a lower PDO when the source lacks the requested one.
USB PD's vSrcValid lets a 9 V source swing ≈ ±0.5 V further in transients (to ≈ 9.95 V), above EN's 9.87 V rising
minimum; C23's 0.88 ms filter probably absorbs such short excursions, but that is not simulated.

**The hard short after the fast trip is not modelled.** The model opens U4 at the fast trip (0.6 µs) and latches it
off. The real part (SLVSFC9C 7.3.5.4, Fig. 7-11) retries after a ~30 µs de-glitch into current limit and stays there
until ITIMER expires (≤ 16 ms) or thermal shutdown, then latches (L variant). Through that phase U4 sinks ILIM
(2.94–3.67 A) with ~15 V across it, so the source sees ≈ 3.7 A plus the board's own load, above a 3 A contract: it
may trip the source's OCP or a PD hard reset, and **the 3V3 hold that s8 shows is not proven for that phase**. The
ring figures above stand (they come from the trip itself). Declined for this cut; the first open item for the next
(below).

**The hard short's falling slew** (−50 V/µs over 100 ns in the Monte Carlo, −61 V/µs at a fixed corner, copper) is
an unclamped, pessimistic bound: the real part's saturation current before tFT (500 ns) is not modelled, so the
model dumps VBUS's capacitors into the short at 110–217 A for 0.6 µs. It is to be measured at bring-up. TI's 10 V/µs IN limit is for the supply; an output short is the case the part is
characterised for. The ring figure is the pessimistic bound; the copper's nH lower it by 1.3 V.

The Monte Carlo drew CdVdt's ±10 % through IdVdt, so the F7 times include it (not X7R's temperature drift), the
resistors at ±1 %, C25 ±10 %, the MLCCs 0.80–1.10, Q1/Q2 Vth over their full windows; it did not draw R28's 1 %
(the ILIM row quotes it by hand).

Copper on the source board (sim4's extraction): C22 → U4 IN 2.40 mΩ / 0.45 nH, C21 → C22 0.49 mΩ / 0.18 nH;
U4 OUT → C32 2.40 mΩ / 0.45 nH, → C31 3.2 mΩ; U4's GND pin to its via 4.16 mΩ / 0.73 nH (rev A: 3.87, 4.26 and
8.2 mΩ through the 0.2 mm necks and the pour). On the source board R23 tees off at C21 (no current in the tee);
R25/R29 tee off nearer the connector, ≈ 15 mΩ upstream of U4's IN, so OVLO reads ≈ 2.5 mV high at 2.5 A, the
conservative side.

## Firmware rules the block needs (from the source board's F7, F8, F9)

- **F7: wait before loading the output.** With 4.7 nF of dVdt the output takes up to 108 ms (simulated 96 ms with
  C24 ±10 %, plus tD,ON up to 11.7 ms, which TI gives typical only and the model omits; 112 ms on the hand stack) to
  reach 90 % at 15 V, 87 ms (90 ms) at 12 V: wait **≥ 130 ms** after PEN goes high at 15 V, ≥ 110 ms at 12 V. A
  load started mid-ramp sagged the rail to 6.6 V in rev A's simulation. Or keep the output on whenever a contract
  exists.
- **Never step the input up with the output on**, and never ask the source for more than the contract the board
  is built for. Rev A's sim3 measured a 9 → 15 V step charging the output bulk at 2.93 A against U4's 2.94 A
  minimum limit (it may time out and latch: safe, but avoid it). Rev B's source board has no such step (fixed
  15 V; its F8 forbids any I²C PDO request), and **a 20 V request reaches OVLO's band** (18.56–19.95 V): it may
  run or be cut. If the contract must change: PEN low, change it, PEN high, wait F7.
- **A latch-off clears with PEN low then high** (Q1 pulls EN below VSD, 0.45 V). An over-voltage cut-off no longer
  needs firmware: **rev A's F9 is retired**, because OVLO's falling minimum (16.88 V) is above any 15 V contract, so
  U4 restarts by itself through dVdt.
- **Enable only at a 12 V or 15 V contract**; at 9 V the block stays off by design (the source board's F8).
- **The block gives firmware no signal of an OVLO trip, a breaker latch-off or a UVLO drop-out** (PG/PGTH unused):
  firmware must infer it from the load (the source board: the printer stops answering), and report it.

## Accepted, and carried by the block

- **The fail-safe enable**: driving EN from a GPIO alone would drop the hardware UVLO interlock (no output below
  ~10 V, whatever firmware does). Rev A's first design pulled Q1's gate up to the logic rail (a dead rail enabled
  the output); the VBUS pull-up has passed every audit and simulation since.
- **PG and PGTH unused and open**; no test pad (PG means nothing with PGTH floating). Declined on the source board
  for want of a GPIO (finding 4 below): that is the board's reason, not the block's (next revision: an optional port).
- **No OVLO filter capacitor** (the rev A review's optional ≤ 1 nF): the margin is now 0.18 V at the pin (2.9 V at
  VBUS), and a filter would only slow the cut.
- **No Schottky from OUT to GND** (TI suggests one for inductive loads): the source board's load has 470 µF of bulk
  at it. A load with long leads or a motor on its own is the board's to judge.
- **The 0.2 mm necks out of IN and OUT** (0.86 mm long, between the corner pads): about 2 mΩ each. Next revision:
  0.27–0.3 mm necks under a U4-local 0.15 mm clearance rule.
- **R28 (ILM) and C25 (ITIMER) return through C21's GND via**, not to U4's GND pin by the shortest path as TI asks
  (C24 does go to pin 8's via). The error is millivolts against ILM's ~0.6 V at the limit. Next revision: return
  them to pin 8.
- **C31.1 is joined only by the board's VPO run** (the cut takes a track whole or not at all, and that run is the
  board's): kept, and documented above.
- **TP3 on ILM**: TI keeps ILM's parasitic capacitance under 50 pF. A pad is a few pF; a scope probe (10–15 pF) is
  fine, a long lead may not be.
- **EN/UVLO and OVLO tops below TI's ≥ 350 kΩ** (R23 75 kΩ, R25 150 kΩ). SLVSFC9C 6.3 footnote (2) asks for it on
  a pull-up straight to IN, for supplies above 5 V or reverse polarity, to limit the pin current. Here they are
  dividers that hold EN ≤ 3.35 V and OVLO ≤ 1.78 V even at a 28 V fault (simulated), under EN's 5 V recommended
  maximum and both pins' 6.5 V absolute maximum, so no pin current needs limiting. Reverse polarity cannot occur
  behind USB-C; a board behind a barrel jack must revisit it.
- **The model's tOVLO is ASSUMED 5 µs**; the datasheet's timing table gives 1.2 µs typ. The model cuts later than the
  part, which overstates the output's overshoot at a fault: the pessimistic side. Kept as sim3 and sim4 ran it.
- **The model's 2N7002** (`N2N7002`, kp 0.067, sized for an ASSUMED 7.5 Ω at 4.5 V) gives 6.0 Ω at VGS 5 V and Vth
  2.5 V, slightly stronger than CJ's 7 Ω row. Q1's job needs kΩ, so no result depends on it; kept as sim4 ran it.
- **JLC**: C2864845 placed by `jlc_verify`, pad by pad; the 2N7002 (C8545) and the AO3400A (C20917) +180 in the
  toolkit's table. The source board's rev B build passed `jlc_verify` for every part.

## Measure at bring-up

- **U4 IN at plug-in on a scope**: falling slew against the 10 V/µs absolute limit. The simulated ring falls at
  ≤ 5.1 V/µs from 1 µs after contact; only the bench's idealised contact edge exceeds it, and a real plug's bounce
  is not modelled.
- **PEN's GPIO through reset**: the simulation assumes it high-impedance (R35 holds Q2 off); confirm no internal
  pull-up on the chosen pin.
- **TP3** against a known load current, if the current limit's reading is to be used.
- **U4 IN falling slew during an output short** (a shorting load at OUT, scope on IN): the simulated figure is an
  unclamped bound above TI's 10 V/µs.

## The board's job

- **Size the power path for TI's 2 × full load** (SLVSFC9C 8.4.1: 6 A for 3 A). 1.2 mm of 1 oz carries ≈ 2.7 A
  at 10 °C rise, 3.7 A at 20 °C: use ≥ 1.2 mm on both outer layers, stitched (as the source board's VPO run is), or
  ≥ 2.5 mm on one. **The block's own IN and OUT copper is 1.2 mm on F.Cu only** (with the 0.6 / 0.2 mm necks out of
  the pads, and the B.Cu link only between IN's two vias): it accepts 1 × full load, not TI's 2 ×.
- **Feed VBUS into one of the block's two VBUS vias**, (−1.2, −2.6) or (−1.2, −3.8); on the source board a locked B.Cu run from the USB-C connector lands on
  (−1.2, −2.6). The block's IN copper already joins U4 IN, C22, C21 and R23.1.
- **Join R25.1/R29.1** (joined to each other on F.Cu in the block) **to VBUS** by a tee that carries no load
  current: the divider tops must never sit in the power path.
- **Lay VPO from (0.24, 2.8) east at ≥ 1.2 mm** past C31.1 (a stub into it) to the bulk and the load, with vias to
  a back-side copy beside U4 (heat out of OUT, half the resistance). Keep it where it is: it lies inside the block's
  copper extent, and C31 is joined to nothing without it.
- **PEN** from a GPIO that is not a strapping pin and idles high-impedance or low through reset.
- **Bulk at the load**, sized for it (the source board: 470 µF 25 V at the printer socket), and a Kelvin shunt if
  the load current is to be measured.
- **A hard output short loads the source with ILIM** (up to 3.67 A) plus the board's own load for up to ~16 ms
  before the latch (above): a board on a 3 A contract must accept a possible source OCP or PD hard reset, and check
  its logic supply's hold-up through it.
- **Every part on VBUS rated ≥ 25 V**; U4's IN is 28 V absolute. The hard-short ring reached 22.4–23.6 V on the
  source board (Monte Carlo, copper / lumped): a board with less VBUS capacitance or a longer cable must simulate
  its own or fit a TVS (TI's transient-protection section).
- **The block's design rules** (block.json): `dru_rules` (U4's own pads 0.14 mm apart; JLC's minimum is 0.1 mm;
  everything else at the board's 0.2 mm) through `Block.dru_rules(refs)`, `min_track_width` 0.18 mm, and four
  copper layers.
- **The firmware rules** above.
- **Keep parts out of the copper extent** (the board's own VPO run excepted).

## Rev A review findings and how rev B answers them

One fresh reviewer read the rev A cut alone, with TI's datasheet (SLVSFC9C, May 2026): NOT CLEAN, 0 blockers,
8 should-fix, 6 suggestions. The source board took the layout findings into its rev B; this cut is that layout.
The rev B block has since had its own independent reviews (rounds 1 and 2, below).

| # | Rev A finding | Rev B |
|---|---|---|
| 1 | IN/OUT 0.6 then 0.2 mm for the last 2 mm, no vias, against TI's "twice full load" and the heat path | **Resolved**: 0.2 mm for 0.86 mm only (between the corner pads), 0.6 mm, then 1.2 mm; two VBUS vias on IN inside the block. **OUT's two vias are on the board's VPO run**, not in the block (the board's job) |
| 2 | C22 4.9 mm from IN, behind the neck; U4's GND pin without a via | **Resolved**: C22 at the pad end of IN's 1.2 mm copper with its own GND via, C21 next; pin 8's escape runs to a via (4.16 mΩ, was 8.2) |
| 3 | Fail-safe grounds only through the pour; R35 6.5 mm from Q2 | **Resolved**: GND vias at R24, C23/R26, Q1.S, Q2.S, R34, R35; R35 beside Q2's gate (≈ 2 mm of track) |
| 4 | OVLO's band held the 9 V contract; no OVLO-trip signal; falling window quoted narrow | **Resolved in part**: fixed 15 V, OVLO at 18.56–19.95 V recovers by itself (rev A's F9 retired), windows quoted worst-case. **Still open**: PG unused, so firmware gets no trip signal (declined on the source board: no free GPIO) |
| 5 | F7 and timing margins omitted CdVdt and RILM tolerance | **Resolved**: sim4's Monte Carlo draws CdVdt ±10 %; ILIM quoted with R28's 1 %. The rev B review added U4's tD,ON (typical only, not in the model): with it 100–108 / 80–87 ms against F7, now ≥ 130 / 110 ms |
| 6 | Dividers 6–8 mm from their pins; OVLO under the IC on In2, unfiltered, 76 mV margin | **Resolved**: both dividers 2–3 mm from pins 1–2 on F.Cu; OVLO margin 0.18 V at the pin; filter declined (Accepted) |
| 7 | Board's job missed two VBUS joins and the turn-off ring on IN | **Resolved**: joins listed above; the ring is simulated (PEN cut 16.33 V, hard short ≤ 23.6 V) |
| 8 | 2N7002 drive below its 4.5 V RDS(on) guarantee | **Q2 resolved**: an AO3400A, guaranteed at 2.5 V, driven at 3.27 V. **Q1 argued from need**: VGS ≥ 4.84 V wherever EN can switch on, just below the fitted part's 5 V row (it has no 4.5 V row); it needs kΩ, not ohms. R34 150 kΩ is the next-revision option |
| 9 | Fast trip at 2 × ILIM is typical only | **Still true** (stated above). The rev B review found the model latches off at the fast trip where the part retries into current limit for up to ITIMER: open, first item for the next cut |
| 10 | Model's tOVLO ASSUMED 5 µs, datasheet 1.2 µs typ | **Still open, model unchanged** (pessimistic side; Accepted). Separately, sim4 found and fixed a latch fault in the model (below) |
| 11 | TP3 and EN figures should be guaranteed ranges | **Resolved** (above) |
| 12 | ≥ 350 kΩ pull-ups on EN/OVLO for reverse polarity | **Accepted**: dividers hold both pins within ratings at 28 V; reverse polarity cannot occur behind USB-C (Accepted) |
| 13 | 21 × 21 mm of copper for a 2 × 2 mm IC | **Resolved**: 20.0 × 14.0 mm, the fail-safe in ≈ 10 × 11 mm left of U4 |
| 14 | One OUT capacitor, half its value at 15 V | **Resolved**: C32 at OUT's pad end plus C31 (≈ 1.2 µF together at 15 V) |

**The eFuse model** (`../models.inc`, ported from the source board's rev B harness): its latch charged at 1 V/ms,
so the "500 ns" fast trip took ~0.5 ms to open the switch, and a short fast trip could freeze it near 0.99, leaving
U4 ~1 % on into a short. It now settles in ~100 ns and holds itself once past 0.5; EN below VSD still clears it.
Only fault paths set the latch, so no non-fault figure moves. The AO3400A model (`NAO3400`: level 1, the weakest
guaranteed device) is added there too.

## Open for the next cut (from the rev B reviews)

1. **Model the fast trip's retry into current limit** (SLVSFC9C 7.3.5.4, Fig. 7-11: ~30 µs de-glitch, then ILIM
   until ITIMER or thermal shutdown, then the latch) and re-run the source board's s8 hard short: source current,
   VBUS and the 3V3 hold through that phase.
2. **R34 150 kΩ** puts Q1's gate on the 2N7002's guaranteed 5 V row wherever EN can switch on.
3. **R28 and C25 returned to U4's GND pin** by the shortest path.
4. **0.27–0.3 mm necks** out of IN and OUT under a U4-local 0.15 mm clearance rule.
5. **The power path at TI's 2 × full load** inside the block (both outer layers, stitched).
6. **PG/PGTH as an optional port**, with a PGTH divider and a PG pull-up footprint, so a board with a free GPIO can
   see an OVLO trip, a latch-off or a UVLO drop-out.

## Independent review of the rev B block

- **Round 1**: NOT CLEAN, 0 blockers, 6 should-fix, 5 suggestions. Answered above: tD,ON added to F7 (now ≥ 130 /
  110 ms); the model's latch-off at the fast trip versus the part's retry into current limit (declined for this
  cut, open item 1); Q1's drive argued from need (the fitted 2N7002 has no 4.5 V row); the 9 V row's worst stack;
  2 × full-load width as the board's job; "on at 12 V" resting on C23; figures reconciled with sim4's outputs.
- **Round 2**: NOT CLEAN, 0 blockers, 3 should-fix, 3 suggestions, wording and numbers only. Answered: the 9 V
  stack's leakage term taken at the pin (1.132 V, margin 0.051 V); this section; the reason for accepting the
  < 350 kΩ divider tops; the short's falling slew called an unclamped bound, with a bring-up measurement; C24's
  50 V rating; PG/PGTH as a next-revision option.
