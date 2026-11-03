# edgecoil-pcb

The shared pipeline behind EdgeCoil's generated KiCad boards, and (to come) a library of
pre-routed, pre-audited circuit blocks.

Each board keeps its own `gen.py` with only its netlist, placement and variants, and builds through
this package:

```python
from edgecoil_pcb import Config, Part, R, C, build

CFG = Config(project="my-board", here=HERE, ns=uuid.UUID("..."), variants={"my-board": variant})
build(CFG, sys.argv[1:])
```

`Config` options default to the newest behaviour. A board ordered before a fix landed sets the
option that keeps its committed output, so moving it onto the toolkit changes nothing; turning the
fix on is then a reviewed change in its next revision.

## Proving a port

Two builds of the same board differ in thousands of lines of `.kicad_pcb` and gerber text (fresh
UUIDs, item order), so a port is proven by a canonical dump instead:

    python3 -m edgecoil_pcb.canon committed.kicad_pcb rebuilt.kicad_pcb

It exits 0 and prints `identical` only if every footprint, pad, field, track, via, drawing, zone
outline, design rule and the stackup match as text, and every zone fill matches as geometry (the
area of the two fills' symmetric difference under 0.001 mm²: KiCad's fill can differ run to run by
a degenerate vertex with the same copper). Keep the `.kicad_pro` beside each board: the design
rules are read from it. Negative controls it fails, as it should: a via moved 1 µm, a resistor's
value, the mask colour, a 0.25 mm² notch in a pour.

Ported so far, each identical to its committed board: cec-bridge, tune-button xiao, c3, c3-jst
and the three-board panel; the date-label-printer with its power copper declared as data, and again
composed from the four blocks cut from it.

## Composing from blocks

`blocks/` holds circuit blocks: parts with their reviewed copper, a SPICE subcircuit and findings
(see its README). Most use only KiCad's stock libraries; a block whose parts KiCad lacks names the
board library they come from (block.json `local_libs`), and a board supplies its own copy.

## Locked power copper

The router thins power paths into small pads and knows nothing of Kelvin sensing, so a board lays
those itself, locked. It declares them as data rather than in a hook:

```python
from edgecoil_pcb import power
CFG = Config(..., power_copper=power.PowerCopper(
    runs=[("VBUS", "B.Cu", [(13.45, 47.54), (20.6, 40.4), (35.4, 40.4)], 1.2)],   # net, layer, polyline (mm), width
    vias=[("VBUS", (35.4, 40.4), 0.8, 0.4)],                                         # net, at, diameter, drill
    sense=[("VPO", (59.8, 44.5), (60.6, 42.0))],                                     # Kelvin taps (sense_width 0.25)
    gnd_vias=[(51.8, 32.6)],                                                         # at the return (gnd_via 0.6/0.3)
    escapes=[("U4", "F.Cu", 0.2, [("VBUS", (-0.225, -0.80), (-0.225, -2.00))])],     # from a part's pad, offsets from its centre
    via_drills=[("VBUS", (13.45, 47.54), 0.4)]),                                     # re-drill a via the toolkit laid
    solid_pads=(("U9", "4"),))                                                       # pads joined solid to the pour
```

It is laid after `board_hooks` and before block copper, and checked like block copper for a net
renamed on save. `power.items(board, pc)` gives it in routing.json's form, which is how
`blocks.cut` takes a board's locked copper along with its routing.

## Routing and assembly files

A board's `route.py` is three lines: `from edgecoil_pcb.route import cli; from gen import CFG; cli(CFG, argv)`.
It replays `<variant>/routing.json` if there is one (refusing redundant segments, joints made only
by overlapping copper, and lost back pour), autoroutes with Freerouting if not, and `--patch`
reroutes only a ripped box. After a hand edit to routing.json:

- `route.py --clean <variant>` (or `python3 -m edgecoil_pcb.clean routing.json`) drops the segments
  replay would refuse as redundant: under 0.05 mm, or lying along another. A short one's neighbours
  are snapped onto one of its ends first (the one on a via, if either is), so no near-miss joint is
  left behind.
- `route.py --restitch <variant>` (or `python3 -m edgecoil_pcb.restitch board.kicad_pcb`) replays
  routing.json onto the freshly generated board, runs the stitcher and the pour checks, and saves it;
  `route.py --freeze` then keeps the new vias.

`python3 -m edgecoil_pcb.jlc` writes JLCPCB's BOM and CPL. Its rotation and offset table is
checked against JLC's own footprints by

    python3 -m edgecoil_pcb.jlc_verify board.kicad_pcb [...]

which places each LCSC part's EasyEDA footprint as the CPL would and checks every pad lands on
KiCad's: by number, or by anode/cathode where the libraries number them differently; centred to
0.05 mm (or 5 % of the pad along that axis); and with no other rotation passing as well. It caught
nine of nine planted errors. `jlc.PROVENANCE` records each check; the build warns about any part
without one.

## Licences

Code: MIT. Circuit blocks: CERN-OHL-S-2.0. The toolkit ships no third-party symbol or footprint
library: blocks use KiCad's own, or name a board library a board supplies. It ships no logo either; a
board passes its own mark (`Config.logo_svg`).
