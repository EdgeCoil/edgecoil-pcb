# SPDX-FileCopyrightText: 2026 edgecoil
# SPDX-License-Identifier: MIT
"""Circuit blocks: parts with their reviewed copper, placed on a board as one piece.

A block is a directory under blocks/ holding block.json (parts in the block's own frame, its ports,
its copper), model.inc (a SPICE subcircuit) and FINDINGS.md (what audits and simulations found and
what was accepted). A board places it:

    core = blocks.load("esp32-c3-wroom-02")
    parts += core.parts(at=(14.0, 6.8), refs={...}, nets={"3V3": "3V3", ...})
    CFG.blocks.append(core.copper(at=(14.0, 6.8), nets={...}))

The block's copper is laid locked by gen.py (route.py --freeze leaves locked copper out of
routing.json), so the router only joins block to block. A block is cut from a board that has
passed review with `python3 -m edgecoil_pcb.blocks cut`, which also proves the cut: the board
rebuilt from its blocks plus the remaining routing must be canonically identical.

Frames: the block's origin is its anchor part's position; `rot` is 0, 90, 180 or 270 degrees
counter-clockwise as KiCad shows it (y down), the same as a footprint's rotation.
"""
import json
import math
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
BLOCKS = os.path.join(os.path.dirname(HERE), "blocks")


def _rot(x, y, rot):
    """(x, y) turned by `rot` degrees as KiCad turns a footprint (counter-clockwise on screen, y down)."""
    a = math.radians(rot)
    c, s = round(math.cos(a)), round(math.sin(a))
    return x * c + y * s, -x * s + y * c


class Block:
    def __init__(self, data, path=None):
        self.data, self.path = data, path
        self.name = data["name"]
        self.ports = data["ports"]

    def _net(self, n, nets, prefix):
        if n in self.data.get("optional_ports", ()):
            return nets.get(n, "")  # a pin the block leaves free: no connection unless the board maps it
        if n in self.ports:
            if n not in nets:
                raise SystemExit(f"block {self.name}: port {n} not connected (nets= has {sorted(nets)})")
            return nets[n]
        return prefix + n  # an internal net, kept apart from another instance's

    def parts(self, at, rot=0, refs=None, nets=None, prefix="", libs=None):
        """The block's parts, placed: board refs from `refs` (local -> board), else prefixed. `libs`
        renames library nicknames (a block's part -> a board's own copy of it)."""
        from .parts import Part
        refs, nets, libs = refs or {}, nets or {}, libs or {}

        def lib(lib_id):
            nick, _, name = lib_id.partition(":")
            return f"{libs.get(nick, nick)}:{name}" if name else lib_id
        if rot % 90:
            raise SystemExit(f"block {self.name}: rot must be a multiple of 90")
        out = []
        for p in self.data["parts"]:
            dx, dy = _rot(p["at"][0], p["at"][1], rot)
            out.append(Part(refs.get(p["ref"], prefix + p["ref"]), lib(p["sym"]) if p["sym"] else p["sym"], lib(p["fp"]), p["value"],
                            {k: (self._net(v, nets, prefix) if v else "") for k, v in p["pins"].items()},
                            (round(at[0] + dx, 6), round(at[1] + dy, 6)), (p["rot"] + rot) % 360,
                            mpn=p.get("mpn", ""), note=p.get("note", ""), lcsc=p.get("lcsc", ""),
                            side=p.get("side", "F")))
        return out

    def board_refs(self, key, refs=None, prefix=""):
        """The board references of the block parts listed under `key` in block.json (e.g.
        "esd_ground": the parts for Config.esd_refs)."""
        refs = refs or {}
        return tuple(refs.get(r, prefix + r) for r in self.data.get(key, ()))

    def solid_pads(self, refs=None, prefix=""):
        """The block's pads that join the pours solid (block.json "solid_pads"), as board (ref, pad)
        pairs for Config.solid_pads."""
        refs = refs or {}
        return tuple((refs.get(r, prefix + r), n) for r, n in self.data.get("solid_pads", ()))

    def dru_rules(self, refs=None, prefix=""):
        """The block's own design rules (block.json "dru_rules", e.g. a fine-pitch part's pad-to-pad
        clearance) for Config.dru_rules, its references renamed to the board's."""
        refs = refs or {}
        out = []
        for rule in self.data.get("dru_rules", ()):
            for r in sorted((p["ref"] for p in self.data["parts"]), key=len, reverse=True):
                rule = rule.replace(f"'{r}'", f"'{refs.get(r, prefix + r)}'")
            out.append(rule)
        return tuple(out)

    def copper(self, at, rot=0, nets=None, prefix=""):
        """The block's tracks and vias in routing.json's form, board coordinates (nm)."""
        nets = nets or {}
        ox, oy = round(at[0] * 1e6), round(at[1] * 1e6)

        def pt(p):
            x, y = _rot(p[0], p[1], rot)
            return [ox + x, oy + y]
        out = []
        for i in self.data["copper"]:
            j = dict(i, net=self._net(i["net"], nets, prefix))
            for k in ("start", "end", "via"):
                if k in j:
                    j[k] = pt(j[k])
            out.append(j)
        return out


