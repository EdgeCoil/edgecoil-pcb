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
- **Dropout 0.50 V maximum at 1 A**: 3V3 holds down to VBUS ≈ 3.8 V at full load, lower at the
  module's currents.
- **Wi-Fi bursts**: 3V3 ≥ 3.149 V worst case on the source board, with its own layout of these parts
  (see the `esp32-c3-wroom-02` FINDINGS). This block's layout was not simulated on copper; it
  shortens C1's input loop and moves C4 to the tab, and the lumped model is unchanged.
- **Iq 250 µA typical, 500 µA maximum**: not for a battery board (the tune-button uses an RT9080).

## Open, and the board's job

- **Output capacitance is above ST's characterised 22 µF** once the module's own 10u and C5 are
  added. The board simulation's check `s3` compared the source board's output network, with its routed copper and
  DC-biased ESR, against ST's stability region (DS12022 Fig. 20/21: 1–22 µF nominal, ESR at 100 kHz
  between about 0.012–0.02 Ω and 10 Ω). The behavioural LDO model is fitted to transients and cannot
  predict phase margin, so this is a comparison, not a proof: **scope 3V3 at bring-up**.
- **JLC placement margin**: `jlc_verify` puts JLC's footprint 0.32 mm off KiCad's pin pads (its limit is
  0.35): KiCad's pin pads sit further out. The lead tips (7.0 mm lead span) land inside both. Watch U5's
  paste and placement on the first JLC order.
- **Heat: the tab has only its own pad** (3.8 × 2.0 mm, inside a GND pour), no spreading copper. U5
  dissipates (VIN − 3.3 V) × I: about 0.2 W average at 5 V in with the ESP32-C3 block, which this
  carries. **Nobody here has checked the SOT-223's θJA against ST's datasheet** (it could not be fetched
  on 2026-10-30), so a board with VIN above 5.5 V, or more than ~0.3 A average, must add 3V3 copper on
  the tab side and check the datasheet first.
- **The symbol's own Description and Datasheet fields are the LD1117's** (KiCad has no LDL1117 symbol;
  the pinout is the same). The part placed and ordered is set by its value, MPN and LCSC number.
- **Datasheet**: ST DS12022 could not be downloaded on 2026-10-30 (ST timed out; Mouser and LCSC served
  HTML). The pinout above is from a summary of DS12022 Rev 7, the KiCad symbol, and the figures recorded
  when the simulation model was fitted (`models.inc`).
