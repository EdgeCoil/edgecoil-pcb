# SPDX-FileCopyrightText: 2026 edgecoil
# SPDX-License-Identifier: MIT
"""Clean a frozen routing.json of the segments replay refuses (route.redundant): ones shorter than
0.05 mm, and ones lying wholly along another of the same net and layer. A short one is a joint
between its neighbours, so dropping it alone would leave them a gap apart, joined only by their
round ends (the near-miss joint replay also refuses): its neighbours' ends are snapped onto one of
its ends first. Long redundant ones add no copper and go as they are.

    python3 -m edgecoil_pcb.clean <routing.json> [--dry-run]

Rewrites the file in route.py --freeze's order and prints what it dropped and snapped. It repeats
until nothing is left (a snap can make the next segment redundant). A short segment with a via at
each end is left for a hand fix. Run it on a copy in the
board's tree, then rebuild and review the diff; it never touches the generator's locked copper.
"""
import json
import math
import sys

from .route import redundant, redundant_items

SHORT = 50000  # nm: route.redundant's limit


def _snap_end(items, s):
    """Which end of the short segment `s` the neighbours move to: one with a via of its net on it
    wins (moving tracks off a via would cut them from it); otherwise its start. None if both ends
    carry a via (it cannot be dropped without moving one)."""
    vias = {tuple(i["via"]) for i in items if "via" in i and i["net"] == s["net"]}
    a, b = tuple(s["start"]), tuple(s["end"])
    if a in vias and b in vias:
        return None
    return (b, a) if b in vias else (a, b)  # (keep, drop)


def clean(items, log=print):
    """The cleaned items (a new list) and the number of segments dropped. Long redundant segments go
    together (dropping one moves nothing); short ones one at a time, re-checked after each snap, since
    a snap moves its neighbours."""
    items = [dict(i) for i in items]
    dropped, stuck = 0, set()
    for _ in range(len(items) + 1):
        bad = [k for k in redundant_items(items) if id(items[k]) not in stuck]
        if not bad:
            break
        long_ = [k for k in bad if math.dist(items[k]["start"], items[k]["end"]) >= SHORT]
        if long_:
            for k in long_:
                log(f"dropped {items[k]['net']} {items[k]['layer']} {_mm(items[k])}: lies along another")
            gone = {id(items[k]) for k in long_}
        else:
            s = items[bad[0]]
            ends = _snap_end(items, s)
            if ends is None:
                log(f"kept    {s['net']} {s['layer']} {_mm(s)}: a via at both ends, fix it by hand")
                stuck.add(id(s))
                continue
            keep, drop = ends
            moved = 0
            for o in items:
                if o is s or "start" not in o or o["net"] != s["net"] or o["layer"] != s["layer"]:
                    continue
                for e in ("start", "end"):
                    if tuple(o[e]) == drop:
                        o[e] = list(keep)
                        moved += 1
            log(f"dropped {s['net']} {s['layer']} {_mm(s)} ({math.dist(s['start'], s['end']) / 1e6:.4f} mm); "
                f"{moved} neighbour end(s) snapped to ({keep[0] / 1e6:.4f}, {keep[1] / 1e6:.4f})")
            gone = {id(s)}
        dropped += len(gone)
        items = [i for i in items if id(i) not in gone]
        # A snap can leave a segment of zero length: it joins nothing.
        zero = [i for i in items if "start" in i and i["start"] == i["end"]]
        for z in zero:
            log(f"dropped {z['net']} {z['layer']} {_mm(z)}: zero length after a snap")
        dropped += len(zero)
        items = [i for i in items if not ("start" in i and i["start"] == i["end"])]
    return items, dropped


def _mm(s):
    return "(%.4f, %.4f)-(%.4f, %.4f)" % tuple(v / 1e6 for v in s["start"] + s["end"])


def write(path, items):
    """route.py --freeze's form: one item per line, sorted by net, vias last, then the item."""
    items = sorted(items, key=lambda i: (i["net"], "via" in i, json.dumps(i)))
    with open(path, "w") as f:
        f.write("[\n" + ",\n".join(json.dumps(i) for i in items) + "\n]\n")


def main(argv):
    if not argv or argv[0].startswith("-"):
        raise SystemExit(__doc__)
    path, dry = argv[0], "--dry-run" in argv[1:]
    items = json.load(open(path))
    out, n = clean(items)
    left = redundant(out)
    print(f"{path}: {n} segment(s) dropped, {len(out)} items left; redundant now: {left or 'none'}")
    if n and not dry:
        write(path, out)
    return 1 if left else 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