def load(name, root=BLOCKS):
    path = os.path.join(root, name, "block.json")
    return Block(json.load(open(path)), path)


def lay(board, items):
    """Lay block copper on a board, locked."""
    import pcbnew
    for i in items:
        net = board.FindNet(i["net"])
        if net is None:
            raise SystemExit(f"block copper on net {i['net']}, which the board doesn't have")
        if "via" in i:
            t = pcbnew.PCB_VIA(board)
            t.SetPosition(pcbnew.VECTOR2I(*i["via"])); t.SetLayerPair(pcbnew.F_Cu, pcbnew.B_Cu)
            t.SetWidth(i["d"]); t.SetDrill(i["drill"])
        else:
            t = pcbnew.PCB_TRACK(board)
            t.SetStart(pcbnew.VECTOR2I(*i["start"])); t.SetEnd(pcbnew.VECTOR2I(*i["end"]))
            t.SetLayer(board.GetLayerID(i["layer"])); t.SetWidth(i["w"])
        t.SetNet(net); t.SetLocked(True)
        board.Add(t)


def renetted(path, items):
    """Laid copper whose net changed on the way to the file. KiCad renames a track or via whose only
    connection is another net's pad to that net when the board is saved, silently, so a frozen item
    placed onto the wrong pad would leave its record and the board disagreeing (found 2026-10-30 by a
    planted track that DRC then never saw). Returns [(item's net, the board's, where)]."""
    import pcbnew
    board = pcbnew.LoadBoard(path)
    found = {}
    for t in board.GetTracks():
        if t.GetClass() == "PCB_VIA":
            key = ("via", t.GetPosition().x, t.GetPosition().y)
        else:
            a, b = (t.GetStart().x, t.GetStart().y), (t.GetEnd().x, t.GetEnd().y)
            key = ("seg", board.GetLayerName(t.GetLayer())) + tuple(sorted([a, b]))
        found.setdefault(key, []).append(t.GetNetname())
    out = []
    for i in items:
        if "via" in i:
            key = ("via", i["via"][0], i["via"][1])
        else:
            key = ("seg", i["layer"]) + tuple(sorted([tuple(i["start"]), tuple(i["end"])]))
        nets = found.get(key, [])
        if i["net"] not in nets:
            where = i.get("via") or i["start"]
            out.append((i["net"], nets[0] if nets else "missing", (where[0] / 1e6, where[1] / 1e6)))
    return out


# ------------------------------------------------------------------------------------------- cutting

def _regions(board, refs, grow=250000):
    """Each block part's courtyard (or pads, if it has none), grown by `grow` nm: where its copper may lie."""
    import pcbnew
    boxes = []
    for fp in board.GetFootprints():
        if fp.GetReference() not in refs:
            continue
        box = pcbnew.BOX2I()
        for g in fp.GraphicalItems():
            if g.GetLayer() in (pcbnew.F_CrtYd, pcbnew.B_CrtYd):
                box.Merge(g.GetBoundingBox())
        if not box.GetWidth():
            for p in fp.Pads():
                box.Merge(p.GetBoundingBox())
        boxes.append((box.GetLeft() - grow, box.GetTop() - grow, box.GetRight() + grow, box.GetBottom() + grow))
    return boxes


def _inside(p, boxes):
    return any(x0 <= p[0] <= x1 and y0 <= p[1] <= y1 for x0, y0, x1, y1 in boxes)


