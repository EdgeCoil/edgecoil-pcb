# Circuit blocks

Each block is a piece of a board that has already passed review: its parts, placed relative to
an anchor part, and the copper that joins them, frozen. A board places blocks and the router only
joins block to block, so a new board's review covers the joins and whatever is new.

| Block | Anchor | Parts | Copper | Ports | Internal nets |
|---|---|---|---|---|---|
| [`esp32-c3-wroom-02`](esp32-c3-wroom-02/) | U1 | U1 module, C5, EN RC (R6, C6), IO8/IO2 pull-ups (R7, R9), RESET/BOOT (SW1, SW2) | 47 items, 3 vias | 3V3, GND, IO0, IO1, IO4, IO5, IO6, IO10, RXD, TXD, USB_DN, USB_DP (IO3, IO7 optional) | EN, IO2, IO8, IO9 |
| [`usb-c-power`](usb-c-power/) | J1 | J1 HRO TYPE-C-31-M-12, CC pull-downs (R1, R2), SRV05-4 ESD (U2) | 17 items, 2 vias | 3V3, GND, USB_DN, USB_DP, VBUS | CC1, CC2 |
| [`ldo-ldl1117`](ldo-ldl1117/) | U5 | U5 LDL1117S33R (KiCad stock SOT-223), C1 10u at VIN, C4 22u at the tab returned through R25 (0 Ω link; swap to add ESR) | 4 items | 3V3, GND, VBUS | C4_ESR |
| [`usb-c-pd-sink`](usb-c-pd-sink/) | U3 | U3 HUSB238_002DD PD sink, C20 2.2u 50 V at VIN, ISET 20.0k (R20: the 2.75/3 A code), VSET 14.0k as R21 13k + R22 1k (fixed 15 V) | 19 items, 3 vias | CC1, CC2, GND, SCL, SDA, VBUS | ISET, VSET, VSET_M |
| [`efuse-tps25947`](efuse-tps25947/) | U4 | U4 TPS259474L eFuse, IN C21 1u + C22 100n, OUT C31 + C32 1u, EN/UVLO 75k/10k (R23, R24: on at 12 and 15 V only) + C23 100n, OVLO 150k/10k (R25, R26: 18.6-20 V), ILM 1k (R28) + TP3, dVdt 4.7n (C24), ITIMER 10n (C25), fail-safe enable Q1 2N7002 + Q2 AO3400A with R29, R34, R30, R35 | 88 items, 15 vias | GND, PEN, VBUS, VPO | DVDT, EFUSE_EN, ILM, ITIMER, OVLO, Q1_G, Q2_G |
| [`buck-ap63203`](buck-ap63203/) | U5 | U5 AP63203WU 3.3 V buck, C41 100n + C40 4.7u 50 V X7R 1206 at VIN, L1 4.7u CKCSA4020, C42 100n bootstrap by pins 5/6, C43/C44 22u at L1 | 25 items, 5 vias | 3V3, GND, VBUS | BST, SW |
| [`rtc-pcf85063a`](rtc-pcf85063a/) | U9 | U9 PCF85063A, Y1 32.768 kHz 7 pF, C50 100n, backup R52 100 Ω + D2 BAV170 (one element) into C51 (0.47 F 5.5 V coin EDLC footprint: optional, hand-fitted, hold-up a target), TP6 on VRTC | 18 items, 5 vias | 3V3, GND, SCL, SDA | 3V3_RTC, OSCI, OSCO, VRTC |

The last four were cut from the date-label-printer rev B (four layers; only efuse-tps25947's copper
uses In2.Cu, the others need just a ground plane under them), and
their parts not in KiCad's libraries (the HUSB238, TPS259474L, PCF85063A and its crystal, the
inductor) come from that board's own LCSC library, nickname `lp` (block.json `local_libs`); each block
carries a copy of just its own `lp` parts in its `lib/` (see below). Every simulated figure
their FINDINGS cite is in that board's committed `sim/results/sim4/`, traced to file and line in
`block-figures-<block>.txt` there. CI runs selftest, drc_block and check_models on every block,
these four with their bundled `lib/`.

