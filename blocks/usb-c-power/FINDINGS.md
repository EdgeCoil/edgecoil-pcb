# usb-c-power: findings and what the board must do

Anchor J1. **Copper extent: x −5.3 … 4.3 mm, y −14.4 … −3.1 mm** from J1 (above the receptacle).

## Accepted, and carried by the block

- **CC1, CC2: 5.1k to GND**: a sink, 5 V only (no PD).
- **SRV05-4 on D+/D−, its rail on 3V3.** Its leakage is specified to 5 µA at 5 V: fine for USB, not
  for a line that must stay quiet unpowered (use a TPD4E1U06 there, as the source board does on HDMI).
- **JLC placement**: HRO TYPE-C-31-M-12 (C165948) at CPL offset (0, 1.571); SRV05-4 (C85364) +180.
  Both checked pad by pad by `jlc_verify`.

## Recorded by simulation: VBUS rings at plug-in

**VBUS rings to 9.135 V** lumped and **8.617 V** on copper (worst of 144 corners: a stiff or 0.3 m
cable, 5.5 V charger, C1 at its peak DC bias). **Every part on raw VBUS needs an absolute maximum of
10 V or more**, or a damper (an earlier simulation: 22 µF + 0.33 Ω brought it to 6.6 V on copper).
Keep charger input within 4.75–5.25 V for parts downstream that care (the source board's load switch
did).

## The board's job

- **The toolkit, not the block, lays the D+/D− crossover under the receptacle and the VBUS pad joins**
  (locked, on any `Connector_USB:` footprint), and keeps tracks off the shell.
- **Give the ESD array its ground via**: the block lists it (`"esd_ground": ["U2"]`), so add
  `block.board_refs("esd_ground", refs)` to `Config.esd_refs`. Without it the via under U2's ground pin,
  which sits between two signal pins where the pour can't reach, is not laid.
- **Bulk capacitance on VBUS is not in this block**: on the source board it is the `ldo-ldl1117`
  block's C1.
