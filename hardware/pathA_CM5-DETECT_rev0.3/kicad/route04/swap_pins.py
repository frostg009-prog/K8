# -*- coding: utf-8 -*-
"""rev0.4 (KiCad python): swap the nets of two pads of one footprint on a routed board and rip the stubs on both pads.
   python3 swap_pins.py in.kicad_pcb out.kicad_pcb REF PAD_A PAD_B"""
import sys, pcbnew
src, out, ref, pa, pb = sys.argv[1:6]
TM = pcbnew.ToMM
b = pcbnew.LoadBoard(src)
fp = b.FindFootprintByReference(ref)
A = [p for p in fp.Pads() if p.GetNumber() == pa][0]; Bp = [p for p in fp.Pads() if p.GetNumber() == pb][0]
na, nb = A.GetNet(), Bp.GetNet()
kill = [t for t in b.GetTracks() if t.GetClass() == 'PCB_TRACK' and (
    (t.GetNetCode() == na.GetNetCode() and (A.HitTest(t.GetStart()) or A.HitTest(t.GetEnd()))) or
    (t.GetNetCode() == nb.GetNetCode() and (Bp.HitTest(t.GetStart()) or Bp.HitTest(t.GetEnd()))))]
for t in kill:
    b.Remove(t)
A.SetNet(nb); Bp.SetNet(na)
pcbnew.ZONE_FILLER(b).Fill(b.Zones())
b.Save(out)
print('swapped', ref, pa, '<->', pb, 'ripped', len(kill))
