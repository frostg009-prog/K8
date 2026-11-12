# -*- coding: utf-8 -*-
"""rev0.4 step 2b (KiCad python): BGA-style fan-out of the CM5 GPIO connector (pins 1..100).
   python3 fanout_cm5.py in.kicad_pcb out.kicad_pcb
Every connected pad gets a 0.1 mm stub on F.Cu and a 0.4/0.2 mm via, placed in three staggered columns:
outer row -> west of the connector, inner row -> east. Stubs and vias are locked (the autorouter keeps them),
so every GPIO / SD / power / GND pin is reachable from the bottom layer and the inner planes.
Geometry (pin pitch 0.4 mm per row): via-to-stub gap 0.4 - 0.2 - 0.05 = 0.15 mm (>= PLANE class clearance),
via-to-via 0.72 mm centre distance (copper gap 0.32 mm, hole gap 0.52 mm)."""
import sys, math
import pcbnew
FM, TM = pcbnew.FromMM, pcbnew.ToMM
src, out = sys.argv[1:3]
b = pcbnew.LoadBoard(src)
m1 = [f for f in b.GetFootprints() if f.GetReference() == 'M1'][0]
pads = [p for p in m1.Pads() if p.GetNumber().isdigit() and 1 <= int(p.GetNumber()) <= 100 and p.GetNetname()]
xs = sorted(set(round(TM(p.GetPosition().x), 2) for p in pads))
x_out, x_in = xs[0], xs[-1]
COLS_OUT = [x_out - 0.91, x_out - 1.51, x_out - 2.11]
COLS_IN = [x_in + 0.91, x_in + 1.51, x_in + 2.11]
SW, VD, VDR = 0.1, 0.4, 0.2
n = 0
for row_x, cols in ((x_out, COLS_OUT), (x_in, COLS_IN)):
    row = sorted([p for p in pads if abs(TM(p.GetPosition().x) - row_x) < 0.05], key=lambda p: TM(p.GetPosition().y))
    for k, p in enumerate(row):
        x, y = TM(p.GetPosition().x), TM(p.GetPosition().y)
        vx = cols[k % 3]
        t = pcbnew.PCB_TRACK(b); t.SetStart(pcbnew.VECTOR2I(FM(x), FM(y))); t.SetEnd(pcbnew.VECTOR2I(FM(vx), FM(y)))
        t.SetWidth(FM(SW)); t.SetLayer(pcbnew.F_Cu); t.SetNet(p.GetNet()); t.SetLocked(True); b.Add(t)
        v = pcbnew.PCB_VIA(b); v.SetPosition(pcbnew.VECTOR2I(FM(vx), FM(y))); v.SetWidth(pcbnew.F_Cu, FM(VD)); v.SetDrill(FM(VDR))
        v.SetNet(p.GetNet()); v.SetLocked(True); b.Add(v)
        n += 1
b.Save(out)
print('CM5 fan-out:', n, 'pins, rows at x', x_out, x_in)