COPPER = ("F.Cu", "In1.Cu", "In2.Cu", "B.Cu")


def _seg_dist(p, a, b):
    """Distance from p to segment a-b, and how far along it (0..1) the nearest point lies."""
    l2 = (b[0] - a[0]) ** 2 + (b[1] - a[1]) ** 2
    u = 0.0 if l2 == 0 else max(0.0, min(1.0, ((p[0] - a[0]) * (b[0] - a[0]) + (p[1] - a[1]) * (b[1] - a[1])) / l2))
    return math.hypot(p[0] - (a[0] + u * (b[0] - a[0])), p[1] - (a[1] + u * (b[1] - a[1]))), u


class Cut:
    """The result of cut(): `block` (board coordinates), `rest` (the routing left to the board),
    `rest_locked` (the locked copper left to it), `ports`, `internal`, `anchor` (nm), and `split`:
    tracks the block needed only part of, which stay with the board whole (a segment is never split,
    so the board stays canonically the same)."""
    def __init__(self, **kw):
        self.__dict__.update(kw)


def cut(board_path, routing, refs, anchor, locked=(), tol=1000):
    """Split a reviewed board's copper between a block made of the parts `refs` and the rest of the
    board. `routing` is the frozen routing (routing.json), `locked` the generator's own copper in the
    same form (power.items(): power runs, escapes, sense tracks, ground vias); both are cut alike and
    each remainder is returned separately.

    Block copper is every item on an internal net, and on each port net the copper that joins the
    block's own pads to each other. The net's copper is a graph: its nodes are track ends, the points
    where one track's end lands on another's centreline (a T, as power runs tee into a bus) and vias
    (a via joins every layer it passes); its edges are the track pieces between them. It is cut
    wherever it reaches another part's pad, and dead-end pieces are pruned until none is left. What
    survives lies on a path from one block pad to another: the branches out to the rest of the board
    are the joins, and stay with the board. A via on a net with a pour (GND) also reaches the plane,
    so a block pad's own ground via stays with the block; and a locked via on that net that no track
    reaches (a ground via placed by the pour it sits in) goes with the part whose pad of that net is
    nearest. A track is taken whole or not at all.

    (Keeping only copper inside the parts' courtyards, as a first version did, dropped every track
    crossing the gap between two of the block's own parts: the LDO's output to its capacitor.)"""
    import pcbnew
    board = pcbnew.LoadBoard(board_path)
    lid = {n: board.GetLayerID(n) for n in COPPER}
    pads_by_net = {}
    for fp in board.GetFootprints():
        for p in fp.Pads():
            n = p.GetNetname()
            if n and not n.startswith("unconnected-"):
                pads_by_net.setdefault(n, []).append((fp.GetReference(), p))
    nets = {n for n, ps in pads_by_net.items() if any(r in refs for r, _ in ps)}
    internal = {n for n in nets if all(r in refs for r, _ in pads_by_net[n])}
    ports = sorted(nets - internal)
    planes = {z.GetNetname() for z in board.Zones() if not z.GetIsRuleArea() and z.GetNetname()}
    items = [("routing", k, i) for k, i in enumerate(routing)] + [("locked", k, i) for k, i in enumerate(locked)]
    taken, split, escapes = set(), [], set()

    def on_pad(pt, p, layers):
        return any(p.IsOnLayer(lid[l]) for l in layers) and p.HitTest(pcbnew.VECTOR2I(int(pt[0]), int(pt[1])))

    for net in sorted(nets):
        idx = [n for n, (_, _, i) in enumerate(items) if i["net"] == net]
        if net in internal:
            taken.update(idx)
            continue
        mine = [p for r, p in pads_by_net[net] if r in refs]
        theirs = [p for r, p in pads_by_net[net] if r not in refs]
        vias = [n for n in idx if "via" in items[n][2]]
        tracks = [n for n in idx if "via" not in items[n][2]]
        # Nodes: each via is one node on every layer; any other point is a node per layer, points
        # within `tol` of each other merged.
        node_at, kind, pad_hits = [], {}, {}

        def node(pt, layer):
            for v in vias:
                vi = items[v][2]
                if math.dist(pt, vi["via"]) <= max(vi["d"] / 2, tol):
                    return ("via", v)
            for key, l, q in node_at:
                if l == layer and math.dist(pt, q) <= tol:
                    return key
            key = ("pt", len(node_at))
            node_at.append((key, layer, pt))
            return key

        def classify(key, pt, layers):
            if key in kind:
                return
            if any(on_pad(pt, p, layers) for p in theirs):
                kind[key] = "cut"
            else:
                hits = {k for k, p in enumerate(mine) if on_pad(pt, p, layers)}
                kind[key] = "pad" if hits else "free"
                pad_hits[key] = hits
        for v in vias:
            key = ("via", v)
            classify(key, items[v][2]["via"], COPPER)
        # Pieces: each track split at every other track end or via that lands on its centreline.
        pieces = []  # (track index, node a, node b)
        ends = {n: [tuple(items[n][2]["start"]), tuple(items[n][2]["end"])] for n in tracks}
        for t in tracks:
            i = items[t][2]
            a, b = ends[t]
            stops = [(0.0, a), (1.0, b)]
            for u in tracks:
                if u != t and items[u][2]["layer"] == i["layer"]:
                    for e in ends[u]:
                        d, f = _seg_dist(e, a, b)
                        if d <= tol and 0 < f < 1 and math.dist(e, a) > tol and math.dist(e, b) > tol:
                            stops.append((f, e))
            for v in vias:
                c = tuple(items[v][2]["via"])
                d, f = _seg_dist(c, a, b)
                if d <= tol and 0 < f < 1 and math.dist(c, a) > tol and math.dist(c, b) > tol:
                    stops.append((f, c))
            stops.sort()
            keys = []
            for f, pt in stops:
                key = node(pt, i["layer"])
                classify(key, pt, (i["layer"],))
                if not keys or keys[-1] != key:
                    keys.append(key)
            pieces += [(t, x, y) for x, y in zip(keys, keys[1:])]
        if len({p[0] for p in pieces}) < len(tracks):  # a track wholly inside one node (a dot)
            for t in tracks:
                if not any(p[0] == t for p in pieces):
                    key = node(ends[t][0], items[t][2]["layer"])
                    classify(key, ends[t][0], (items[t][2]["layer"],))
                    pieces.append((t, key, key))
        alive = set(range(len(pieces)))
        via_alive = set(vias)
        plane = net in planes

        def leads(key, but=None):
            # (A piece from a node to itself, a track lying inside one via's copper, joins nothing.)
            n = sum(1 for k in alive if k != but and pieces[k][1] != pieces[k][2] and key in pieces[k][1:])
            n += len(pad_hits.get(key, ())) if kind[key] == "pad" else 0
            if key[0] == "via" and plane:
                n += 1  # a via reaches the pour
            return n

        changed = True
        while changed:
            changed = False
            for k in list(alive):
                _, x, y = pieces[k]
                if kind[x] == "cut" or kind[y] == "cut" or (leads(x) < 2 if x == y else (leads(x, k) == 0 or leads(y, k) == 0)):
                    alive.discard(k)
                    changed = True
            for v in list(via_alive):
                key = ("via", v)
                if kind[key] == "cut" or leads(key) < 2:
                    via_alive.discard(v)
                    changed = True
            if not changed and plane:
                # A via reaches the pour, so it ends a path; but a path from one via to another joins
                # the plane to itself. Keep only pieces whose stretch between vias holds a block pad.
                comp = {}

                def root(x):
                    while comp.setdefault(x, x) != x:
                        x = comp[x]
                    return x
                def end(x, k):  # a via node, split per piece
                    return ("at-via", x[1], k) if x[0] == "via" else x
                for k in alive:
                    t, x, y = pieces[k]
                    comp[root(end(x, k))] = root(end(y, k))
                padded = {root(x) for x in list(comp) if x[0] == "pt" and kind[x] == "pad"}
                for k in list(alive):
                    t, x, y = pieces[k]
                    if root(end(x, k)) not in padded:
                        alive.discard(k)
                        changed = True
            if not changed:
                # A track the block needs only part of (a bus running on past the block's last tee)
                # stays with the board whole; prune again without it.
                for t in tracks:
                    mine_pieces = [k for k, p in enumerate(pieces) if p[0] == t]
                    if any(k in alive for k in mine_pieces) and not all(k in alive for k in mine_pieces):
                        split.append(items[t][2])
                        alive -= set(mine_pieces)
                        changed = True
        taken.update(t for t in tracks if all(k in alive for k, p in enumerate(pieces) if p[0] == t))
        taken.update(via_alive)
        # A locked escape (a track the generator lays from one of the block's pads out to where the
        # router joins it, as out of a fine-pitch part) stays with the block, though it is a join:
        # the router cannot lay it. Not a locked track running on to other locked copper or into
        # another part's pad (the board's own power run).
        for t in tracks:
            if items[t][0] != "locked" or t in taken:
                continue
            ps = [p for p in pieces if p[0] == t]
            first, last = ps[0][1], ps[-1][2]
            if (kind[first] == "pad") == (kind[last] == "pad"):
                continue
            far = last if kind[first] == "pad" else first
            if kind[far] == "cut" or any(items[p[0]][0] == "locked" and p[0] != t and far in p[1:] for p in pieces):
                continue
            taken.add(t)
            escapes.add(t)
        if plane:
            # Locked vias on the pour net that nothing joins by track: with the part whose pad is nearest.
            for v in vias:
                src, _, vi = items[v]
                if src != "locked" or v in taken or any(("via", v) in p[1:] for p in pieces):
                    continue
                if kind[("via", v)] == "cut":
                    continue
                near = min(pads_by_net[net], key=lambda rp: math.dist(vi["via"], (rp[1].GetPosition().x, rp[1].GetPosition().y)))
                if near[0] in refs:
                    taken.add(v)
    # Escapes are marked: on the block alone they end on nothing (a port's join), and drc_block expects that.
    block = [dict(items[n][2], escape=True) if n in escapes else items[n][2] for n in sorted(taken)]
    rest = [i for n, (src, _, i) in enumerate(items) if src == "routing" and n not in taken]
    rest_locked = [i for n, (src, _, i) in enumerate(items) if src == "locked" and n not in taken]
    a = board.FindFootprintByReference(anchor).GetPosition()
    return Cut(block=block, rest=rest, rest_locked=rest_locked, ports=ports, internal=sorted(internal),
               anchor=(a.x, a.y), split=split)


