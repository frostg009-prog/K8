# -*- coding: utf-8 -*-
"""rev0.4 step 6 (KiCad python): power-path hardening after routing.
   python3 power.py in.kicad_pcb out.kicad_pcb
1. every segment of a power net is widened to the largest width from its ladder that keeps clearance (collision-checked
   against all other-net copper on the same layer, incl. pads, tracks, vias, board edge margin 0.3 mm);
2. power nets that own an In2 plane island get stitching vias (0.6/0.3) wherever their copper sits over the island
   and there is room, so the plane carries the current instead of the thin tracks;
3. zones refilled. Prints a width report per net."""
import sys, math, collections
import pcbnew
src, out = sys.argv[1:3]
FM, TM = pcbnew.FromMM, pcbnew.ToMM
b = pcbnew.LoadBoard(src)
bb = b.GetBoardEdgesBoundingBox(); W, L = TM(bb.GetWidth()), TM(bb.GetHeight())
LADDER = {
    '+5V_CM5': [1.5, 1.2, 1.0, 0.8, 0.6, 0.5, 0.4, 0.3, 0.25, 0.2], '+5V_AUX': [1.5, 1.2, 1.0, 0.8, 0.6, 0.5, 0.4],
    'VIN_PROT': [1.5, 1.2, 1.0, 0.8, 0.6, 0.5, 0.4], 'VSERVO': [1.5, 1.2, 1.0, 0.8, 0.6, 0.5],
    'VIN_B1': [1.2, 1.0], 'VBAT_RAW': [1.5, 1.2, 1.0], 'VBAT_F': [1.5, 1.2, 1.0],
    '+5V_AI': [1.0, 0.8, 0.6, 0.5], 'VBUS1': [0.8, 0.6, 0.5], 'VBUS2': [0.8, 0.6, 0.5], 'VBUS3': [0.8, 0.6, 0.5],
    '+3V3_CAM': [0.6, 0.5], '+3V3_CM5': [0.6, 0.5, 0.4, 0.3, 0.25, 0.2], '+3V3_AON': [0.5], 'MATEK_5V': [0.6, 0.5], 'SD_VDD': [0.5],
    'GND': [0.8, 0.6, 0.5, 0.4, 0.3, 0.25, 0.2],
}
CLR = {'default': 0.15}
items = [t for t in b.GetTracks()] + [p for f in b.GetFootprints() for p in f.Pads()]
holes = [p for f in b.GetFootprints() for p in f.Pads() if p.GetAttribute() == pcbnew.PAD_ATTRIB_NPTH]
LAY = (pcbnew.F_Cu, pcbnew.B_Cu)


def seg_ok(t, w):
    a, c = t.GetStart(), t.GetEnd()
    lay = t.GetLayer()
    sh = pcbnew.SHAPE_SEGMENT(a, c, FM(w))
    x0, y0, x1, y1 = min(TM(a.x), TM(c.x)) - w / 2, min(TM(a.y), TM(c.y)) - w / 2, max(TM(a.x), TM(c.x)) + w / 2, max(TM(a.y), TM(c.y)) + w / 2
    if x0 < 0.3 or y0 < 0.3 or x1 > W - 0.3 or y1 > L - 0.3:
        return False
    nc = t.GetNetCode()
    for it in items:
        if it.GetNetCode() == nc or not it.IsOnLayer(lay):
            continue
        if it.GetEffectiveShape(lay).Collide(sh, FM(CLR['default'])):
            return False
    for h in holes:
        r = TM(h.GetDrillSizeX()) / 2 + (1.7 if h.GetParentFootprint().GetReference() == 'M1' else 0.25)
        if sh.Collide(pcbnew.SHAPE_CIRCLE(h.GetPosition(), FM(r)), 0):
            return False
    return True


