# KiCad python: dump pads / zones / holes / net classes of a placed board to JSON for router.py
import sys, json, pcbnew
b = pcbnew.LoadBoard(sys.argv[1])
TM = pcbnew.ToMM
pads = []
for fp in b.GetFootprints():
    for p in fp.Pads():
        bb = p.GetBoundingBox()
        att = p.GetAttribute()
        if att == pcbnew.PAD_ATTRIB_NPTH:
            layers = ['HOLE']
        elif att == pcbnew.PAD_ATTRIB_PTH:
            layers = ['F', 'B']
        else:
            layers = ['F'] if p.IsOnLayer(pcbnew.F_Cu) else ['B']
        sz = p.GetSize()
        pads.append(dict(ref=fp.GetReference(), num=p.GetNumber(), net=p.GetNetname(), layers=layers,
                         x=TM(p.GetPosition().x), y=TM(p.GetPosition().y),
                         bb=[TM(bb.GetX()), TM(bb.GetY()), TM(bb.GetRight()), TM(bb.GetBottom())],
                         drill=TM(p.GetDrillSizeX()), round=p.GetShape() == pcbnew.PAD_SHAPE_CIRCLE,
                         w=TM(min(sz.x, sz.y))))
zones = []
for z in b.Zones():
    o = z.Outline().Outline(0)
    zones.append(dict(net=z.GetNetname(), layer=b.GetLayerName(z.GetLayer()), prio=z.GetAssignedPriority(),
                      pts=[(TM(o.CPoint(i).x), TM(o.CPoint(i).y)) for i in range(o.PointCount())]))
ns = b.GetDesignSettings().m_NetSettings
cls = {}
for n in set(p['net'] for p in pads if p['net']):
    nc = ns.GetEffectiveNetClass(n)
    cls[n] = dict(cls=nc.GetName(), w=TM(nc.GetTrackWidth()), clr=TM(nc.GetClearance()))
bb = b.GetBoardEdgesBoundingBox()
json.dump(dict(W=TM(bb.GetWidth()), L=TM(bb.GetHeight()), pads=pads, zones=zones, cls=cls), open(sys.argv[2], 'w'))
print(len(pads), 'pads', len(zones), 'zones', len(cls), 'nets')
