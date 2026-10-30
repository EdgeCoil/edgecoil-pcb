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
outline and fill, design rule and the stackup match. Keep the `.kicad_pro` beside each board: the
design rules are read from it.

## Licences

Code: MIT. Circuit blocks: CERN-OHL-S-2.0. The toolkit ships no logo; a board passes its own mark
(`Config.logo_svg`).
