# -*- coding: utf-8 -*-
"""rev0.4 (KiCad python): move a footprint to the nearest collision-free spot around a target, ripping its old stubs.
   python3 move_fp.py in.kicad_pcb out.kicad_pcb REF X Y"""
import sys, math, pcbnew
src, out, ref, tx, ty = sys.argv[1], sys.argv[2], sys.argv[3], float(sys.argv[4]), float(sys.argv[5])
FM, TM = pcbnew.FromMM, pcbnew.ToMM
b = pcbnew.LoadBoard(src)
fp = b.FindFootprintByReference(ref)
lay = pcbnew.B_Cu if fp.IsFlipped() else pcbnew.F_Cu
orig = (fp.GetPosition(), fp.GetOrientationDegrees())
EB = b.GetBoardEdgesBoundingBox()
padnets = {p.GetNetCode() for p in fp.Pads()}
kill = []
for t in b.GetTracks():
    if t.GetNetCode() in padnets and t.GetClass() == 'PCB_TRACK' and (TM(t.GetLength()) < 2.5 or t.GetNetname() not in ('GND', '+5V_CM5')):
        if any(p.HitTest(t.GetStart()) or p.HitTest(t.GetEnd()) for p in fp.Pads()):
            kill.append(t)
for t in kill:
    b.Remove(t)
shapes = []
for f in b.GetFootprints():
    if f.GetReference() == ref: continue
    for p in f.Pads():
        if p.IsOnLayer(lay): shapes.append(p.GetEffectiveShape(lay))
for t in b.GetTracks():
    if t.IsOnLayer(lay): shapes.append(t.GetEffectiveShape(lay))
done = None
for r in [k * 0.2 for k in range(0, 40)]:
    for k in range(1 if r == 0 else 24):
        a = 2 * math.pi * k / 24
        for rot in (0, 90):
            fp.SetOrientationDegrees(rot); fp.SetPosition(pcbnew.VECTOR2I(FM(tx + r * math.cos(a)), FM(ty + r * math.sin(a))))
            fb = fp.GetBoundingBox(False)
            if TM(fb.GetX()) < 0.6 or TM(fb.GetY()) < 0.6 or TM(fb.GetRight()) > TM(EB.GetRight()) - 0.6 or TM(fb.GetBottom()) > TM(EB.GetBottom()) - 0.6:
                continue
            if any(f.GetReference() != ref and f.IsFlipped() == fp.IsFlipped() and f.GetBoundingBox(False).Intersects(fb) for f in b.GetFootprints()):
                continue
            if all(not s.Collide(p.GetEffectiveShape(lay), FM(0.3)) for p in fp.Pads() for s in shapes):
                done = (TM(fp.GetPosition().x), TM(fp.GetPosition().y), rot); break
        if done: break
    if done: break
if not done:
    fp.SetPosition(orig[0]); fp.SetOrientationDegrees(orig[1])
pcbnew.ZONE_FILLER(b).Fill(b.Zones())
b.Save(out)
print('ripped', len(kill), 'moved', ref, done)
