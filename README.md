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
and the three-board panel.

## Composing from blocks

`blocks/` holds circuit blocks: parts with their reviewed copper, a SPICE subcircuit and findings
(see its README). They use only KiCad's stock libraries.

## Routing and assembly files

A board's `route.py` is three lines: `from edgecoil_pcb.route import cli; from gen import CFG; cli(CFG, argv)`.
It replays `<variant>/routing.json` if there is one (refusing redundant segments, joints made only
by overlapping copper, and lost back pour), autoroutes with Freerouting if not, and `--patch`
reroutes only a ripped box.

`python3 -m edgecoil_pcb.jlc` writes JLCPCB's BOM and CPL. Its rotation and offset table is
checked against JLC's own footprints by

    python3 -m edgecoil_pcb.jlc_verify board.kicad_pcb [...]

which places each LCSC part's EasyEDA footprint as the CPL would and checks every pad lands on
KiCad's: by number, or by anode/cathode where the libraries number them differently; centred to
0.05 mm (or 5 % of the pad along that axis); and with no other rotation passing as well. It caught
nine of nine planted errors. `jlc.PROVENANCE` records each check; the build warns about any part
without one.

## Licences

Code: MIT. Circuit blocks: CERN-OHL-S-2.0. The blocks use KiCad's own symbol and footprint libraries
only. The toolkit ships no logo; a board passes its own mark
(`Config.logo_svg`).
