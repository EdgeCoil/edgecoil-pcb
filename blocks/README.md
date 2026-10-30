# Circuit blocks

Each block is a piece of a board that has already passed review: its parts, placed relative to
an anchor part, and the copper that joins them, frozen. A board places blocks and the router only
joins block to block, so a new board's review covers the joins and whatever is new.

| Block | Anchor | Parts | Copper | Ports | Internal nets |
|---|---|---|---|---|---|
| [`esp32-c3-wroom-02`](esp32-c3-wroom-02/) | U1 | U1 module, C5, EN RC (R6, C6), IO8/IO2 pull-ups (R7, R9), RESET/BOOT (SW1, SW2) | 47 items, 3 vias | 3V3, GND, IO0, IO1, IO4, IO5, IO6, IO10, RXD, TXD, USB_DN, USB_DP (IO3, IO7 optional) | EN, IO2, IO8, IO9 |
| [`usb-c-power`](usb-c-power/) | J1 | J1 HRO TYPE-C-31-M-12, CC pull-downs (R1, R2), SRV05-4 ESD (U2) | 17 items, 2 vias | 3V3, GND, USB_DN, USB_DP, VBUS | CC1, CC2 |
| [`ldo-ldl1117`](ldo-ldl1117/) | U5 | U5 LDL1117S33R, C1 10u in, C4 22u out | 8 items | 3V3, GND, VBUS | — |

Each directory holds:

- `block.json`: parts in the block's frame (the anchor at 0, 0), ports, internal nets, copper (nm).
- `model.inc`: a SPICE subcircuit on the block's ports, from the device models in
  [`models.inc`](models.inc).
- `FINDINGS.md`: what audits and simulation found about it and what was accepted, and what a board
  using it must still do itself.

## Using one

```python
from edgecoil_pcb import blocks
core = blocks.load("esp32-c3-wroom-02")
nets = {"3V3": "3V3", "GND": "GND", "IO4": "CEC_IO", ...}   # every port; optional ones may be left out
parts += core.parts((14.0, 6.8), rot=0, refs={"U1": "U1", ...}, nets=nets)
CFG.block_copper += core.copper((14.0, 6.8), rot=0, nets=nets)
```

`refs` gives board references (default: the block's own, prefixed by `prefix=`); internal nets are
prefixed the same way, so two instances don't merge. The copper is laid locked, and `route.py
--freeze` leaves locked copper out of `routing.json`.

**Keep parts out of a block's copper extent** (given in its FINDINGS): the frozen tracks run there.
**Order matters for silk**: the toolkit's silk clean-up and label placement break ties in the
order parts are listed, so keep a block's parts where they were when proving a board identical.

## How these were cut, and checked

`edgecoil_pcb.blocks.cut` takes the parts by reference from a reviewed board and splits its frozen
routing: every item on an internal net, and on each port net the copper joining the block's own
pads (cut where it reaches another part's pad, dead ends pruned until none is left). The rest stays
with the board. Then three checks, all repeatable:

1. **The source board rebuilt from these blocks plus the remaining 396 routing items is
   canonically identical to the committed board** (1680 lines, 5 zone fills; schematic, BOM, CPL and
   pos byte-identical).
2. **`python3 -m edgecoil_pcb.blocks selftest <dir>`** places the block alone at 0, 90, 180 and 270
   degrees and checks every internal net is one connected piece and every copper item reaches a pad.
   It fails, as it should, on copper turned the wrong way, a track moved 1 mm and a track deleted.
3. **`python3 tests/check_models.py`** runs each `model.inc` against the same parts written flat, as
   in the board simulation the device models were validated in: they agree to 1e-12. It fails, as it
   should, on R6 10k → 11k and C4 22u → 10u. This checks wiring and parameters; the physics was
   validated in that simulation (behavioural models fitted to guaranteed datasheet figures, 144
   plug-in corners lumped and on copper, 200 × 8 Monte Carlo).