rep = collections.defaultdict(collections.Counter)
for t in b.GetTracks():
    if t.GetClass() != 'PCB_TRACK' or (t.IsLocked() and t.GetNetname() not in ('+5V_CM5', 'GND', '+3V3_CM5')) or t.GetLayer() not in LAY:
        continue
    lad = LADDER.get(t.GetNetname())
    if not lad:
        continue
    w0 = TM(t.GetWidth())
    for w in lad:
        if w <= w0 + 1e-3:
            break
        if seg_ok(t, w):
            t.SetWidth(FM(w)); break
    rep[t.GetNetname()][round(TM(t.GetWidth()), 2)] += TM(t.GetLength())

# ---- stitching vias from power copper into its In2 island
islands = [z for z in b.Zones() if z.GetLayer() == pcbnew.In2_Cu and z.GetNetname() not in ('GND',)]
pcbnew.ZONE_FILLER(b).Fill(b.Zones())
VD, VR = 0.6, 0.3
vias = [t for t in b.GetTracks() if t.GetClass() == 'PCB_VIA']


def via_ok(x, y, nc):
    c = pcbnew.SHAPE_CIRCLE(pcbnew.VECTOR2I(FM(x), FM(y)), FM(VD / 2))
    for it in items:
        if it.GetNetCode() == nc:
            continue
        for l in LAY:
            if it.IsOnLayer(l) and it.GetEffectiveShape(l).Collide(c, FM(0.15)):
                return False
    for v in vias:
        if math.hypot(TM(v.GetPosition().x) - x, TM(v.GetPosition().y) - y) < VR / 2 + TM(v.GetDrillValue()) / 2 + 0.3:
            return False
    for h in holes:
        if math.hypot(TM(h.GetPosition().x) - x, TM(h.GetPosition().y) - y) < TM(h.GetDrillSizeX()) / 2 + VD / 2 + 0.3 + (1.7 if h.GetParentFootprint().GetReference() == 'M1' else 0):
            return False
    return 0.8 < x < W - 0.8 and 0.8 < y < L - 0.8


added = collections.Counter()
for z in islands:
    net = z.GetNet(); nc = net.GetNetCode()
    fill = z.GetFilledPolysList(pcbnew.In2_Cu)
    cand = []
    for t in b.GetTracks():
        if t.GetNetCode() != nc or t.GetClass() != 'PCB_TRACK':
            continue
        a, c = t.GetStart(), t.GetEnd(); n = max(1, int(TM(t.GetLength()) / 1.5))
        for k in range(n + 1):
            cand.append((TM(a.x) + (TM(c.x) - TM(a.x)) * k / n, TM(a.y) + (TM(c.y) - TM(a.y)) * k / n))
    for f in b.GetFootprints():
        for p in f.Pads():
            if p.GetNetCode() == nc and p.GetAttribute() == pcbnew.PAD_ATTRIB_SMD:
                cand.append((TM(p.GetPosition().x), TM(p.GetPosition().y)))
    for x, y in cand:
        if not fill.Contains(pcbnew.VECTOR2I(FM(x), FM(y))):
            continue
        if any(math.hypot(TM(v.GetPosition().x) - x, TM(v.GetPosition().y) - y) < 2.0 for v in vias if v.GetNetCode() == nc):
            continue                                   # one via per ~2 mm of copper is enough
        if not via_ok(x, y, nc):
            continue
        v = pcbnew.PCB_VIA(b); v.SetPosition(pcbnew.VECTOR2I(FM(x), FM(y))); v.SetWidth(pcbnew.F_Cu, FM(VD)); v.SetDrill(FM(VR)); v.SetNet(net)
        b.Add(v); vias.append(v); items.append(v); added[net.GetNetname()] += 1
pcbnew.ZONE_FILLER(b).Fill(b.Zones())
b.Save(out)
for n in sorted(rep):
    print('%-10s %s' % (n, {k: round(v, 1) for k, v in sorted(rep[n].items())}))
print('plane stitching vias', dict(added))
