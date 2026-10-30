# SPDX-FileCopyrightText: 2026 edgecoil
# SPDX-License-Identifier: MIT
"""Canonical dump of a KiCad board: everything that reaches the fab, nothing that doesn't.

Two builds of the same board differ in thousands of lines of .kicad_pcb and gerber text (fresh
UUIDs, item order, timestamps), so a port is proven by comparing these dumps instead:

    python3 -m edgecoil_pcb.canon a.kicad_pcb b.kicad_pcb    exit 0 if identical, else a diff
    python3 -m edgecoil_pcb.canon a.kicad_pcb                print the dump

Coordinates are integer nanometres. Footprints are keyed by reference, copper and drawings are
sorted, zone fills are compared polygon by polygon.
"""
import difflib
import sys

import pcbnew


def _xy(p):
    return f"{p.x},{p.y}"


def _layers(lset):
    return "+".join(sorted(pcbnew.BOARD.GetStandardLayerName(l) for l in lset.Seq()))


def _shape(s, origin=""):
    t = s.GetShape()
    layer = s.GetLayerName()
    w = s.GetWidth()
    fill = int(s.IsFilled())
    if t == pcbnew.SHAPE_T_SEGMENT:
        a, b = sorted([_xy(s.GetStart()), _xy(s.GetEnd())])
        g = f"seg {a} {b}"
    elif t == pcbnew.SHAPE_T_RECTANGLE:
        g = f"rect {_xy(s.GetStart())} {_xy(s.GetEnd())}"
    elif t == pcbnew.SHAPE_T_CIRCLE:
        g = f"circle {_xy(s.GetCenter())} r{s.GetRadius()}"
    elif t == pcbnew.SHAPE_T_ARC:
        g = f"arc {_xy(s.GetStart())} {_xy(s.GetArcMid())} {_xy(s.GetEnd())}"
    elif t == pcbnew.SHAPE_T_POLY:
        poly = s.GetPolyShape()
        g = "poly " + " ".join(_xy(poly.CVertex(i)) for i in range(poly.TotalVertices()))
    else:
        g = f"shape{t} {_xy(s.GetStart())} {_xy(s.GetEnd())}"
    return f"{origin}draw {layer} w{w} f{fill} {g}"


def _text(t, origin=""):
    vis = int(t.IsVisible()) if hasattr(t, "IsVisible") else 1
    return (f"{origin}text {t.GetLayerName()} {t.GetText()!r} at {_xy(t.GetPosition())} "
            f"rot{t.GetTextAngleDegrees():g} size{t.GetTextWidth()}x{t.GetTextHeight()} "
            f"th{t.GetTextThickness()} mirror{int(t.IsMirrored())} vis{vis} "
            f"just{t.GetHorizJustify()},{t.GetVertJustify()}")


def _polyset(ps):
    out = []
    for i in range(ps.OutlineCount()):
        outline = ps.Outline(i)
        pts = [_xy(outline.CPoint(j)) for j in range(outline.PointCount())]
        holes = []
        for h in range(ps.HoleCount(i)):
            hole = ps.Hole(i, h)
            holes.append(" ".join(_xy(hole.CPoint(j)) for j in range(hole.PointCount())))
        out.append(" ".join(pts) + "".join(f" | {h}" for h in sorted(holes)))
    return sorted(out)


def _stackup(path):
    """The stackup block (mask and legend colours, finish), which the Python API doesn't reach."""
    text = open(path).read()
    i = text.find("(stackup")
    if i < 0:
        return ["stackup none"]
    depth, j = 0, i
    while True:
        depth += {"(": 1, ")": -1}.get(text[j], 0)
        j += 1
        if depth == 0:
            break
    return ["stackup " + " ".join(text[i:j].split())]


