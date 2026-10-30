# esp32-c3-wroom-02: findings and what the board must do

Anchor U1 (the module's origin). **Copper extent: x −13.3 … 12.2 mm, y −6.0 … 10.1 mm** from U1.

## Accepted, and carried by the block

- **IO2 and IO8 must read high at reset**: R9 and R7, 10k to 3V3. IO9 is BOOT (SW2 to GND, with the
  chip's own 45k pull-up).
- **EN**: R6 10k / C6 1u, so EN rises after 3V3; SW1 pulls it to GND (RESET).
- **C5 10u at the module's 3V3 pin**, because the regulator's 22u may be far away (46 mm of track on
  the source board).
- **Wi-Fi bursts** (345 mA TX peak, 84 mA RX shoulder, datasheet Table 6-4): on the source board, with
  its LDL1117 stage and copper (the `ldo-ldl1117` block's layout has since changed), 3V3 bottomed at **3.149 V** worst case (4.75 V charger, 0.3 m
  cable, LDO at −3 % and maximum dropout, low capacitors; limit 3.0 V, +0.149 V).

## The board's job

- **IO5 (MTDI) floats through reset.** Anything it drives needs its own pull (the source board's
  R16 100k holds a load switch's EN low).
- **Antenna**: the module's top 6.35 mm is the antenna; it overhangs the board's top edge on every
  board so far (on the source board U1's origin is 6.8 mm below the edge). No copper, pour or parts under it — the block lays no
  keepout for it.
- **Silk**: the RESET and BOOT legends are board silk, not the block's. So are any test pads for
  TXD/RXD.
- IO3 and IO7 are left free (optional ports): map them to use them.
