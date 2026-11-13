# -*- coding: utf-8 -*-
"""rev0.4 (KiCad python): GND via-in-pad for pads that have no other way to the GND planes.
   python3 via_in_pad.py in out REF.PAD:x:y [...]     (x, y = via position inside the pad, mm)
Fab note: these vias are filled and capped (Rezonit: 'заполнение переходных отверстий')."""
import sys, pcbnew
src, out = sys.argv[1:3]
FM = pcbnew.FromMM
b = pcbnew.LoadBoard(src)
for spec in sys.argv[3:]:
    rp, x, y = spec.split(':')
    ref, num = rp.split('.')
    pad = [p for p in b.FindFootprintByReference(ref).Pads() if p.GetNumber() == num][0]
    v = pcbnew.PCB_VIA(b); v.SetPosition(pcbnew.VECTOR2I(FM(float(x)), FM(float(y)))); v.SetWidth(pcbnew.F_Cu, FM(0.4)); v.SetDrill(FM(0.2))
    v.SetNet(pad.GetNet()); b.Add(v)
    print('via-in-pad', rp, x, y, pad.GetNetname())
pcbnew.ZONE_FILLER(b).Fill(b.Zones())
b.Save(out)