def dump(path):
    board = pcbnew.LoadBoard(path)
    lines = _stackup(path)
    ds = board.GetDesignSettings()
    lines.append(f"board layers{board.GetCopperLayerCount()} thickness{ds.GetBoardThickness()}")
    for name in ("m_TrackMinWidth", "m_ViasMinSize", "m_MinThroughDrill", "m_MinClearance",
                 "m_CopperEdgeClearance", "m_HoleClearance", "m_SolderMaskExpansion",
                 "m_SolderMaskMinWidth"):
        if hasattr(ds, name):
            lines.append(f"rule {name} {getattr(ds, name)}")

    for fp in sorted(board.GetFootprints(), key=lambda f: f.GetReference()):
        ref = fp.GetReference()
        o = f"fp {ref} "
        lines.append(f"{o}id {fp.GetFPIDAsString()} value {fp.GetValue()!r} side {fp.GetLayerName()} "
                     f"at {_xy(fp.GetPosition())} rot{fp.GetOrientationDegrees():g} attrs{fp.GetAttributes()}")
        for field in sorted(fp.GetFields(), key=lambda f: f.GetName()):
            if field.GetName() in ("Reference", "Value"):
                lines.append(_text(field, f"{o}field {field.GetName()} "))
            elif field.GetText():
                lines.append(f"{o}field {field.GetName()} {field.GetText()!r}")
        for pad in sorted(fp.Pads(), key=lambda p: (p.GetNumber(), p.GetPosition().x, p.GetPosition().y)):
            d = pad.GetDrillSize()
            lines.append(f"{o}pad {pad.GetNumber()} net {pad.GetNetname()!r} at {_xy(pad.GetPosition())} "
                         f"size{_xy(pad.GetSize(pcbnew.F_Cu))} shape{pad.GetShape(pcbnew.F_Cu)} "
                         f"rot{pad.GetOrientationDegrees():g} drill{_xy(d)} attr{pad.GetAttribute()} "
                         f"layers {_layers(pad.GetLayerSet())}")
        items = []
        for g in fp.GraphicalItems():
            if isinstance(g, pcbnew.PCB_SHAPE):
                items.append(_shape(g, o))
            elif isinstance(g, pcbnew.PCB_TEXT):
                items.append(_text(g, o))
        lines += sorted(items)
        for m in fp.Models():
            lines.append(f"{o}model {m.m_Filename} show{int(m.m_Show)}")

    copper = []
    for t in board.GetTracks():
        net = t.GetNetname()
        if isinstance(t, pcbnew.PCB_VIA):
            copper.append(f"via {_xy(t.GetPosition())} d{t.GetWidth(pcbnew.F_Cu)} drill{t.GetDrillValue()} "
                          f"net {net!r} {t.TopLayer()}-{t.BottomLayer()} type{t.GetViaType()}")
        elif isinstance(t, pcbnew.PCB_ARC):
            copper.append(f"arc {t.GetLayerName()} w{t.GetWidth()} {_xy(t.GetStart())} {_xy(t.GetMid())} "
                          f"{_xy(t.GetEnd())} net {net!r}")
        else:
            a, b = sorted([_xy(t.GetStart()), _xy(t.GetEnd())])
            copper.append(f"track {t.GetLayerName()} w{t.GetWidth()} {a} {b} net {net!r}")
    lines += sorted(copper)

    drawings = []
    for d in board.GetDrawings():
        if isinstance(d, pcbnew.PCB_SHAPE):
            drawings.append(_shape(d))
        elif isinstance(d, pcbnew.PCB_TEXT):
            drawings.append(_text(d))
        else:
            drawings.append(f"other {d.GetClass()} {d.GetLayerName()} {_xy(d.GetPosition())}")
    lines += sorted(drawings)

    zones = []
    for z in board.Zones():
        head = (f"zone net {z.GetNetname()!r} layers {_layers(z.GetLayerSet())} prio{z.GetAssignedPriority()} "
                f"clear{z.GetLocalClearance()} minw{z.GetMinThickness()} pad{z.GetPadConnection()} "
                f"keepout{int(z.GetIsRuleArea())}")
        if z.GetIsRuleArea():
            head += (f" no:tracks{int(z.GetDoNotAllowTracks())} vias{int(z.GetDoNotAllowVias())} "
                     f"pads{int(z.GetDoNotAllowPads())} fp{int(z.GetDoNotAllowFootprints())} "
                     f"pour{int(z.GetDoNotAllowCopperPour())}")
        block = [head] + [f"  outline {p}" for p in _polyset(z.Outline())]
        for layer in z.GetLayerSet().Seq():
            if z.HasFilledPolysForLayer(layer):
                for p in _polyset(z.GetFilledPolysList(layer)):
                    block.append(f"  fill {pcbnew.BOARD.GetStandardLayerName(layer)} {p}")
        zones.append("\n".join(block))
    lines += sorted(zones)
    return lines


def main(argv):
    if len(argv) == 1:
        print("\n".join(dump(argv[0])))
        return 0
    if len(argv) != 2:
        raise SystemExit(__doc__)
    a, b = dump(argv[0]), dump(argv[1])
    if a == b:
        print(f"identical: {len(a)} canonical lines")
        return 0
    sys.stdout.writelines(l + "\n" for l in difflib.unified_diff(a, b, argv[0], argv[1], n=0, lineterm=""))
    return 1


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
