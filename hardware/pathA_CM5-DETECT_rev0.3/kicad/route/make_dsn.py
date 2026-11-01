import sys, re
s = open(sys.argv[1]).read(); L = float(sys.argv[2]); W = 44.0
for l in ('In1.Cu', 'In2.Cu'):
    s = s.replace('(layer %s\n      (type signal)' % l, '(layer %s\n      (type power)' % l)
m = re.search(r'\(path pcb 0  [^)]*\)', s)
f = lambda v: int(round(v * 1000))
s = s.replace(m.group(0), '(path pcb 0  %d %d  %d %d  %d %d  %d %d  %d %d)' % (f(W - .15), -f(L - .15), 150, -f(L - .15), 150, -150, f(W - .15), -150, f(W - .15), -f(L - .15)))
ko = ''.join('    (keepout "" (circle signal 6100 %d %d))\n' % (x, -y) for x, y in [(5500, 64000), (38500, 64000), (5500, 16000), (38500, 16000)])
i = s.index('    (via "Via[0-3]'); s = s[:i] + ko + s[i:]
open(sys.argv[3], 'w').write(s)
