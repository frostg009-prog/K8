# KiCad python: apply routes.json to placed board, add outer GND pours, fill zones, save routed board
import sys, json, pcbnew
src, routes, out = sys.argv[1:4]
b = pcbnew.LoadBoard(src)
R = json.load(open(routes)) if routes.endswith('.json') else {'tracks': [], 'vias': []}
if routes.endswith('.ses'):
    print('SES import', pcbnew.ImportSpecctraSES(b, routes))
FM = pcbnew.FromMM
nets = {n.GetNetname(): n for n in b.GetNetInfo().NetsByName().values()} if hasattr(b.GetNetInfo(), 'NetsByName') else {}
if not nets:
    for i in range(b.GetNetCount()):
        ni = b.FindNet(i)
        if ni: nets[ni.GetNetname()] = ni
for n, l, a, c, w in R['tracks']:
    t = pcbnew.PCB_TRACK(b)
    t.SetStart(pcbnew.VECTOR2I(FM(a[0]), FM(a[1]))); t.SetEnd(pcbnew.VECTOR2I(FM(c[0]), FM(c[1])))
    t.SetWidth(FM(w)); t.SetLayer(pcbnew.F_Cu if l == 'F' else pcbnew.B_Cu); t.SetNet(b.FindNet(n)); b.Add(t)
seen = set()
for n, x, y in R['vias']:
    k = (n, round(x, 2), round(y, 2))
    if k in seen: continue
    seen.add(k)
    v = pcbnew.PCB_VIA(b); v.SetPosition(pcbnew.VECTOR2I(FM(x), FM(y)))
    v.SetWidth(FM(0.45)); v.SetDrill(FM(0.2)); v.SetNet(b.FindNet(n)); b.Add(v)
# outer-layer GND pours (lowest priority) for return paths and shielding
bb = b.GetBoardEdgesBoundingBox()
W, L = pcbnew.ToMM(bb.GetWidth()), pcbnew.ToMM(bb.GetHeight())
for layer in (pcbnew.F_Cu, pcbnew.B_Cu):
    z = pcbnew.ZONE(b); z.SetLayer(layer); z.SetNet(b.FindNet('GND')); z.SetAssignedPriority(0)
    z.SetLocalClearance(FM(0.2)); z.SetMinThickness(FM(0.2)); z.SetPadConnection(pcbnew.ZONE_CONNECTION_FULL)
    z.SetThermalReliefGap(FM(0.25)); z.SetThermalReliefSpokeWidth(FM(0.3))
    z.SetIslandRemovalMode(pcbnew.ISLAND_REMOVAL_MODE_ALWAYS)
    ol = z.Outline(); ol.NewOutline()
    for x, y in [(0.3, 0.3), (W - 0.3, 0.3), (W - 0.3, L - 0.3), (0.3, L - 0.3)]:
        ol.Append(FM(x), FM(y))
    b.Add(z)
# power copper pours: SW nodes and high-current nets get solid copper islands on their pad layer
POUR = ['B1_SW', 'B2_SW', 'HB_SW', 'VIN_B1', 'VIN_PROT', '+5V_CM5', '+5V_AUX', 'VBAT_RAW', 'VBAT_F', 'VSCAP']
def hull(pts):
    pts = sorted(set(pts))
    if len(pts) < 3: return pts
    def cr(o, a, b): return (a[0]-o[0])*(b[1]-o[1]) - (a[1]-o[1])*(b[0]-o[0])
    lo, up = [], []
    for p in pts:
        while len(lo) >= 2 and cr(lo[-2], lo[-1], p) <= 0: lo.pop()
        lo.append(p)
    for p in reversed(pts):
        while len(up) >= 2 and cr(up[-2], up[-1], p) <= 0: up.pop()
        up.append(p)
    return lo[:-1] + up[:-1]
TM = pcbnew.ToMM
for netname in POUR:
    for layer in (pcbnew.F_Cu, pcbnew.B_Cu):
        pads = [p for fp in b.GetFootprints() for p in fp.Pads() if p.GetNetname() == netname and p.IsOnLayer(layer) and p.GetAttribute() != pcbnew.PAD_ATTRIB_PTH]
        clusters = []
        for p in pads:
            c = (TM(p.GetPosition().x), TM(p.GetPosition().y))
            for cl in clusters:
                if any(abs(c[0]-q[0]) < 9 and abs(c[1]-q[1]) < 9 for q, _ in cl): cl.append((c, p)); break
            else: clusters.append([(c, p)])
        for cl in clusters:
            if len(cl) < 2: continue
            pts = []
            for _, p in cl:
                bb = p.GetBoundingBox(); m = 0.5
                pts += [(TM(bb.GetX())-m, TM(bb.GetY())-m), (TM(bb.GetRight())+m, TM(bb.GetY())-m), (TM(bb.GetRight())+m, TM(bb.GetBottom())+m), (TM(bb.GetX())-m, TM(bb.GetBottom())+m)]
            h = hull(pts)
            z = pcbnew.ZONE(b); z.SetLayer(layer); z.SetNet(b.FindNet(netname)); z.SetAssignedPriority(3)
            z.SetLocalClearance(FM(0.2)); z.SetMinThickness(FM(0.25)); z.SetPadConnection(pcbnew.ZONE_CONNECTION_FULL)
            z.SetIslandRemovalMode(pcbnew.ISLAND_REMOVAL_MODE_ALWAYS)
            ol = z.Outline(); ol.NewOutline()
            for x, y in h: ol.Append(FM(x), FM(y))
            b.Add(z)
for z in b.Zones():
    if z.GetLayer() in (pcbnew.In1_Cu, pcbnew.In2_Cu):
        z.SetIslandRemovalMode(pcbnew.ISLAND_REMOVAL_MODE_ALWAYS)
pcbnew.ZONE_FILLER(b).Fill(b.Zones())
b.Save(out)
print('applied', len(R['tracks']), 'tracks', len(R['vias']), 'vias ->', out)
