# -*- coding: utf-8 -*-
"""Finisher v2. KiCad python: /usr/bin/python3 finish2.py in.kicad_pcb drc.json out.kicad_pcb
Routes the links that KiCad DRC reports as unconnected (non-GND) on a fine 0.05 mm grid and adds GND stitching vias."""
import sys, os, re, json, math, ctypes, shutil, collections
import numpy as np
import pcbnew
from PIL import Image, ImageDraw
from scipy import ndimage

HERE = os.path.dirname(os.path.abspath(__file__))
src, drcj, out = sys.argv[1:4]
TM = pcbnew.ToMM
FM = lambda v: pcbnew.FromMM(float(v))
B = pcbnew.LoadBoard(src)
bb = B.GetBoardEdgesBoundingBox()
W, L = TM(bb.GetWidth()), TM(bb.GetHeight())
G = 0.05
NX, NY = int(round(W / G)), int(round(L / G))
lib = ctypes.CDLL(HERE + '/libastar.so')
P8 = np.ctypeslib.ndpointer(np.uint8, flags='C_CONTIGUOUS')
lib.astar3.argtypes = [ctypes.c_int, ctypes.c_int, ctypes.c_int, P8, P8, P8, P8, P8, ctypes.c_int, np.ctypeslib.ndpointer(np.int32), ctypes.c_int]
lib.astar3.restype = ctypes.c_int
lib.astar.argtypes = [ctypes.c_int, ctypes.c_int, P8, P8, P8, P8, P8, ctypes.c_int, np.ctypeslib.ndpointer(np.int32), ctypes.c_int]
lib.astar.restype = ctypes.c_int
nets = {}
def nid(name):
    if name not in nets: nets[name] = len(nets) + 1
    return nets[name]
LI = {pcbnew.F_Cu: 0, pcbnew.In2_Cu: 1, pcbnew.B_Cu: 2}
NL = 3
LAY = [pcbnew.F_Cu, pcbnew.In2_Cu, pcbnew.B_Cu]
VIA_R = 0.225
EXPC = 0.03          # clearance raster expansion


class Raster:
    def __init__(self, exp):
        self.exp = exp
        self.img = [Image.new('I', (NX, NY), 0) for _ in range(3)]
        self.d = [ImageDraw.Draw(i) for i in self.img]
    def rect(self, l, x0, y0, x1, y1, n):
        e = self.exp; self.d[l].rectangle([(x0 - e) / G, (y0 - e) / G, (x1 + e) / G - 1e-3, (y1 + e) / G - 1e-3], fill=n)
    def disc(self, l, x, y, r, n):
        r += self.exp; self.d[l].ellipse([(x - r) / G, (y - r) / G, (x + r) / G, (y + r) / G], fill=n)
    def line(self, l, a, c, w, n):
        k = max(1, int(round((w + 2 * self.exp) / G)))
        self.d[l].line([a[0] / G, a[1] / G, c[0] / G, c[1] / G], fill=n, width=k)
        self.disc(l, a[0], a[1], w / 2, n); self.disc(l, c[0], c[1], w / 2, n)
    def array(self):
        return np.stack([np.array(i, dtype=np.int32) for i in self.img])


RC, RE = Raster(EXPC), Raster(0.0)
keep = []
VIA_LINK = []   # (x, y, netid) via / PTH positions
for fp in B.GetFootprints():
    for p in fp.Pads():
        n = nid(p.GetNetname()) if p.GetNetname() else 99999
        att = p.GetAttribute(); pos = p.GetPosition(); bx = p.GetBoundingBox()
        if att == pcbnew.PAD_ATTRIB_NPTH:
            keep.append((TM(pos.x), TM(pos.y), TM(p.GetDrillSizeX()) / 2 + (1.8 if fp.GetReference() == 'M1' else 0.45))); continue
        ls = [0, 1, 2] if att == pcbnew.PAD_ATTRIB_PTH else [0 if p.IsOnLayer(pcbnew.F_Cu) else 2]
        if att == pcbnew.PAD_ATTRIB_PTH: VIA_LINK.append((TM(pos.x), TM(pos.y), n))
        for R in (RC, RE):
            for l in ls:
                if p.GetShape() == pcbnew.PAD_SHAPE_CIRCLE: R.disc(l, TM(pos.x), TM(pos.y), TM(p.GetSizeX()) / 2, n)
                else: R.rect(l, TM(bx.GetX()), TM(bx.GetY()), TM(bx.GetRight()), TM(bx.GetBottom()), n)
