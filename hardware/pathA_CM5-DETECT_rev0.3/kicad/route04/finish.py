# -*- coding: utf-8 -*-
"""rev0.4 step 4 (KiCad python): import the Freerouting session, add copper pours, fill zones.
   python3 finish.py pairs.kicad_pcb board.ses out.kicad_pcb"""
import sys, pcbnew
src, ses, out = sys.argv[1:4]
FM = pcbnew.FromMM
b = pcbnew.LoadBoard(src)
_bb = b.GetBoardEdgesBoundingBox(); W, L = pcbnew.ToMM(_bb.GetWidth()), pcbnew.ToMM(_bb.GetHeight())
locked = {(t.GetNetname(), t.GetStart().x, t.GetStart().y, t.GetEnd().x, t.GetEnd().y) for t in b.GetTracks() if t.IsLocked()}
print('SES import', pcbnew.ImportSpecctraSES(b, ses))
# duplicate-safe: the session re-emits the fixed pair wires; remove exact duplicates
seen = set(); dup = 0
for t in list(b.GetTracks()):
    k = (t.GetClass(), t.GetNetname(), t.GetLayer(), t.GetStart().x, t.GetStart().y, t.GetEnd().x if t.GetClass() != 'PCB_VIA' else 0, t.GetEnd().y if t.GetClass() != 'PCB_VIA' else 0)
    if k in seen:
        b.Remove(t); dup += 1
    else:
        seen.add(k)
print('duplicates removed', dup)
for layer in (pcbnew.F_Cu, pcbnew.B_Cu):           # outer GND pours, stitched to the inner GND planes
    z = pcbnew.ZONE(b); z.SetLayer(layer); z.SetNet(b.FindNet('GND')); z.SetAssignedPriority(0)
    z.SetLocalClearance(FM(0.2)); z.SetMinThickness(FM(0.2)); z.SetPadConnection(pcbnew.ZONE_CONNECTION_THERMAL)
    z.SetThermalReliefGap(FM(0.25)); z.SetThermalReliefSpokeWidth(FM(0.3))
    z.SetIslandRemovalMode(pcbnew.ISLAND_REMOVAL_MODE_ALWAYS)
    ol = z.Outline(); ol.NewOutline()
    for x, y in [(0.3, 0.3), (W - 0.3, 0.3), (W - 0.3, L - 0.3), (0.3, L - 0.3)]:
        ol.Append(FM(x), FM(y))
    b.Add(z)
pcbnew.ZONE_FILLER(b).Fill(b.Zones())
b.Save(out)
print('saved', out, 'tracks', len(b.GetTracks()))
