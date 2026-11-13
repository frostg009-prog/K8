# -*- coding: utf-8 -*-
"""rev0.4 (KiCad python): small hand corrections after autorouting.  python3 manual.py in out
REMOVE: (net, x1, y1, x2, y2) track segments to rip up;  ADD: (net, layer, [(x, y), ...], width)."""
import sys, pcbnew
src, out = sys.argv[1:3]
FM, TM = pcbnew.FromMM, pcbnew.ToMM
b = pcbnew.LoadBoard(src)
REMOVE = [
    ('HB_ILIM', 18.13, 117.82, 17.55, 117.82), ('HB_ILIM', 17.39, 117.08, 17.11, 116.81), ('HB_ILIM', 17.39, 117.66, 17.39, 117.08),
    ('HB_ILIM', 17.55, 117.82, 17.39, 117.66), ('HB_ILIM', 17.11, 116.81, 16.05, 116.81),
    ('LED_RUN_N', 10.14, 42.98, 9.66, 42.50),
]
ADD = [
    ('VSCAP', 'B', [(18.13, 117.33), (16.9, 117.33)], 0.2),    # U_HB pin 9 straight to R19
    ('LED_RUN_N', 'B', [(10.14, 42.98), (9.66, 42.98), (9.66, 42.50)], 0.15),   # square corner: clear of JP_MATEK pad
]
VIAS = []
n = 0
for t in list(b.GetTracks()):
    if t.GetClass() != 'PCB_TRACK':
        continue
    a, c = t.GetStart(), t.GetEnd()
    for net, x1, y1, x2, y2 in REMOVE:
        if t.GetNetname() == net and ((abs(TM(a.x) - x1) < .02 and abs(TM(a.y) - y1) < .02 and abs(TM(c.x) - x2) < .02 and abs(TM(c.y) - y2) < .02) or
                                      (abs(TM(a.x) - x2) < .02 and abs(TM(a.y) - y2) < .02 and abs(TM(c.x) - x1) < .02 and abs(TM(c.y) - y1) < .02)):
            b.Remove(t); n += 1; break
for net, lay, pts, w in ADD:
    for p, q in zip(pts, pts[1:]):
        t = pcbnew.PCB_TRACK(b); t.SetStart(pcbnew.VECTOR2I(FM(p[0]), FM(p[1]))); t.SetEnd(pcbnew.VECTOR2I(FM(q[0]), FM(q[1])))
        t.SetWidth(FM(w)); t.SetLayer(pcbnew.F_Cu if lay == 'F' else pcbnew.B_Cu); t.SetNet(b.FindNet(net)); b.Add(t)
for net, x, y in VIAS:
    v = pcbnew.PCB_VIA(b); v.SetPosition(pcbnew.VECTOR2I(FM(x), FM(y))); v.SetWidth(pcbnew.F_Cu, FM(0.45)); v.SetDrill(FM(0.2)); v.SetNet(b.FindNet(net)); b.Add(v)
pcbnew.ZONE_FILLER(b).Fill(b.Zones())
b.Save(out)
print('removed', n, 'added', len(ADD))
