# ldo-ldl1117: findings and what the board must do

Anchor U5. **Copper extent: x −4.65 … 0.0 mm, y −3.15 … 5.45 mm** from U5 (three tracks).

**U5 is KiCad's stock part, and the layout is this block's own** (2026-10-30), not a cut from a reviewed
board: so the toolkit ships no third-party library, and so the input capacitor sits at the input.
- **U5**: symbol `Regulator_Linear:LD1117S33TR_SOT223` (the LDL1117's SOT-223 pinout: 1 GND, 2 VOUT,
  3 VIN, tab = VOUT), footprint `Package_TO_SOT_SMD:SOT-223-3_TabPin2` at 270°: pins in a row at
  y = −3.15, tab at +3.15. KiCad's footprint is EasyEDA's turned 180° (not mirrored), with wider pin
  pads (2.0 × 1.5 mm against 2.47 × 0.98) 0.32 mm further out.
- **C1 (input) beside VIN**, rotated 90°: pad 1 level with pin 3 on a 2.35 mm track, its GND pad facing
  into the front pour, which runs under the pin row to pin 1. **C4 (output) at the tab** on a 2.3 mm
  track. On the source board C1 sat 10.5 mm of track away, past the tab — an independent review of the
  first stock-part version flagged it (SHOULD-FIX), and this layout is the fix.
- **Checked**: `selftest` (connected at all four rotations); `tests/drc_block.py` — KiCad DRC of the
  block alone, clean, no unconnected items, the front GND pour one piece reaching U5.1, C1.2 and C4.2;
  it fails, as it should, on a VBUS track 0.05 mm from the tab and on C1's courtyard pushed into U5's;
  `jlc_verify` with **JLC CPL +180** for C435835 on this footprint (`jlc.ROTATE_FP`; the source board's
  EasyEDA footprint needs 0 and keeps it), and an end-to-end CPL export placing U5 at 90°.

## Accepted, and carried by the block

- **VIN absolute maximum 20 V**: 10.9 V of margin over the 9.135 V plug-in ring (11.3 V on copper,
  8.719 V at VIN).
- **Dropout 350 mV typical, 600 mV maximum at 1.2 A** (DS12022 Table 4): 3V3 holds down to VBUS ≈ 3.9 V
  at full load, lower at the module's currents.
- **Wi-Fi bursts**: 3V3 ≥ 3.149 V worst case on the source board, with its own layout of these parts
  (see the `esp32-c3-wroom-02` FINDINGS). This block's layout was not simulated on copper; it
  shortens C1's input loop and moves C4 to the tab, and the lumped model is unchanged.
- **Iq 250 µA typical, 500 µA maximum** (Table 4): not for a battery board (the tune-button uses an RT9080).

## Open, and the board's job

- **The output network lies outside ST's characterised stability region, on both axes — the block's
  main open risk.** DS12022 Fig. 20/21 plot the stable region as C_OUT 1–22 µF nominal (3.3–22 µF at
  1.2 V out) with ESR at 100 kHz from a floor of about 0.02 Ω at 1 µF falling to about 0.012 Ω at 22 µF,
  up to 10 Ω (about 5 Ω at 1.2 V out). Here:
  - **ESR below the floor**: C4 (22 µF X5R 0805, CL21A226MAQ) is about 4.7 mΩ at 100 kHz, DC-biased
    (Samsung's data, as in `model.inc`), against ~0.012 Ω. Its 2.3 mm track adds only milliohms.
  - **Capacitance above 22 µF** once a board adds the module's own 10 µF and the C3 block's C5 10 µF:
    about 42 µF nominal on the rail.
  The plot shows where ST characterised the part as stable, not where it is unstable, and the
  behavioural model can't predict phase margin. **Scope 3V3 at bring-up for ringing or oscillation, on
  a load step (Wi-Fi TX).** If it rings, the datasheet's own suggestion is 4.7 µF at the output (with
  1 µF in); dropping C4 to 4.7–10 µF raises its ESR toward the floor and keeps the sum lower. The same
  applies to the source board.
- **JLC placement margin**: `jlc_verify` puts JLC's footprint 0.32 mm off KiCad's pin pads (its limit is
  0.35): KiCad's pin pads sit further out. The lead tips (7.0 mm lead span) land inside both. Watch U5's
  paste and placement on the first JLC order.
- **Heat: the tab has only its own pad** (3.8 × 2.0 mm, inside a GND pour), no spreading copper.
  DS12022 Table 3: θJA 120 °C/W, θJC 15 °C/W (no board conditions stated); §6.1:
  P_DMAX = (125 °C − T_AMB) / θJA, so **0.71 W at 40 °C ambient, 0.54 W at 60 °C**. U5 dissipates
  (VIN − 3.3 V) × I: at 5 V in that allows **0.42 A average at 40 °C (0.32 A at 60 °C)**. The C3
  block's TX peak (345 mA) held continuously would be 0.59 W: inside the limit at 40 °C, not at 60 °C;
  its real average is far lower (bursts), but nobody has measured it. At 12 V in the limit is about 80 mA. A board above those
  must add 3V3 copper on the tab side (θJC 15 °C/W: the tab is the heat path).
- **The symbol's own Description and Datasheet fields are the LD1117's** (KiCad has no LDL1117 symbol;
  the pinout is the same). The part placed and ordered is set by its value, MPN and LCSC number.
- **Datasheet**: checked against ST DS12022 Rev 6 (April 2020), supplied 2026-10-30 after downloads
  from ST, Mouser and LCSC failed: pinout (Table 1: 1 GND, 2 VOUT, 3 VIN, tab = VOUT), absolute maximum
  VIN 20 V (Table 2), thermal data (Table 3), dropout and Iq (Table 4), capacitors (§6.2: input at least
  1 µF, "as close as possible to the input pin … returned to a clean analog ground"; both capacitors as
  close as possible to their pins), stability plan (Fig. 20/21). The datasheet itself is ST's and is not
  in this repo.