for t in B.GetTracks():
    n = nid(t.GetNetname())
    if t.Type() == pcbnew.PCB_VIA_T:
        x, y = TM(t.GetPosition().x), TM(t.GetPosition().y); VIA_LINK.append((x, y, n))
        for R in (RC, RE):
            for l in (0, 1, 2): R.disc(l, x, y, TM(t.GetWidth(pcbnew.F_Cu)) / 2, n)
    else:
        a, c = t.GetStart(), t.GetEnd(); l = LI.get(t.GetLayer())
        if l is None: continue
        for R in (RC, RE): R.line(l, (TM(a.x), TM(a.y)), (TM(c.x), TM(c.y)), TM(t.GetWidth()), n)
OC, OE = RC.array(), RE.array()
e = int(0.3 / G)
for o in (OC,):
    o[:, :e, :] = -1; o[:, -e:, :] = -1; o[:, :, :e] = -1; o[:, :, -e:] = -1
yy, xx = np.mgrid[0:NY, 0:NX]; xs, ys = (xx + .5) * G, (yy + .5) * G
for (x, y, r) in keep:
    m = (xs - x) ** 2 + (ys - y) ** 2 <= r * r
    OC[0][m] = -1; OC[1][m] = -1; OC[2][m] = -1
del xx, yy

# ---------------------------------------------------------------- unconnected pairs (non-GND) from DRC
d = json.load(open(drcj))
pairs = collections.defaultdict(list)
for u in d['unconnected_items']:
    m = re.search(r'\[([^\]]+)\]', u['items'][0]['description'])
    if not m or m.group(1) == 'GND': continue
    pairs[m.group(1)].append([(i['pos']['x'], i['pos']['y']) for i in u['items']])
SKIP = {'B1_SW', 'B2_SW'}
print('nets', len(pairs), 'pairs', sum(len(v) for v in pairs.values()), flush=True)
STRUCT = np.ones((3, 3), bool)
new_tracks, new_vias = [], []


def exact_component(n, x, y):
    """connected copper (exact geometry, both layers linked by vias/PTH) of net n nearest to (x, y)"""
    labs = [ndimage.label(OE[l] == n, structure=STRUCT) for l in (0, 1, 2)]
    offs = [0, labs[0][1], labs[0][1] + labs[1][1]]
    parent = list(range(sum(x[1] for x in labs) + 2))
    def f(a):
        while parent[a] != a: parent[a] = parent[parent[a]]; a = parent[a]
        return a
    for (vx, vy, vn) in VIA_LINK:
        if vn != n: continue
        j, i = int(vy / G), int(vx / G); ids = []
        for l, o in ((0, offs[0]), (1, offs[1]), (2, offs[2])):
            sub = labs[l][0][max(j - 2, 0):j + 3, max(i - 2, 0):i + 3]
            ids += [int(v) + o for v in np.unique(sub) if v]
        for q in ids[1:]: parent[f(q)] = f(ids[0])
    # nearest labelled cell
    j0, i0 = int(y / G), int(x / G); best = None
    for r in (6, 14, 30, 60):
        for l in (0, 1, 2):
            sub = labs[l][0][max(j0 - r, 0):j0 + r + 1, max(i0 - r, 0):i0 + r + 1]
            jj, ii = np.nonzero(sub)
            if len(jj):
                dd = (jj + max(j0 - r, 0) - j0) ** 2 + (ii + max(i0 - r, 0) - i0) ** 2; k = dd.argmin()
                if best is None or dd[k] < best[0]: best = (dd[k], f(int(sub[jj[k], ii[k]]) + offs[l]))
        if best: break
    if best is None: return None
    root = best[1]; mask = np.zeros((3, NY, NX), bool)
    for l in (0, 1, 2):
        lab = labs[l][0]; o = offs[l]
        mp = np.zeros(lab.max() + 1, np.int32)
        for v in np.unique(lab[lab > 0]): mp[v] = f(int(v) + o)
        mask[l] = mp[lab] == root
    return mask


