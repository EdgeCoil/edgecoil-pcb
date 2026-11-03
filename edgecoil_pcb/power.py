# SPDX-FileCopyrightText: 2026 edgecoil
# SPDX-License-Identifier: MIT
"""Locked power copper a board declares, instead of laying it in a hook.

The router thins power paths into small pads and has no idea of Kelvin sensing, so a board lays
those itself, locked: wide runs, vias with their own size and drill, sense tracks, ground vias at
the return, escapes out of a fine-pitch part. A board's Config names them as data:

    CFG = Config(..., power_copper=power.PowerCopper(
        runs=[("VBUS", "B.Cu", [(13.45, 47.54), (20.6, 40.4), (35.4, 40.4)], 1.2), ...],
        vias=[("VBUS", (35.4, 40.4), 0.8, 0.4), ...],
        sense=[("VPO", (59.8, 44.5), (60.6, 42.0))],
        gnd_vias=[(51.8, 32.6), ...],
        escapes=[("U4", "F.Cu", 0.2, [("VBUS", (-0.225, -0.80), (-0.225, -2.00)), ...])],
        via_drills=[("VBUS", (13.45, 47.54), 0.4)]))

Coordinates in mm, as the board's parts are placed. Each run is a polyline, one locked segment per
pair of points; route.py --freeze leaves locked copper out of routing.json, so it stays here.
Escapes are offsets from a part's centre at its own orientation, starting on that part's pad of the
same net. `via_drills` re-drills a via the toolkit has already laid (the USB-C VBUS joins), found at
that point. `items(board)` gives the copper in routing.json's form, which is what
`blocks.cut` takes alongside the frozen routing.
"""
from dataclasses import dataclass, field


@dataclass
class PowerCopper:
    runs: list = field(default_factory=list)        # (net, layer, [(x, y), ...], width)
    vias: list = field(default_factory=list)        # (net, (x, y), diameter, drill)
    sense: list = field(default_factory=list)       # (net, (x, y), (x, y)): Kelvin taps, no current
    sense_width: float = 0.25
    sense_layer: str = "F.Cu"
    gnd_vias: list = field(default_factory=list)    # (x, y): ground vias where the current returns
    gnd_via: tuple = (0.6, 0.3)                     # their diameter and drill
    escapes: list = field(default_factory=list)     # (ref, layer, width, [(net, (dx, dy), (dx, dy)), ...])
    via_drills: list = field(default_factory=list)  # (net, (x, y), drill): a via already laid, re-drilled

    def __bool__(self):
        return any((self.runs, self.vias, self.sense, self.gnd_vias, self.escapes, self.via_drills))


def _nm(v):
    import pcbnew
    return pcbnew.FromMM(v)


def _track(net, layer, a, b, w):
    return {"net": net, "layer": layer, "start": [_nm(a[0]), _nm(a[1])], "end": [_nm(b[0]), _nm(b[1])], "w": _nm(w)}


def _via(net, at, d, drill):
    return {"net": net, "via": [_nm(at[0]), _nm(at[1])], "d": _nm(d), "drill": _nm(drill)}


def items(board, pc):
    """The declared copper as routing.json items (nm), in the order it is laid. Escapes need the
    board for their part's position, and are checked to start on that part's pad of their net."""
    import pcbnew
    from .blocks import _rot
    out = []
    for ref, layer, w, legs in pc.escapes:
        fp = board.FindFootprintByReference(ref)
        if fp is None:
            raise SystemExit(f"power copper: escape from {ref}, which the board doesn't have")
        if fp.GetLayer() != pcbnew.F_Cu:
            raise SystemExit(f"power copper: escape offsets are for a front-side part; {ref} is on the back")
        rot = fp.GetOrientationDegrees() % 360
        if rot % 90:
            raise SystemExit(f"power copper: {ref} at {rot} degrees; escapes need a multiple of 90")
        x0, y0 = (pcbnew.ToMM(v) for v in fp.GetPosition())
        for net, a, b in legs:
            a, b = _rot(*a, rot), _rot(*b, rot)
            t = _track(net, layer, (x0 + a[0], y0 + a[1]), (x0 + b[0], y0 + b[1]), w)
            start = pcbnew.VECTOR2I(*t["start"])
            if not any(p.GetNetname() == net and p.HitTest(start) for p in fp.Pads()):
                raise SystemExit(f"power copper: {ref} {net} escape does not start on its {ref} pad")
            out.append(t)
    for net, layer, pts, w in pc.runs:
        out += [_track(net, layer, a, b, w) for a, b in zip(pts, pts[1:])]
    out += [_via(net, at, d, drill) for net, at, d, drill in pc.vias]
    out += [_track(net, pc.sense_layer, a, b, pc.sense_width) for net, a, b in pc.sense]
    out += [_via("GND", at, *pc.gnd_via) for at in pc.gnd_vias]
    return out


def lay(board, pc):
    """Re-drill the named vias, then lay the declared copper, locked. Returns the items laid, for the
    check that none changed net on save (blocks.renetted)."""
    import pcbnew
    from .blocks import lay as lay_items
    tol = 5000
    for net, at, drill in pc.via_drills:
        x, y = _nm(at[0]), _nm(at[1])
        found = [t for t in board.GetTracks() if t.GetClass() == "PCB_VIA" and t.GetNetname() == net
                 and abs(t.GetPosition().x - x) < tol and abs(t.GetPosition().y - y) < tol]
        if len(found) != 1:
            raise SystemExit(f"power copper: {len(found)} {net} vias at {at} to re-drill (want 1)")
        found[0].SetDrill(_nm(drill))
    laid = items(board, pc)
    lay_items(board, laid)
    return laid
