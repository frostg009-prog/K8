# -*- coding: utf-8 -*-
"""rev0.4 (KiCad python): last isolated GND pads. Geometry checked on zoomed renders of both layers.  python3 manual3.py in out
 - U_AON pin 2: B stub east + GND via in the free pocket (F pour above)
 - R27 pin 2: C33_FB loop around the pad replaced by a straight run U_C33.5 -> R27.1 (pad gets free to the pour)
 - J_CAM1 pin 4 / U_SEC pin 4: see via_in_pad.py"""
import sys, pcbnew
src, out = sys.argv[1:3]
FM, TM = pcbnew.FromMM, pcbnew.ToMM
b = pcbnew.LoadBoard(src)
RIP = [('C33_FB', (26.86, 14.46, 27.41, 15.01)), ('C33_FB', (27.41, 15.01, 28.16, 15.01)), ('C33_FB', (28.16, 15.01, 28.38, 14.80)),
       ('C33_FB', (28.38, 14.80, 28.38, 14.04)), ('C33_FB', (28.38, 14.04, 27.83, 13.49))]
RIPNET = []
ADD = [('GND', 'B', [(19.70, 46.50), (20.65, 46.50)], 0.3),
       ('C33_FB', 'B', [(26.14, 13.55), (27.83, 13.49)], 0.15)]
VIAS = [('GND', 20.65, 46.50)]
kill = []
for t in b.GetTracks():
    if t.GetNetname() in RIPNET:
        kill.append(t); continue
    if t.GetClass() != 'PCB_TRACK': continue
    a, c = t.GetStart(), t.GetEnd()
    e = [(TM(a.x), TM(a.y)), (TM(c.x), TM(c.y))]
    for net, (x1, y1, x2, y2) in RIP:
        if t.GetNetname() == net and any(abs(p[0] - x1) < .02 and abs(p[1] - y1) < .02 and abs(q[0] - x2) < .02 and abs(q[1] - y2) < .02 for p, q in (e, e[::-1])):
            kill.append(t); break
for t in kill: b.Remove(t)
for net, lay, pts, w in ADD:
    for p, q in zip(pts, pts[1:]):
        t = pcbnew.PCB_TRACK(b); t.SetStart(pcbnew.VECTOR2I(FM(p[0]), FM(p[1]))); t.SetEnd(pcbnew.VECTOR2I(FM(q[0]), FM(q[1])))
        t.SetWidth(FM(w)); t.SetLayer(pcbnew.F_Cu if lay == 'F' else pcbnew.B_Cu); t.SetNet(b.FindNet(net)); b.Add(t)
for net, x, y in VIAS:
    v = pcbnew.PCB_VIA(b); v.SetPosition(pcbnew.VECTOR2I(FM(x), FM(y))); v.SetWidth(pcbnew.F_Cu, FM(0.4)); v.SetDrill(FM(0.2)); v.SetNet(b.FindNet(net)); b.Add(v)
pcbnew.ZONE_FILLER(b).Fill(b.Zones())
b.Save(out)
print('ripped', len(kill))