def astar_route(net, sm, gm):
    n = nets[net]
    cls = B.GetDesignSettings().m_NetSettings.GetEffectiveNetClass(net)
    base_w = TM(cls.GetTrackWidth())
    js = np.concatenate([np.nonzero(sm.any(0))[0], np.nonzero(gm.any(0))[0]]); is_ = np.concatenate([np.nonzero(sm.any(0))[1], np.nonzero(gm.any(0))[1]])
    for w, clr in ((min(base_w, 0.25), 0.15), (0.15, 0.13), (0.12, 0.11)):
        for margin in (3.0, 10.0, 80.0):
            k = int(margin / G)
            i0, i1 = max(is_.min() - k, 0), min(is_.max() + k + 1, NX); j0, j1 = max(js.min() - k, 0), min(js.max() + k + 1, NY)
            ow = OC[:, j0:j1, i0:i1]
            obst = (ow != 0) & (ow != n)
            dist = np.stack([ndimage.distance_transform_edt(~obst[l]) for l in (0, 1, 2)]) * G
            free = (dist >= clr + w / 2 + 0.02) | (OE[:, j0:j1, i0:i1] == n)
            vr = clr + VIA_R + 0.02
            viaok = (dist[0] >= vr) & (dist[1] >= vr) & (dist[2] >= vr) & (ow[0] != -1) & (ow[1] != -1) & (ow[2] != -1)
            H_, W_ = j1 - j0, i1 - i0
            st = np.ascontiguousarray(sm[:, j0:j1, i0:i1], np.uint8); go = np.ascontiguousarray(gm[:, j0:j1, i0:i1], np.uint8)
            outp = np.zeros(3_000_000, np.int32)
            kk = lib.astar3(W_, H_, 3, np.ascontiguousarray(free, np.uint8).ravel(), np.ascontiguousarray(viaok, np.uint8).ravel(),
                            st.ravel(), go.ravel(), np.zeros(3 * H_ * W_, np.uint8), 160, outp, len(outp))
            if kk > 0:
                NN = W_ * H_; path = []
                for c in outp[:kk][::-1]:
                    l, rr = divmod(int(c), NN); jj, ii = divmod(rr, W_); path.append((l, jj + j0, ii + i0))
                return path, w
    return None


def commit(net, path, w):
    n = nets[net]; rad = int(math.ceil((w / 2 + EXPC) / G)); r2 = int(math.ceil((VIA_R + EXPC) / G))
    segs, cur = [], [path[0]]
    for k, (l, j, i) in enumerate(path):
        sub = OC[l, max(j - rad, 0):j + rad + 1, max(i - rad, 0):i + rad + 1]; sub[sub == 0] = n
        OE[l, j, i] = n
        if k and path[k - 1][0] != l:
            new_vias.append((net, (i + .5) * G, (j + .5) * G)); VIA_LINK.append(((i + .5) * G, (j + .5) * G, n))
            for ll in (0, 1, 2):
                sub = OC[ll, max(j - r2, 0):j + r2 + 1, max(i - r2, 0):i + r2 + 1]; sub[sub == 0] = n
                OE[ll, max(j - 4, 0):j + 5, max(i - 4, 0):i + 5] = n
    cur = [path[0]]
    for a in path[1:]:
        b = cur[-1]
        if a[0] != b[0]:
            if len(cur) > 1: segs.append((cur[0], cur[-1]))
            cur = [a]; continue
        if len(cur) >= 2:
            d1 = (cur[-1][1] - cur[-2][1], cur[-1][2] - cur[-2][2]); d2 = (a[1] - b[1], a[2] - b[2])
            if d1 != d2: segs.append((cur[0], cur[-1])); cur = [b]
        cur.append(a)
    if len(cur) > 1: segs.append((cur[0], cur[-1]))
    for a, b in segs:
        new_tracks.append((net, a[0], ((a[2] + .5) * G, (a[1] + .5) * G), ((b[2] + .5) * G, (b[1] + .5) * G), w))


ok = fail = 0; failed = []
for net, prs in sorted(pairs.items()):
    if net in SKIP: continue
    n = nets.get(net)
    if n is None: continue
    for p0, p1 in prs:
        sm = exact_component(n, *p0); gm = exact_component(n, *p1)
        if sm is None or gm is None: fail += 1; failed.append(net); print('NOCOPPER', net, flush=True); continue
        if (sm & gm).any(): continue            # already one component
        r = astar_route(net, sm, gm)
        if r is None: fail += 1; failed.append(net); print('FAIL', net, flush=True); continue
        commit(net, *r); ok += 1
