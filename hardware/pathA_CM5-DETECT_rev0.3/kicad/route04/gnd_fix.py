# -*- coding: utf-8 -*-
"""rev0.4 step 5 (KiCad python): GND fan-out vias + stitching vias.
   python3 gnd_fix.py in.kicad_pcb drc.json out.kicad_pcb
1. every GND pad that DRC reports as unconnected / starved gets a via to the inner GND planes (short stub, collision-checked);
2. stitching vias on a 2.5 mm grid wherever both outer GND pours have copper (ties the outer pours to In1/In2 GND);
3. outer GND pours switched to solid pad connection (no starved thermals on fine-pitch pads); zones refilled."""
import sys, json, math
import pcbnew
src, drcj, out = sys.argv[1:4]
FM, TM = pcbnew.FromMM, pcbnew.ToMM
b = pcbnew.LoadBoard(src)
GND = b.FindNet('GND')
import os
VD, VR = float(os.environ.get('VD', 0.45)), 0.2           # via
CLR = float(os.environ.get('CLR', 0.16))   # clearance used for checks (>= 0.125 board rule, >= 0.15 power classes)
d = json.load(open(drcj))
targets = set()
for v in d['violations']:
    if v['type'] == 'starved_thermal':
        for i in v['items']:
            if 'Pad' in i['description']:
                targets.add((round(i['pos']['x'], 3), round(i['pos']['y'], 3)))
for u in d['unconnected_items']:
    for i in u['items']:
        if 'Pad' in i['description'] and '[GND]' in i['description']:
            targets.add((round(i['pos']['x'], 3), round(i['pos']['y'], 3)))

items = []                    # (item, layers) non-GND copper
for t in b.GetTracks():
    items.append(t)
for fp in b.GetFootprints():
    for p in fp.Pads():
        items.append(p)
npth = [p for fp in b.GetFootprints() for p in fp.Pads() if p.GetAttribute() == pcbnew.PAD_ATTRIB_NPTH]
LAYERS = (pcbnew.F_Cu, pcbnew.B_Cu)
bb = b.GetBoardEdgesBoundingBox(); W, L = TM(bb.GetWidth()), TM(bb.GetHeight())


def clear(shape_fn, layers, net_ok=GND.GetNetCode(), extra=0.0):
    for it in items:
        if it.GetNetCode() == net_ok and it.GetNetCode() != 0:
            continue
        for l in layers:
            if not it.IsOnLayer(l):
                continue
            if it.GetEffectiveShape(l).Collide(shape_fn(), FM(CLR + extra)):
                return False
    return True


def via_ok(x, y):
    if x < 0.7 or y < 0.7 or x > W - 0.7 or y > L - 0.7:
        return False
    c = lambda: pcbnew.SHAPE_CIRCLE(pcbnew.VECTOR2I(FM(x), FM(y)), FM(VD / 2))
    for h in npth:
        hx, hy = TM(h.GetPosition().x), TM(h.GetPosition().y)
        if math.hypot(hx - x, hy - y) < TM(h.GetDrillSizeX()) / 2 + VD / 2 + 0.25 + (1.7 if h.GetParentFootprint().GetReference() == 'M1' else 0):
            return False
    if not clear(c, LAYERS):
        return False
    # hole-to-hole with other vias / PTH
    for it in items:
        if isinstance(it, pcbnew.PCB_VIA) or (isinstance(it, pcbnew.PAD) and it.GetAttribute() == pcbnew.PAD_ATTRIB_PTH):
            px, py = TM(it.GetPosition().x), TM(it.GetPosition().y)
            dr = TM(it.GetDrillValue() if isinstance(it, pcbnew.PCB_VIA) else it.GetDrillSizeX())
            if math.hypot(px - x, py - y) < dr / 2 + VR / 2 + 0.3:
                return False
    return True


def seg_ok(layer, a, c, w):
    s = lambda: pcbnew.SHAPE_SEGMENT(pcbnew.VECTOR2I(FM(a[0]), FM(a[1])), pcbnew.VECTOR2I(FM(c[0]), FM(c[1])), FM(w))
    return clear(s, (layer,))


def add_via(x, y):
    v = pcbnew.PCB_VIA(b); v.SetPosition(pcbnew.VECTOR2I(FM(x), FM(y))); v.SetWidth(pcbnew.F_Cu, FM(VD)); v.SetDrill(FM(VR)); v.SetNet(GND); b.Add(v)
    items.append(v)


