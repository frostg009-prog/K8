# KiCad python: apply routes.json to placed board, add outer GND pours, fill zones, save routed board
import sys, json, pcbnew
src, routes, out = sys.argv[1:4]
b = pcbnew.LoadBoard(src)
R = json.load(open(routes))
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
for n, x, y in R['vias']:
    v = pcbnew.PCB_VIA(b); v.SetPosition(pcbnew.VECTOR2I(FM(x), FM(y)))
    v.SetWidth(FM(0.45)); v.SetDrill(FM(0.2)); v.SetNet(b.FindNet(n)); b.Add(v)
# outer-layer GND pours (lowest priority) for return paths and shielding
bb = b.GetBoardEdgesBoundingBox()
W, L = pcbnew.ToMM(bb.GetWidth()), pcbnew.ToMM(bb.GetHeight())
for layer in (pcbnew.F_Cu, pcbnew.B_Cu):
    z = pcbnew.ZONE(b); z.SetLayer(layer); z.SetNet(b.FindNet('GND')); z.SetAssignedPriority(0)
    z.SetLocalClearance(FM(0.2)); z.SetMinThickness(FM(0.2)); z.SetPadConnection(pcbnew.ZONE_CONNECTION_THERMAL)
    z.SetThermalReliefGap(FM(0.25)); z.SetThermalReliefSpokeWidth(FM(0.3))
    z.SetIslandRemovalMode(pcbnew.ISLAND_REMOVAL_MODE_ALWAYS)
    ol = z.Outline(); ol.NewOutline()
    for x, y in [(0.3, 0.3), (W - 0.3, 0.3), (W - 0.3, L - 0.3), (0.3, L - 0.3)]:
        ol.Append(FM(x), FM(y))
    b.Add(z)
for z in b.Zones():
    if z.GetLayer() in (pcbnew.In1_Cu, pcbnew.In2_Cu):
        z.SetIslandRemovalMode(pcbnew.ISLAND_REMOVAL_MODE_ALWAYS)
pcbnew.ZONE_FILLER(b).Fill(b.Zones())
b.Save(out)
print('applied', len(R['tracks']), 'tracks', len(R['vias']), 'vias ->', out)
