# SPDX-FileCopyrightText: 2026 edgecoil
# SPDX-License-Identifier: MIT
"""KiCad DRC of a block on its own: the block placed alone on a small board built by the toolkit
(the same design rules and ground pours a real board gets), pours filled, kicad-cli DRC run. Every
violation is reported except the ones a lone block must have: its ports go nowhere (unconnected
items) and there is no schematic to compare with.

    python3 blocks/tests/drc_block.py <block dir> [<block.json to use instead>] [nickname=dir ...]

A block whose parts come from a board's own library (block.json "local_libs") needs that library:
nickname=dir names the directory holding <nickname>.kicad_sym and <nickname>.pretty. The block's
"copper_layers", "min_track_width", "dru_rules" and "solid_pads" are applied as a board would.

Exit 1 on any other violation. Needs KiCad 9 (pcbnew, kicad-cli) and KICAD_SYMBOL_DIR.
"""
import json
import os
import subprocess
import sys
import tempfile
import uuid

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.dirname(os.path.dirname(HERE)))
import pcbnew  # noqa: E402

from edgecoil_pcb import Config, blocks, build  # noqa: E402

EXPECTED = {"unconnected_items", "schematic_parity", "lib_footprint_mismatch", "lib_footprint_issues",
            "silk_overlap", "silk_over_copper", "silk_edge_clearance", "text_height", "missing_footprint",
            }
# A lone block has no stitching vias (route.py adds them on a real board), so its back pour is an
# island: that one is expected. An island on the front is not, and is reported.
EXPECTED_ONLY_ON_BACK = {"isolated_copper"}


def main(block_dir, override=None, libs=None):
    b = blocks.Block(json.load(open(override or os.path.join(block_dir, "block.json"))), os.path.join(block_dir, "block.json"))
    libs = libs or {}
    missing = sorted(set(b.data.get("local_libs", {})) - set(libs))
    if missing:
        raise SystemExit(f"{b.name}: needs library {missing}: pass nickname=dir")
    pts = [p["at"] for p in b.data["parts"]] + [[v / 1e6 for v in i.get("start", i.get("via"))] for i in b.data["copper"]]
    x0, y0 = min(p[0] for p in pts) - 8, min(p[1] for p in pts) - 8
    w, h = max(p[0] for p in pts) - x0 + 8, max(p[1] for p in pts) - y0 + 8
    at = (-x0, -y0)
    nets = {p: p for p in b.ports}
    with tempfile.TemporaryDirectory() as d:
        cfg = Config(project="drc", here=d, ns=uuid.uuid4(), variants={}, width=w,
                     power_nets=tuple(n for n in b.ports if n not in ("GND",)),
                     esd_refs=b.board_refs("esd_ground"),
                     local_libs={k: (os.path.abspath(v), "") for k, v in libs.items()},
                     copper_layers=b.data.get("copper_layers", 2),
                     min_track_width=b.data.get("min_track_width", 0.2),
                     dru_rules=b.dru_rules(), solid_pads=b.solid_pads(),
                     # no back text: its via keepout is the test board's, not the block's
                     back_text=lambda name, w, h: [])
        cfg.variants = {"drc": lambda: (b.parts(at, nets=nets), h, [], [], {"width": w})}
        cfg.block_copper = b.copper(at, nets=nets)
        build(cfg, ["drc"])
        path = cfg.base("drc") + ".kicad_pcb"
        board = pcbnew.LoadBoard(path)
        pcbnew.ZONE_FILLER(board).Fill(board.Zones())
        board.Save(path)
        rpt = os.path.join(d, "drc.json")
        subprocess.run(["kicad-cli", "pcb", "drc", "--format", "json", "--severity-all", "-o", rpt, path],
                       capture_output=True)
        r = json.load(open(rpt))
        if os.environ.get("DRC_DUMP"):
            import shutil; shutil.copy(rpt, os.environ["DRC_DUMP"]); shutil.copy(path, os.environ["DRC_DUMP"] + ".kicad_pcb")
    # A locked escape (block.json copper marked "escape") runs from a pad out to where a board joins
    # it: alone, it ends on nothing. Expected for those, by net and length, and for nothing else.
    import math
    import re
    escapes = [(i["net"], round(math.dist(i["start"], i["end"]) / 1e6, 4)) for i in b.data["copper"] if i.get("escape")]

    def expected(v):
        # Ports go nowhere on a lone block, except ground: the pours must join every GND pad.
        if v["type"] == "unconnected_items" and any("[GND]" in i["description"] for i in v.get("items", [])):
            return False
        if v["type"] == "track_dangling":
            m = re.match(r"Track \[([^]]*)\] on \S+, length ([0-9.]+) mm", v["items"][0]["description"])
            return bool(m) and (m.group(1), float(m.group(2))) in escapes
        if v["type"] in EXPECTED:
            return True
        return v["type"] in EXPECTED_ONLY_ON_BACK and all("on B.Cu" in i["description"] for i in v.get("items", []))
    found = [v for v in r.get("violations", []) + r.get("unconnected_items", []) if not expected(v)]
    for v in found:
        print(f"  {v['type']}: {v['description']} — " + "; ".join(i["description"] for i in v.get("items", [])))
    print(f"{b.name}: {len(found)} DRC violation(s) beyond a lone block's unconnected ports")
    return 1 if found else 0


if __name__ == "__main__":
    args = [a for a in sys.argv[1:] if "=" not in a]
    sys.exit(main(*args[:2], libs=dict(a.split("=", 1) for a in sys.argv[1:] if "=" in a)))