def add_seg(layer, a, c, w):
    t = pcbnew.PCB_TRACK(b); t.SetStart(pcbnew.VECTOR2I(FM(a[0]), FM(a[1]))); t.SetEnd(pcbnew.VECTOR2I(FM(c[0]), FM(c[1])))
    t.SetWidth(FM(w)); t.SetLayer(layer); t.SetNet(GND); b.Add(t); items.append(t)


pads = {}
for fp in b.GetFootprints():
    for p in fp.Pads():
        if p.GetNetCode() == GND.GetNetCode():
            pads[(round(TM(p.GetPosition().x), 3), round(TM(p.GetPosition().y), 3))] = p
fan, fail = 0, []
for pos in sorted(targets):
    p = pads.get(pos)
    if p is None:
        best = min(pads, key=lambda k: math.hypot(k[0] - pos[0], k[1] - pos[1]))
        if math.hypot(best[0] - pos[0], best[1] - pos[1]) > 0.05:
            continue
        p = pads[best]
    if p.GetAttribute() == pcbnew.PAD_ATTRIB_PTH:
        continue                     # PTH pads already reach the inner GND planes
    layer = pcbnew.F_Cu if p.IsOnLayer(pcbnew.F_Cu) else pcbnew.B_Cu
    px, py = pos
    sx, sy = TM(p.GetBoundingBox().GetWidth()) / 2, TM(p.GetBoundingBox().GetHeight()) / 2
    done = False
    w = min(0.3, max(0.12, min(sx, sy) * 2 * 0.75))
    for r in [0.0] + [0.15 * k for k in range(2, 20)]:
        for k in range(32 if r else 1):
            a = 2 * math.pi * k / 32
            # start from the pad edge in direction a
            ex, ey = px + math.cos(a) * (sx if abs(math.cos(a)) > 0.01 else 0), py + math.sin(a) * (sy if abs(math.sin(a)) > 0.01 else 0)
            vx, vy = ex + math.cos(a) * (r + VD / 2), ey + math.sin(a) * (r + VD / 2)
            if r == 0.0:
                continue
            if not via_ok(vx, vy):
                continue
            if seg_ok(layer, (px, py), (vx, vy), w):
                add_seg(layer, (px, py), (vx, vy), w); add_via(vx, vy); fan += 1; done = True
                break
            # dog-leg: leave along the long pad axis, then turn to the via
            axis = (1, 0) if sx > sy else (0, 1)
            for sgn in (1, -1):
                mx, my = px + sgn * axis[0] * (sx + 0.35), py + sgn * axis[1] * (sy + 0.35)
                if seg_ok(layer, (px, py), (mx, my), w) and seg_ok(layer, (mx, my), (vx, vy), w):
                    add_seg(layer, (px, py), (mx, my), w); add_seg(layer, (mx, my), (vx, vy), w); add_via(vx, vy); fan += 1; done = True
                    break
            if done:
                break
        if done:
            break
    if not done:
        fail.append('%s.%s (%.2f,%.2f)' % (p.GetParentFootprint().GetReference(), p.GetNumber(), px, py))
# outer pours: solid connection
for z in b.Zones():
    if z.GetNetname() == 'GND' and z.GetLayer() in LAYERS:
        z.SetPadConnection(pcbnew.ZONE_CONNECTION_FULL)
pcbnew.ZONE_FILLER(b).Fill(b.Zones())
# stitching: grid points where both outer GND fills cover the whole via
zf = [z for z in b.Zones() if z.GetNetname() == 'GND' and z.GetLayer() in LAYERS]


def in_fill(x, y):
    for l in LAYERS:
        z = [q for q in zf if q.GetLayer() == l][0]
        poly = z.GetFilledPolysList(l)
        for a in range(0, 360, 45):
            px, py = x + math.cos(math.radians(a)) * (VD / 2 + 0.05), y + math.sin(math.radians(a)) * (VD / 2 + 0.05)
            if not poly.Contains(pcbnew.VECTOR2I(FM(px), FM(py))):
                return False
    return True


st = 0
G = 2.5
yy = 1.5
while yy < L - 1.0:
    xx = 1.5
    while xx < W - 1.0:
        if in_fill(xx, yy) and via_ok(xx, yy):
            add_via(xx, yy); st += 1
        xx += G
    yy += G
pcbnew.ZONE_FILLER(b).Fill(b.Zones())
b.Save(out)
print('targets', len(targets), 'fan-out vias', fan, 'stitching vias', st)
for f in fail:
    print('  no fan-out:', f)