def to_local(items, anchor, rot=0):
    """Board copper to the block's frame (the inverse of Block.copper at rot=0)."""
    out = []
    for i in items:
        j = dict(i)
        for k in ("start", "end", "via"):
            if k in j:
                j[k] = [j[k][0] - anchor[0], j[k][1] - anchor[1]]
        out.append(j)
    return out


def selftest(block, cfg_libs=None, at=(60.0, 60.0)):
    """Place the block alone at each rotation and check its copper still does its job: every internal
    net is one connected piece (pads and copper), and every copper item touches its own net's pads or
    copper. Returns a list of problems; empty is a pass."""
    import pcbnew
    from .config import Config
    from .geom import mm
    cfg = Config(project="selftest", here=os.path.dirname(block.path), ns=__import__("uuid").uuid4(), variants={},
                 local_libs=cfg_libs or {})
    problems = []
    inner = (pcbnew.In1_Cu, pcbnew.In2_Cu) if block.data.get("copper_layers", 2) == 4 else ()
    for rot in (0, 90, 180, 270):
        board = pcbnew.BOARD()
        board.GetDesignSettings().SetCopperLayerCount(block.data.get("copper_layers", 2))
        nets = {p: p for p in block.ports}
        parts = block.parts(at, rot, nets=nets)
        names = sorted({n for p in parts for n in p.pins.values() if n})
        for n in names:
            board.Add(pcbnew.NETINFO_ITEM(board, n))
        for p in parts:
            lib, fpname = p.fp.split(":")
            fp = pcbnew.FootprintLoad(os.path.join(cfg.lib_dir(lib) or cfg.footprint_dir, lib + ".pretty"), fpname)
            fp.SetReference(p.ref)
            board.Add(fp)
            fp.SetPosition(mm(*p.at)); fp.SetOrientationDegrees(p.rot)
            if p.side == "B":
                fp.Flip(fp.GetPosition(), pcbnew.FLIP_DIRECTION_LEFT_RIGHT)
            for pad in fp.Pads():
                n = p.pins.get(pad.GetNumber(), "")
                if n:
                    pad.SetNet(board.FindNet(n))
        lay(board, block.copper(at, rot, nets=nets))
        # Union-find over pads and copper, joined where copper ends meet pads, each other or vias.
        nodes = [("pad", p) for p in board.GetPads() if p.GetNetname()] + [("cu", t) for t in board.GetTracks()]
        parent = list(range(len(nodes)))

        def find(i):
            while parent[i] != i:
                parent[i] = parent[parent[i]]
                i = parent[i]
            return i

        def ends(t):
            return [t.GetPosition()] if t.GetClass() == "PCB_VIA" else [t.GetStart(), t.GetEnd()]

        def layers(o):
            return {l for l in (pcbnew.F_Cu, pcbnew.B_Cu) + inner if o.IsOnLayer(l)}

        for i, (ki, a) in enumerate(nodes):
            if ki != "cu":
                continue
            for j, (kj, b) in enumerate(nodes):
                if i == j or a.GetNetname() != b.GetNetname() or not (layers(a) & layers(b)):
                    continue
                hit = (any(b.HitTest(e) for e in ends(a)) if kj == "pad"
                       else any(b.HitTest(e) for e in ends(a)) or any(a.HitTest(e) for e in ends(b)))
                if hit:
                    parent[find(i)] = find(j)
        for net in block.data.get("internal", []):
            members = [i for i, (_, o) in enumerate(nodes) if o.GetNetname() == net]
            roots = {find(i) for i in members}
            if len(roots) > 1:
                problems.append(f"rot {rot}: internal net {net} in {len(roots)} pieces")
        for i, (k, o) in enumerate(nodes):
            if k == "cu" and not any(find(j) == find(i) for j, (kj, _) in enumerate(nodes) if kj == "pad"):
                e = ends(o)[0]
                problems.append(f"rot {rot}: {o.GetNetname()} copper at ({e.x / 1e6:.3f}, {e.y / 1e6:.3f}) reaches no pad")
    return problems


