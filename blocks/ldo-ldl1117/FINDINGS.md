# ldo-ldl1117: findings and what the board must do

Anchor U5. **Copper extent: x −2.3 … 0.0 mm, y −7.0 … 6.7 mm** from U5.

## Accepted, and carried by the block

- **VIN absolute maximum 20 V**: 10.9 V of margin over the 9.135 V plug-in ring (11.3 V on copper,
  8.719 V at VIN).
- **Dropout 0.50 V maximum at 1 A**: 3V3 holds down to VBUS ≈ 3.8 V at full load, lower at the
  module's currents.
- **Wi-Fi bursts**: 3V3 ≥ 3.149 V worst case with the `esp32-c3-wroom-02` block (see its FINDINGS).
- **Iq 250 µA typical, 500 µA maximum**: not for a battery board (the tune-button uses an RT9080).

## Open, and the board's job

- **Output capacitance is above ST's characterised 22 µF** once the module's own 10u and C5 are
  added. The board simulation's check `s3` compared the output network, with its routed copper and
  DC-biased ESR, against ST's stability region (DS12022 Fig. 20/21: 1–22 µF nominal, ESR at 100 kHz
  between about 0.012–0.02 Ω and 10 Ω). The behavioural LDO model is fitted to transients and cannot
  predict phase margin, so this is a comparison, not a proof: **scope 3V3 at bring-up**.
- **U5's symbol, footprint and 3D model are in the toolkit's library `ec`** (`edgecoil_pcb/lib/`,
  from the JLCEDA/EasyEDA library, credited in its README): set `Config(toolkit_libs=("ec",))`. A board
  that has its own copy of the same part can map it: `parts(..., libs={"ec": "<its nickname>"})`.
