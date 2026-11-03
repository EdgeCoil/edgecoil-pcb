# SPDX-FileCopyrightText: 2026 edgecoil
# SPDX-License-Identifier: MIT
"""Re-stitch a board after a hand edit to its frozen routing: replay routing.json onto the freshly
generated board, then run the stitcher (route.stitch) and the pour checks (route.lost_pour,
crowded_pins, cut_plane), as an autoroute attempt does. A track moved or added by hand can fence off
a pocket of ground pour that no via reaches; the fill would then drop it, and replay refuses a board
that loses more than route.LOST_POUR. The stitcher puts vias where both layers' pour now surrounds
one, keeping the ones already there (a stitching via is part of routing.json).

    python3 -m edgecoil_pcb.restitch <board.kicad_pcb> [routing.json] [--freeze]
    python3 route.py --restitch <variant>        (the same, through the board's own route.py)

The board must be as gen.py writes it (no routing yet). It prints the pour lost before and after and
how many vias it added, and saves the board; --freeze then writes its copper back to routing.json
(the locked copper stays out, as route.py --freeze leaves it). Review the diff before the next build.
"""
import json
import os
import sys

import pcbnew

from . import route as R


def lay(board, items):
    """routing.json items onto the board, unlocked (they are the router's copper)."""
    for i in items:
        net = board.FindNet(i["net"])
        if net is None:
            raise SystemExit(f"restitch: routing on net {i['net']}, which the board doesn't have")
        if "via" in i:
            t = pcbnew.PCB_VIA(board)
            t.SetPosition(pcbnew.VECTOR2I(*i["via"])); t.SetLayerPair(pcbnew.F_Cu, pcbnew.B_Cu)
            t.SetWidth(i["d"]); t.SetDrill(i["drill"])
        else:
            t = pcbnew.PCB_TRACK(board)
            t.SetStart(pcbnew.VECTOR2I(*i["start"])); t.SetEnd(pcbnew.VECTOR2I(*i["end"]))
            t.SetLayer(board.GetLayerID(i["layer"])); t.SetWidth(i["w"])
        t.SetNet(net)
        board.Add(t)


def restitch(path, routing, log=print):
    """Replay, stitch and check; saves the board at `path`. Returns (vias added, lost pour mm2 after,
    crowded pins, nets on the In1 plane)."""
    board = pcbnew.LoadBoard(path)
    if any(not t.IsLocked() for t in board.GetTracks()):
        raise SystemExit(f"restitch: {path} already carries routing; regenerate it first (gen.py)")
    items = json.load(open(routing))
    lay(board, items)
    log(f"replayed {len(items)} items; pour lost to islands {R.lost_pour(board):.1f} mm2")
    board.Save(path)
    # Reload from disk before filling (SWIG wrappers after many Adds, as route_once does), then stitch with
    # islands kept: a pocket fenced in by tracks is otherwise removed before it can get a via.
    board = pcbnew.LoadBoard(path)
    for z in board.Zones():
        if not z.GetIsRuleArea():
            z.SetIslandRemovalMode(pcbnew.ISLAND_REMOVAL_MODE_NEVER)
    pcbnew.ZONE_FILLER(board).Fill(board.Zones())
    added = R.stitch(board)
    lost, crowded, cut = R.lost_pour(board), R.crowded_pins(board), R.cut_plane(board)
    log(f"stitched {added} via(s); pour lost {lost:.1f} mm2 (limit {R.LOST_POUR}); "
        f"crowded pins {crowded or 'none'}; In1 cut by {cut or 'nothing'}")
    board.Save(path)
    from .blocks import renetted
    moved = renetted(path, items)
    if moved:
        raise SystemExit(f"restitch: routing items changed net on save (each touches another net's pad): {moved}")
    return added, lost, crowded, cut


def freeze(path, routing):
    """The board's unlocked copper back to routing.json, as route.freeze writes it."""
    board = pcbnew.LoadBoard(path)
    items = []
    for t in board.GetTracks():
        if t.IsLocked():
            continue
        if t.GetClass() == "PCB_VIA":
            p = t.GetPosition()
            items.append({"net": t.GetNetname(), "via": [p.x, p.y], "d": t.GetWidth(pcbnew.F_Cu), "drill": t.GetDrillValue()})
        else:
            a, b = t.GetStart(), t.GetEnd()
            items.append({"net": t.GetNetname(), "layer": board.GetLayerName(t.GetLayer()),
                          "start": [a.x, a.y], "end": [b.x, b.y], "w": t.GetWidth()})
    items.sort(key=lambda i: (i["net"], "via" in i, json.dumps(i)))
    with open(routing, "w") as f:
        f.write("[\n" + ",\n".join(json.dumps(i) for i in items) + "\n]\n")
    return len(items)


def main(argv):
    args = [a for a in argv if not a.startswith("--")]
    if not args:
        raise SystemExit(__doc__)
    path = args[0]
    routing = args[1] if len(args) > 1 else os.path.join(os.path.dirname(path), "routing.json")
    added, lost, crowded, cut = restitch(path, routing)
    if "--freeze" in argv:
        print(f"froze {freeze(path, routing)} items in {routing}")
    return 1 if lost > R.LOST_POUR or crowded or cut else 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
