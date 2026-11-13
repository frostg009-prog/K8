# -*- coding: utf-8 -*-
"""rev0.4 (KiCad python): remove dangling vias / track stubs reported by DRC, then refill zones.
   python3 cleanup.py in.kicad_pcb drc.json out.kicad_pcb"""
import sys, json, pcbnew
src, drcj, out = sys.argv[1:4]
b = pcbnew.LoadBoard(src); TM = pcbnew.ToMM
d = json.load(open(drcj))
pts = {'via_dangling': [], 'track_dangling': []}
for v in d['violations']:
    if v['type'] in pts:
        pts[v['type']].append((v['items'][0]['pos']['x'], v['items'][0]['pos']['y']))
n = 0
near = lambda p, x, y: abs(TM(p.x) - x) < 0.02 and abs(TM(p.y) - y) < 0.02
for t in list(b.GetTracks()):
    if t.GetClass() == 'PCB_VIA':
        if any(near(t.GetPosition(), x, y) for x, y in pts['via_dangling']):
            b.Remove(t); n += 1
    else:
        if any(near(t.GetStart(), x, y) or near(t.GetEnd(), x, y) for x, y in pts['track_dangling']) and TM(t.GetLength()) < 5.0:
            b.Remove(t); n += 1
pcbnew.ZONE_FILLER(b).Fill(b.Zones())
b.Save(out)
print('removed', n)
