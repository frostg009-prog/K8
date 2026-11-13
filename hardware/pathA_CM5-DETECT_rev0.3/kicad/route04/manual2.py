# -*- coding: utf-8 -*-
"""rev0.4 (KiCad python): clean V5_SENSE escape under U_MCU so pin 5 (VBAT_SENSE) gets a via site.  python3 manual2.py in out"""
import sys, pcbnew
src, out = sys.argv[1:3]
FM, TM = pcbnew.FromMM, pcbnew.ToMM
b = pcbnew.LoadBoard(src)
kill = []
for t in b.GetTracks():
    if t.GetClass() == 'PCB_TRACK' and t.GetNetname() == 'V5_SENSE' and t.GetLayer() == pcbnew.B_Cu:
        a, c = t.GetStart(), t.GetEnd()
        if all(28.5 <= TM(p.x) <= 31.0 and 40.6 <= TM(p.y) <= 42.4 for p in (a, c)):
            kill.append(t)
for t in kill:
    b.Remove(t)
net = b.FindNet('V5_SENSE')
pts = [(27.94, 40.67), (29.35, 40.67), (29.75, 41.07), (30.93, 42.25), (30.93, 42.27)]
for p, q in zip(pts, pts[1:]):
    t = pcbnew.PCB_TRACK(b); t.SetStart(pcbnew.VECTOR2I(FM(p[0]), FM(p[1]))); t.SetEnd(pcbnew.VECTOR2I(FM(q[0]), FM(q[1])))
    t.SetWidth(FM(0.15)); t.SetLayer(pcbnew.B_Cu); t.SetNet(net); b.Add(t)
pcbnew.ZONE_FILLER(b).Fill(b.Zones())
b.Save(out)
print('V5_SENSE: ripped', len(kill), 'segments, rerouted')
