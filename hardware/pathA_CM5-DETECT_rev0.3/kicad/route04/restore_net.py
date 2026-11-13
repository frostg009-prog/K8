# -*- coding: utf-8 -*-
"""rev0.4 (KiCad python): copy all tracks/vias of the given nets from a donor board (same placement) into a board.
   python3 restore_net.py donor.kicad_pcb in.kicad_pcb out.kicad_pcb NET [NET...]"""
import sys, pcbnew
donor, src, out = sys.argv[1:4]
nets = set(sys.argv[4:])
d = pcbnew.LoadBoard(donor); b = pcbnew.LoadBoard(src)
for t in list(b.GetTracks()):
    if t.GetNetname() in nets: b.Remove(t)
n = 0
for t in d.GetTracks():
    if t.GetNetname() not in nets: continue
    c = t.Duplicate(); c.SetNet(b.FindNet(t.GetNetname())); b.Add(c); n += 1
pcbnew.ZONE_FILLER(b).Fill(b.Zones())
b.Save(out)
print('copied', n, 'items of', sorted(nets))
