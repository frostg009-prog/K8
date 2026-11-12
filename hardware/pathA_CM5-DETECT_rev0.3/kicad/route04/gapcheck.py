# measures the edge-to-edge gap along every diff pair (sampled each 0.1 mm), reports min/max and length off-nominal
import sys, math, pcbnew, collections
b = pcbnew.LoadBoard(sys.argv[1]); TM = pcbnew.ToMM
seg = collections.defaultdict(list)
for t in b.GetTracks():
    if t.GetClass() == 'PCB_TRACK' and t.IsLocked() and t.GetNetname()[-2:] in ('_P', '_N', 'DP', 'DN'):
        seg[t.GetNetname()].append((t.GetLayer(), TM(t.GetStart().x), TM(t.GetStart().y), TM(t.GetEnd().x), TM(t.GetEnd().y), TM(t.GetWidth())))
def mate(n):
    return n[:-1] + ('N' if n.endswith('P') else 'P')
def dps(px, py, s):
    _, x1, y1, x2, y2, w = s; dx, dy = x2 - x1, y2 - y1; L2 = dx * dx + dy * dy
    t = 0 if L2 == 0 else max(0, min(1, ((px - x1) * dx + (py - y1) * dy) / L2))
    return math.hypot(px - x1 - t * dx, py - y1 - t * dy)
for n in sorted(seg):
    if not n.endswith('P'): continue
    m = mate(n)
    hist = collections.Counter(); tot = 0
    for s in seg[n]:
        L = math.hypot(s[3] - s[1], s[4] - s[2]); k = max(1, int(L / 0.1))
        for i in range(k):
            px, py = s[1] + (s[3] - s[1]) * (i + .5) / k, s[2] + (s[4] - s[2]) * (i + .5) / k
            g = min(dps(px, py, q) - q[5] / 2 for q in seg[m] if q[0] == s[0]) - s[5] / 2
            hist[round(g, 2)] += L / k; tot += L / k
    nom = max(hist, key=hist.get)
    off = sum(v for g, v in hist.items() if abs(g - nom) > 0.011)
    print('%-12s nominal gap %.2f mm on %5.1f mm; off-nominal %4.1f mm (%s)' % (n[:-2], nom, hist[nom], off, ', '.join('%.2f:%.1f' % (g, v) for g, v in sorted(hist.items()) if abs(g - nom) > 0.011)))
