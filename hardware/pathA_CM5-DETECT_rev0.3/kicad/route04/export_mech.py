# KiCad python: export mechanical data (holes, edge connectors, buttons, LEDs) for the enclosure generator
import sys, json, pcbnew
b = pcbnew.LoadBoard(sys.argv[1]); TM = pcbnew.ToMM
_bb = b.GetBoardEdgesBoundingBox()
out = {'board': [round(TM(_bb.GetWidth()), 3), round(TM(_bb.GetHeight()), 3), 1.5], 'holes': [], 'parts': []}
for fp in b.GetFootprints():
    r = fp.GetReference()
    if r.startswith('H') and r[1:].isdigit():
        out['holes'].append([TM(fp.GetPosition().x), TM(fp.GetPosition().y)])
        continue
    if r == 'M1':
        for p in fp.Pads():
            if p.GetAttribute() == pcbnew.PAD_ATTRIB_NPTH:
                out['holes'].append([TM(p.GetPosition().x), TM(p.GetPosition().y), 'cm5'])
    if r.startswith(('J_', 'SW_', 'D_PWR', 'D_RUN', 'D_ERR', 'M1', 'SC', 'C_BULK', 'L_', 'D_')):
        bb = fp.GetBoundingBox(False)
        out['parts'].append(dict(ref=r, side='B' if fp.IsFlipped() else 'F', x=TM(fp.GetPosition().x), y=TM(fp.GetPosition().y),
                                 bb=[TM(bb.GetX()), TM(bb.GetY()), TM(bb.GetRight()), TM(bb.GetBottom())]))
json.dump(out, open(sys.argv[2], 'w'), indent=1)
print(len(out['holes']), 'holes', len(out['parts']), 'parts')
