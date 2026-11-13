# KiCad python: GND pads inside outer-layer pour islands without a via -> (GND, pad, nearest GND via) pairs for finish_astar.py
#   python3 island_pairs.py board.kicad_pcb pairs.json
import sys, json, math, pcbnew
b = pcbnew.LoadBoard(sys.argv[1]); TM = pcbnew.ToMM
vias = [t.GetPosition() for t in b.GetTracks() if t.GetClass() == 'PCB_VIA' and t.GetNetname() == 'GND']
vias += [p.GetPosition() for f in b.GetFootprints() for p in f.Pads() if p.GetNetname() == 'GND' and p.GetAttribute() == pcbnew.PAD_ATTRIB_PTH]
pads = [p for f in b.GetFootprints() for p in f.Pads() if p.GetNetname() == 'GND' and p.GetAttribute() != pcbnew.PAD_ATTRIB_PTH]
out = []
for z in b.Zones():
    if z.GetNetname() != 'GND' or z.GetLayer() not in (pcbnew.F_Cu, pcbnew.B_Cu): continue
    l = z.GetLayer(); ps = z.GetFilledPolysList(l)
    for i in range(ps.OutlineCount()):
        sub = pcbnew.SHAPE_POLY_SET(); sub.AddOutline(ps.COutline(i))
        if any(sub.Contains(v) for v in vias): continue
        for p in pads:
            if p.IsOnLayer(l) and sub.Contains(p.GetPosition()):
                x, y = TM(p.GetPosition().x), TM(p.GetPosition().y)
                vx, vy = min(((TM(v.x), TM(v.y)) for v in vias), key=lambda q: math.hypot(q[0] - x, q[1] - y))
                out.append(['GND', [x, y], [vx, vy]])
json.dump(out, open(sys.argv[2], 'w'))
print('island pads', len(out))
