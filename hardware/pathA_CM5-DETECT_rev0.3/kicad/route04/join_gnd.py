# -*- coding: utf-8 -*-
"""rev0.4 (KiCad python): join GND pads that sit in isolated pour islands to the nearest GND via/pad/track
with a short straight or L-shaped track (collision-checked).  python3 join_gnd.py in.kicad_pcb islands.json out.kicad_pcb"""
import sys, json, math, pcbnew
src, ij, out = sys.argv[1:4]
FM, TM = pcbnew.FromMM, pcbnew.ToMM
b = pcbnew.LoadBoard(src)
GND = b.FindNet('GND'); gc = GND.GetNetCode()
items = list(b.GetTracks()) + [p for f in b.GetFootprints() for p in f.Pads()]
CLR = 0.13
def free(lay, a, c, w):
    sh = pcbnew.SHAPE_SEGMENT(pcbnew.VECTOR2I(FM(a[0]), FM(a[1])), pcbnew.VECTOR2I(FM(c[0]), FM(c[1])), FM(w))
    return not any(it.GetNetCode() != gc and it.IsOnLayer(lay) and it.GetEffectiveShape(lay).Collide(sh, FM(CLR)) for it in items)
targets = [(v['items'][0]['pos']['x'], v['items'][0]['pos']['y']) for v in json.load(open(ij))['violations']]
done, fail = 0, []
for x, y in targets:
    pad = None
    for f in b.GetFootprints():
        for p in f.Pads():
            if p.GetNetCode() == gc and abs(TM(p.GetPosition().x) - x) < .02 and abs(TM(p.GetPosition().y) - y) < .02:
                pad = p
    if pad is None: continue
    lay = pcbnew.F_Cu if pad.IsOnLayer(pcbnew.F_Cu) else pcbnew.B_Cu
    cands = []
    for it in items:
        if it.GetNetCode() != gc or it is pad: continue
        if isinstance(it, pcbnew.PCB_VIA) or (isinstance(it, pcbnew.PAD) and (it.GetAttribute() == pcbnew.PAD_ATTRIB_PTH)):
            px, py = TM(it.GetPosition().x), TM(it.GetPosition().y)
            cands.append((math.hypot(px - x, py - y), px, py))
    cands.sort()
    ok = False
    for d, px, py in cands[:25]:
        if d > 6: break
        for w in (0.3, 0.2, 0.15):
            for mid in [None, (px, y), (x, py)]:
                path = [(x, y), (px, py)] if mid is None else [(x, y), mid, (px, py)]
                if all(free(lay, a, c, w) for a, c in zip(path, path[1:])):
                    for a, c in zip(path, path[1:]):
                        t = pcbnew.PCB_TRACK(b); t.SetStart(pcbnew.VECTOR2I(FM(a[0]), FM(a[1]))); t.SetEnd(pcbnew.VECTOR2I(FM(c[0]), FM(c[1])))
                        t.SetWidth(FM(w)); t.SetLayer(lay); t.SetNet(GND); b.Add(t); items.append(t)
                    ok = True; break
            if ok: break
        if ok: break
    if ok: done += 1
    else: fail.append('%s.%s' % (pad.GetParentFootprint().GetReference(), pad.GetNumber()))
pcbnew.ZONE_FILLER(b).Fill(b.Zones())
b.Save(out)
print('joined', done, 'failed', fail)
