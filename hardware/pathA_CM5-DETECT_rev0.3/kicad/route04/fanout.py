# -*- coding: utf-8 -*-
"""rev0.4 (KiCad python): signal fan-out - short stub + via for unconnected pads of footprints REFS (default M1).
   python3 fanout.py in.kicad_pcb drc.json out.kicad_pcb
(derived from gnd_fix.py)
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
CLR = float(os.environ.get('CLR', 0.15))   # clearance used for checks (>= 0.125 board rule, >= 0.15 power classes)
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


REFS = set(os.environ.get('REFS', 'M1').split(','))
fan, fail = 0, []
for u in d['unconnected_items']:
    for it in u['items']:
        desc = it['description']
        if 'Pad' not in desc or '[GND]' in desc:
            continue
        ref = desc.split(' of ')[-1].split(' ')[0]
        if ref not in REFS:
            continue
        pos = (it['pos']['x'], it['pos']['y'])
        p = None
        for fp in b.GetFootprints():
            if fp.GetReference() != ref: continue
            for q in fp.Pads():
                if abs(TM(q.GetPosition().x) - pos[0]) < 0.02 and abs(TM(q.GetPosition().y) - pos[1]) < 0.02:
                    p = q
        if p is None or p.GetAttribute() == pcbnew.PAD_ATTRIB_PTH:
            continue
        NET = p.GetNet(); nc = NET.GetNetCode()
        layer = pcbnew.F_Cu if p.IsOnLayer(pcbnew.F_Cu) else pcbnew.B_Cu
        px, py = pos
        sx, sy = TM(p.GetBoundingBox().GetWidth()) / 2, TM(p.GetBoundingBox().GetHeight()) / 2
        axis = (1, 0) if sx > sy else (0, 1)
        done = False
        w = 0.12
        for L1 in [0.35 + 0.1 * k for k in range(0, 40)]:
            for sgn in (1, -1):
                ex = px + sgn * axis[0] * (sx + L1); ey = py + sgn * axis[1] * (sy + L1)
                for off in (0.0, 0.3, -0.3, 0.6, -0.6):
                    vx, vy = ex + axis[1] * off, ey + axis[0] * off
                    def okv():
                        c = lambda: pcbnew.SHAPE_CIRCLE(pcbnew.VECTOR2I(FM(vx), FM(vy)), FM(VD / 2))
                        for it2 in items:
                            if it2.GetNetCode() == nc: continue
                            for l in LAYERS:
                                if it2.IsOnLayer(l) and it2.GetEffectiveShape(l).Collide(c(), FM(CLR)): return False
                        for h in npth:
                            hx, hy = TM(h.GetPosition().x), TM(h.GetPosition().y)
                            if math.hypot(hx - vx, hy - vy) < TM(h.GetDrillSizeX()) / 2 + VD / 2 + 0.25 + (1.7 if h.GetParentFootprint().GetReference() == 'M1' else 0): return False
                        for it2 in items:
                            if isinstance(it2, pcbnew.PCB_VIA):
                                if math.hypot(TM(it2.GetPosition().x) - vx, TM(it2.GetPosition().y) - vy) < VR + 0.3: return False
                        return 0.7 < vx < W - 0.7 and 0.7 < vy < L - 0.7
                    def oks(a, c_):
                        sh = lambda: pcbnew.SHAPE_SEGMENT(pcbnew.VECTOR2I(FM(a[0]), FM(a[1])), pcbnew.VECTOR2I(FM(c_[0]), FM(c_[1])), FM(w))
                        for it2 in items:
                            if it2.GetNetCode() == nc: continue
                            if it2.IsOnLayer(layer) and it2.GetEffectiveShape(layer).Collide(sh(), FM(CLR)): return False
                        return True
                    mid = (ex, ey)
                    if okv() and oks((px, py), mid) and oks(mid, (vx, vy)):
                        for a, c_ in (((px, py), mid), (mid, (vx, vy))):
                            if math.hypot(a[0] - c_[0], a[1] - c_[1]) < 1e-3: continue
                            t = pcbnew.PCB_TRACK(b); t.SetStart(pcbnew.VECTOR2I(FM(a[0]), FM(a[1]))); t.SetEnd(pcbnew.VECTOR2I(FM(c_[0]), FM(c_[1])))
                            t.SetWidth(FM(w)); t.SetLayer(layer); t.SetNet(NET); b.Add(t); items.append(t)
                        v = pcbnew.PCB_VIA(b); v.SetPosition(pcbnew.VECTOR2I(FM(vx), FM(vy))); v.SetWidth(pcbnew.F_Cu, FM(VD)); v.SetDrill(FM(VR)); v.SetNet(NET); b.Add(v); items.append(v)
                        fan += 1; done = True; break
                if done: break
            if done: break
        if not done:
            fail.append('%s.%s' % (ref, p.GetNumber()))
pcbnew.ZONE_FILLER(b).Fill(b.Zones())
b.Save(out)
print('fan-out', fan, 'failed', fail)
