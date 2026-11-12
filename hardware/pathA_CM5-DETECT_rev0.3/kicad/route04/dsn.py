# -*- coding: utf-8 -*-
"""rev0.4 step 3 (KiCad python): export a Specctra DSN for Freerouting.
   python3 dsn.py board.kicad_pcb board.dsn
Inner layers are declared as power planes; every NPTH hole gets a keep-out (CM5 stand-off holes: bare ring dia 6.1)."""
import sys, re, pcbnew
src, out = sys.argv[1:3]
b = pcbnew.LoadBoard(src)
TM = pcbnew.ToMM
bb = b.GetBoardEdgesBoundingBox(); W, L = TM(bb.GetWidth()), TM(bb.GetHeight())
tmp = out + '.raw'
assert pcbnew.ExportSpecctraDSN(b, tmp)
s = open(tmp).read()
for l in ('In1.Cu', 'In2.Cu'):
    s = s.replace('(layer %s\n      (type signal)' % l, '(layer %s\n      (type power)' % l)
f = lambda v: int(round(v * 1000))
m = re.search(r'\(path pcb 0  [^)]*\)', s)
E = 0.25
s = s.replace(m.group(0), '(path pcb 0  %d %d  %d %d  %d %d  %d %d  %d %d)' % (f(W - E), -f(L - E), f(E), -f(L - E), f(E), -f(E), f(W - E), -f(E), f(W - E), -f(L - E)))
ko = ''
for fp in b.GetFootprints():
    for p in fp.Pads():
        if p.GetAttribute() == pcbnew.PAD_ATTRIB_NPTH:
            x, y = TM(p.GetPosition().x), TM(p.GetPosition().y)
            d = TM(p.GetDrillSizeX())
            r = d / 2 + (1.75 if fp.GetReference() == 'M1' else 0.3)
            ko += '    (keepout "" (circle signal %d %d %d))\n' % (f(2 * r), f(x), -f(y))
i = s.index('    (via "Via[0-3]'); s = s[:i] + ko + s[i:]
open(out, 'w').write(s)
print('dsn', out, 'protected wires', s.count('(type protect)'), 'wires', s.count('(wire'))