**A block's own library parts** go in its `lib/` with
`python3 -m edgecoil_pcb.blocks bundle <dir> lp=<board library dir>`: only the symbols and
footprints its parts name, byte for byte, plus `SHA256SUMS` (CI checks it) and a README saying where
they came from. `bundle --check` compares the copy with a board library; re-bundle after any
change to the board's library, and after each re-cut.

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
--freeze` leaves locked copper out of `routing.json`. Also:

```python
CFG.esd_refs += usb.board_refs("esd_ground", refs)   # parts that need esd_ground's via
CFG.solid_pads += rtc.solid_pads(refs)               # pads joined solid to the pour (block.json "solid_pads")
CFG.dru_rules += efuse.dru_rules(refs)               # its own design rules, references renamed
parts += efuse.parts(at, nets=nets, libs={"lp": "mylib"})   # its "lp" parts from the board's own library
```

A block may also carry `"copper_layers": 4` (it has inner-layer copper: the board needs four) and
`"min_track_width"` (its narrowest track: the board's own minimum must allow it). Copper items marked
`"escape"` run from a pad out to where the board joins them (a fine-pitch part's pins), so on the block
alone they end on nothing.

**Keep parts out of a block's copper extent** (given in its FINDINGS): the frozen tracks run there.
**Part order doesn't matter** with the default `order_free_silk=True`: the board came out identical
from the parts list shuffled three ways and reversed (it differed in 14 silk and label lines without
it). Boards built before it (`order_free_silk=False`) must keep their parts in order.

## How these were cut, and checked

`edgecoil_pcb.blocks.cut` takes the parts by reference from a reviewed board and splits its frozen
routing, and the generator's locked copper with it (`power.items()`: power runs, escapes, sense
tracks, ground vias): every item on an internal net, and on each port net the copper joining the
block's own pads. Each net's copper is a graph whose nodes are track ends, the points where a track
ends on another's centreline (a power run teeing into a bus) and vias (one node on every layer); it
is cut where it reaches another part's pad and dead ends are pruned until none is left. On a net with
a pour, a via also reaches the plane, so a pad's own ground via stays with the block, but a track
from one via to another does not; a locked ground via that no track reaches goes with the part whose
pad is nearest. A locked escape from a block pad stays with the block. A segment is never split (the
board must stay canonically the same), so a track the block needs only part of stays with the board,
and the cut names it. The rest of the routing and of the locked copper stays with the board.

    python3 -m edgecoil_pcb.blocks cut <gen.py> <variant> <name> <anchor> <ref,ref,...> \
        [--routing in.json] [--locked in.json] [--rest out.json] [--rest-locked out.json] \
        [--solid REF:PAD] [--esd REF] [--set key=json]

writes `<name>/block.json` and the remainders; cut the next block from those. **`esp32-c3-wroom-02`
and `usb-c-power` are such cuts; `ldo-ldl1117` is not**: it was cut, then moved to KiCad's stock parts
and laid out again with its input capacitor at the input, after an independent review (see its
FINDINGS). The four date-label-printer blocks are cuts, with the locked copper. The checks, all
repeatable:

1. **The source board rebuilt from the two cut blocks plus its remaining routing is canonically
   identical to the committed board** (1680 lines, 5 zone fills; schematic, BOM, CPL and pos
   byte-identical); before the LDO's rework, so was the board from all three. **The
   date-label-printer rebuilt from its four blocks, its remaining routing and its remaining locked
   copper is too** (3255 lines, 10 zone fills; schematic, BOM, CPL and pos byte-identical, with the
   parts kept in the committed order: the schematic's library-symbol table follows first use).
2. **`python3 -m edgecoil_pcb.blocks selftest <dir> [lp=<library dir>]`** (the block's `lib/` unless one is named) places the block alone at
   0, 90, 180 and 270 degrees and checks every internal net is one connected piece and every copper
   item reaches a pad, on every copper layer the block uses. It fails, as it should, on copper turned
   the wrong way, a track moved 1 mm and a track deleted.
3. **`python3 tests/drc_block.py <dir> [lp=<library dir>]`** (likewise) builds the block alone into a board
   through the toolkit (real rules and pours, the block's own layers, rules and solid pads) and runs
   KiCad's DRC: anything but a lone block's dangling ports (and its marked escapes) fails it, ground
   included. It fails, as it should, on a clearance cut to 0.05 mm and an overlapping courtyard. The
   build itself refuses copper KiCad would rename on save (a track touching only another net's pad
   silently becomes that net: found here by a planted track DRC never saw).
4. **`python3 tests/check_models.py [block ...]`** runs each `model.inc` against the same parts written
   flat, as in the board simulation the device models were validated in: they agree to 1e-12 (the
   buck's input current to 1 µA: two copies of its averaged loop, even two of the block itself, cross
   a comparison a time step apart). Each case carries a planted error in a copy of its model.inc,
   which the run must catch: R6 10k → 11k, C4 22u → 10u, R22 1k → 2k, R26 10k → 11k,
   C43 22u → 10u, R52 100 → 1k. This checks wiring and parameters; the physics was validated in those
   simulations (behavioural models fitted to guaranteed datasheet figures, the plug-in corners lumped
   and on copper, 200 × 8, 200 × 9 and, for the rev B cut, 200 × 24 Monte Carlo). The date-label-printer's device models are in
   [`models.inc`](models.inc) with their ground made a pin; renamed (ngspice takes a node called
   `gnd` as ground) and held 2 V above node 0, they match the originals (to 1e-10 V; the buck to 1 µV).