def write_json(path, data):
    """block.json: one part and one copper item per line, so a re-cut reads as a small diff."""
    head = {k: v for k, v in data.items() if k not in ("parts", "copper")}
    lines = ["{"] + [f"{json.dumps(k)}: {json.dumps(v)}," for k, v in head.items()]
    for key in ("parts", "copper"):
        rows = data[key]
        lines.append(f"{json.dumps(key)}: [")
        lines += [json.dumps(r) + ("," if n < len(rows) - 1 else "") for n, r in enumerate(rows)]
        lines.append("]," if key == "parts" else "]")
    open(path, "w").write("\n".join(lines) + "\n}\n")


def write_items(path, items):
    """routing.json's form: one item per line, sorted as route.py --freeze sorts them."""
    items = sorted(items, key=lambda i: (i["net"], "via" in i, json.dumps(i)))
    open(path, "w").write("[\n" + ",\n".join(json.dumps(i) for i in items) + "\n]\n")


def cut_cli(argv):
    """python3 -m edgecoil_pcb.blocks cut <gen.py> <variant> <name> <anchor> <ref,ref,...>
        [--routing in.json] [--locked in.json] [--rest out.json] [--rest-locked out.json]
        [--root blocks dir] [--solid REF:PAD,...] [--esd REF,...]

    Cut a block from a built, reviewed board: its parts from the board's generator (gen.py's Config,
    the variant's parts list), its copper from the frozen routing (default <variant>/routing.json) and
    the generator's locked power copper (default power.items() of Config.power_copper on the built
    board, or --locked). Writes <root>/<name>/block.json and, given --rest/--rest-locked, what is left
    to the board, in routing.json's form: cut the next block from those, and rebuild the board from
    the blocks plus them to prove the cut (canon)."""
    import argparse
    import importlib.util
    import pcbnew
    from . import power
    ap = argparse.ArgumentParser(prog="edgecoil_pcb.blocks cut")
    ap.add_argument("gen"); ap.add_argument("variant"); ap.add_argument("name"); ap.add_argument("anchor")
    ap.add_argument("refs")
    ap.add_argument("--routing"); ap.add_argument("--locked"); ap.add_argument("--rest"); ap.add_argument("--rest-locked")
    ap.add_argument("--root", default=BLOCKS); ap.add_argument("--solid", default=""); ap.add_argument("--esd", default="")
    ap.add_argument("--set", action="append", default=[], metavar="KEY=JSON",
                    help='another block.json key, e.g. local_libs=\'{"lp": "..."}\' or min_track_width=0.12')
    a = ap.parse_args(argv)
    spec = importlib.util.spec_from_file_location("board_gen", os.path.abspath(a.gen))
    gen = importlib.util.module_from_spec(spec)
    sys.path.insert(0, os.path.dirname(os.path.abspath(a.gen)))
    spec.loader.exec_module(gen)
    cfg = gen.CFG
    path = cfg.base(a.variant) + ".kicad_pcb"
    refs = set(a.refs.split(","))
    parts = {p.ref: p for p in cfg.variants[a.variant]()[0]}
    missing = sorted(refs - set(parts))
    if missing or a.anchor not in refs:
        raise SystemExit(f"cut: not on the board: {missing}; the anchor must be one of the refs")
    routing = json.load(open(a.routing or os.path.join(cfg.here, a.variant, "routing.json")))
    if a.locked:
        locked = json.load(open(a.locked))
    else:
        locked = power.items(pcbnew.LoadBoard(path), cfg.power_copper) if cfg.power_copper else []
    c = cut(path, routing, refs, a.anchor, locked)
    if c.split:
        print(f"{a.name}: {len(c.split)} track(s) the block needs only part of, left to the board whole:", file=sys.stderr)
        for i in c.split:
            print(f"  {i['net']} {i['layer']} {[v / 1e6 for v in i['start']]} {[v / 1e6 for v in i['end']]}", file=sys.stderr)
    ax, ay = parts[a.anchor].at
    rows = []
    for r in sorted(refs, key=lambda r: list(parts).index(r)):
        p = parts[r]
        row = {"ref": p.ref, "sym": p.sym, "fp": p.fp, "value": p.value, "pins": p.pins,
               "at": [round(p.at[0] - ax, 6), round(p.at[1] - ay, 6)], "rot": p.rot, "mpn": p.mpn, "lcsc": p.lcsc,
               "side": p.side}
        if p.note:
            row["note"] = p.note
        rows.append(row)
    copper = to_local(c.block, c.anchor)
    copper.sort(key=lambda i: (i["net"], "via" in i, json.dumps(i)))
    data = {"name": a.name, "anchor": a.anchor, "ports": c.ports, "internal": c.internal}
    if any(i.get("layer", "F.Cu") not in ("F.Cu", "B.Cu") for i in copper):
        data["copper_layers"] = 4
    if a.esd:
        data["esd_ground"] = a.esd.split(",")
    if a.solid:
        data["solid_pads"] = [s.split(":") for s in a.solid.split(",")]
    for kv in a.set:
        k, _, v = kv.partition("=")
        data[k] = json.loads(v)
    data["parts"], data["copper"] = rows, copper
    os.makedirs(os.path.join(a.root, a.name), exist_ok=True)
    write_json(os.path.join(a.root, a.name, "block.json"), data)
    if a.rest:
        write_items(a.rest, c.rest)
    if a.rest_locked:
        write_items(a.rest_locked, c.rest_locked)
    vias = sum(1 for i in copper if "via" in i)
    print(f"{a.name}: {len(rows)} parts, {len(copper)} copper items ({vias} vias; "
          f"{sum(1 for i in c.block if i in locked)} from locked copper); ports {c.ports}; internal {c.internal}")


if __name__ == "__main__":
    if len(sys.argv) >= 2 and sys.argv[1] == "cut":
        cut_cli(sys.argv[2:])
        sys.exit(0)
    # python3 -m edgecoil_pcb.blocks selftest <block dir> [lib nickname=dir ...]
    if len(sys.argv) >= 3 and sys.argv[1] == "selftest":
        d = os.path.abspath(sys.argv[2])
        libs = dict(a.split("=", 1) for a in sys.argv[3:])
        b = Block(json.load(open(os.path.join(d, "block.json"))), os.path.join(d, "block.json"))
        probs = selftest(b, {k: (os.path.relpath(v, d), "") for k, v in libs.items()})
        print("\n".join(probs) if probs else f"{b.name}: copper connected at 0/90/180/270")
        sys.exit(1 if probs else 0)
    sys.exit(__doc__)