print('routed', ok, 'failed', fail, sorted(set(failed)), flush=True)

# ---------------------------------------------------------------- GND pads without via to the inner plane: dog-bone stub + via
gid = nets['GND']
gpads = []
for u in d['unconnected_items']:
    for i in u['items']:
        if i['description'].startswith('Pad ') and '[GND]' in i['description']:
            gpads.append((i['pos']['x'], i['pos']['y']))
gpads = list(dict.fromkeys((round(x, 3), round(y, 3)) for x, y in gpads))
print('GND pads to via:', len(gpads), flush=True)
gok = gfail = 0
for (x, y) in gpads:
    j0, i0 = int(y / G), int(x / G)
    lay = [l for l in (0, 2) if OE[l, j0, i0] == gid]
    if not lay: gfail += 1; continue
    l = lay[0]; done = False
    R = int(4.0 / G)
    sl = (slice(None), slice(max(j0 - R, 0), j0 + R), slice(max(i0 - R, 0), i0 + R))
    ow = OC[sl]; obst = (ow != 0) & (ow != gid)
    dist = np.stack([ndimage.distance_transform_edt(~obst[q]) for q in (0, 1, 2)]) * G
    oj, oi = max(j0 - R, 0), max(i0 - R, 0)
    for rad in np.arange(0.6, 3.2, 0.1):
        for ang in np.arange(0, 360, 15):
            cx, cy = x + rad * math.cos(math.radians(ang)), y + rad * math.sin(math.radians(ang))
            cj, ci = int(cy / G) - oj, int(cx / G) - oi
            if not (0 <= cj < dist.shape[1] and 0 <= ci < dist.shape[2]): continue
            if min(dist[0, cj, ci], dist[1, cj, ci], dist[2, cj, ci]) < 0.15 + VIA_R + 0.03: continue
            if ow[:, cj, ci].min() == -1: continue
            ts = np.linspace(0, 1, int(rad / G) + 2)
            okl = True
            for tt in ts:
                pj, pi = int((y + (cy - y) * tt) / G) - oj, int((x + (cx - x) * tt) / G) - oi
                if not (0 <= pj < dist.shape[1] and 0 <= pi < dist.shape[2]) or dist[l, pj, pi] < 0.13 + 0.075 + 0.03 or ow[l, pj, pi] == -1: okl = False; break
            if not okl: continue
            new_tracks.append(('GND', l, (x, y), (cx, cy), 0.15)); new_vias.append(('GND', cx, cy))
            for ll in (0, 1, 2):
                rr = int(math.ceil((VIA_R + EXPC) / G)); sub = OC[ll, max(int(cy / G) - rr, 0):int(cy / G) + rr + 1, max(int(cx / G) - rr, 0):int(cx / G) + rr + 1]; sub[sub == 0] = gid
            for tt in ts:
                OC[l, int((y + (cy - y) * tt) / G), int((x + (cx - x) * tt) / G)] = gid
            done = True; break
        if done: break
    if done: gok += 1
    else: gfail += 1; print('GNDFAIL', x, y)
print('GND vias added', gok, 'failed', gfail, flush=True)
for net, l, a, c, w in new_tracks[-gok:] if gok else []:
    pass
for net, l, a, c, w in new_tracks:
    t = pcbnew.PCB_TRACK(B); t.SetStart(pcbnew.VECTOR2I(FM(a[0]), FM(a[1]))); t.SetEnd(pcbnew.VECTOR2I(FM(c[0]), FM(c[1])))
    t.SetWidth(FM(w)); t.SetLayer(LAY[l]); t.SetNet(B.FindNet(net)); B.Add(t)
for net, x, y in new_vias:
    v = pcbnew.PCB_VIA(B); v.SetPosition(pcbnew.VECTOR2I(FM(x), FM(y))); v.SetWidth(FM(0.45)); v.SetDrill(FM(0.2)); v.SetNet(B.FindNet(net)); B.Add(v)

pcbnew.ZONE_FILLER(B).Fill(B.Zones())
B.Save(out)
shutil.copy(src.replace('.kicad_pcb', '.kicad_pro'), out.replace('.kicad_pcb', '.kicad_pro'))
print('saved', out)
