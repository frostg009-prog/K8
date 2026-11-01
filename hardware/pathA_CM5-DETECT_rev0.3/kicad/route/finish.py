# -*- coding: utf-8 -*-
"""Finisher: route the remaining unconnected links on an already routed board (fine 0.05 mm grid), stitch GND zones.
KiCad python:  /usr/bin/python3 finish.py in.kicad_pcb drc.json out.kicad_pcb
"""
import sys, os, re, json, math, ctypes, subprocess, collections
import numpy as np
import pcbnew
from PIL import Image, ImageDraw
from scipy import ndimage

HERE = os.path.dirname(os.path.abspath(__file__))
src, drcj, out = sys.argv[1:4]
FM0 = pcbnew.FromMM
TM = pcbnew.ToMM
FM = lambda v: FM0(float(v))
B = pcbnew.LoadBoard(src)
bb = B.GetBoardEdgesBoundingBox()
W, L = TM(bb.GetWidth()), TM(bb.GetHeight())
G = 0.05
NX, NY = int(round(W / G)), int(round(L / G))
so = HERE + '/libastar.so'
lib = ctypes.CDLL(so)
P8 = np.ctypeslib.ndpointer(np.uint8, flags='C_CONTIGUOUS')
lib.astar.argtypes = [ctypes.c_int, ctypes.c_int, P8, P8, P8, P8, P8, ctypes.c_int, np.ctypeslib.ndpointer(np.int32), ctypes.c_int]
lib.astar.restype = ctypes.c_int

nets = {}
def nid(name):
    if name not in nets: nets[name] = len(nets) + 1
    return nets[name]

EXP = 0.03
img = [Image.new('I', (NX, NY), 0), Image.new('I', (NX, NY), 0)]
drw = [ImageDraw.Draw(i) for i in img]
px = lambda v: v / G
def rect(l, x0, y0, x1, y1, n):
    drw[l].rectangle([px(x0 - EXP), px(y0 - EXP), px(x1 + EXP), px(y1 + EXP)], fill=n)
def disc(l, x, y, r, n):
    drw[l].ellipse([px(x - r), px(y - r), px(x + r), px(y + r)], fill=n)
LI = {pcbnew.F_Cu: 0, pcbnew.B_Cu: 1}
VM_pts = []
# edge / holes keepout = -1  (draw last)
keep = []
for fp in B.GetFootprints():
    for p in fp.Pads():
        b = p.GetBoundingBox(); n = nid(p.GetNetname()) if p.GetNetname() else 99999
        att = p.GetAttribute()
        if att == pcbnew.PAD_ATTRIB_NPTH:
            keep.append((TM(p.GetPosition().x), TM(p.GetPosition().y), TM(p.GetDrillSizeX()) / 2 + 0.25)); continue
        ls = [0, 1] if att == pcbnew.PAD_ATTRIB_PTH else [0 if p.IsOnLayer(pcbnew.F_Cu) else 1]
        if att == pcbnew.PAD_ATTRIB_PTH: VM_pts.append((TM(p.GetPosition().x), TM(p.GetPosition().y), n))
        for l in ls:
            if p.GetShape() == pcbnew.PAD_SHAPE_CIRCLE:
                disc(l, TM(p.GetPosition().x), TM(p.GetPosition().y), TM(p.GetSizeX()) / 2 + EXP, n)
            else:
                rect(l, TM(b.GetX()), TM(b.GetY()), TM(b.GetRight()), TM(b.GetBottom()), n)
for t in B.GetTracks():
    n = nid(t.GetNetname())
    if t.Type() == pcbnew.PCB_VIA_T:
        for l in (0, 1): disc(l, TM(t.GetPosition().x), TM(t.GetPosition().y), TM(t.GetWidth(pcbnew.F_Cu)) / 2 + EXP, n)
    else:
        l = LI[t.GetLayer()]; w = max(2, int(round((TM(t.GetWidth()) + 2 * EXP) / G)))
        a, c = t.GetStart(), t.GetEnd()
        drw[l].line([px(TM(a.x)), px(TM(a.y)), px(TM(c.x)), px(TM(c.y))], fill=n, width=w)
        disc(l, TM(a.x), TM(a.y), TM(t.GetWidth()) / 2 + EXP, n); disc(l, TM(c.x), TM(c.y), TM(t.GetWidth()) / 2 + EXP, n)
owner = np.stack([np.array(i, dtype=np.int32) for i in img])
e = int(0.3 / G)
owner[:, :e, :] = -1; owner[:, -e:, :] = -1; owner[:, :, :e] = -1; owner[:, :, -e:] = -1
yy, xx = np.mgrid[0:NY, 0:NX]
xs, ys = (xx + .5) * G, (yy + .5) * G
for (x, y, r) in keep:
    m = (xs - x) ** 2 + (ys - y) ** 2 <= r * r
    owner[0][m] = -1; owner[1][m] = -1
NAME = {v: k for k, v in nets.items()}

# ------------------------------------------------------------------ nets to finish (from DRC) -> own component analysis
d = json.load(open(drcj))
todo = set()
for u in d['unconnected_items']:
    m = re.search(r'\[([^\]]+)\]', u['items'][0]['description'])
    if m and m.group(1) not in ('GND',): todo.add(m.group(1))
SKIP = {'B1_SW', 'B2_SW'}
todo -= SKIP
print('nets to finish:', len(todo), flush=True)
STRUCT = np.ones((3, 3), bool)


def components(n):
    labs, cnts = [], []
    tot = 0
    L2 = []
    for l in (0, 1):
        lab, k = ndimage.label(owner[l] == n, structure=STRUCT)
        L2.append((lab, k))
    off = L2[0][1]
    parent = list(range(L2[0][1] + L2[1][1] + 1))
    def f(x):
        while parent[x] != x:
            parent[x] = parent[parent[x]]; x = parent[x]
        return x
    for (x, y, nn) in VM_pts:
        if nn != n: continue
        j, i = int(y / G), int(x / G)
        win = [(jj, ii) for jj in range(j - 3, j + 4) for ii in range(i - 3, i + 4) if 0 <= jj < NY and 0 <= ii < NX]
        a0 = [L2[0][0][jj, ii] for jj, ii in win if L2[0][0][jj, ii]]
        a1 = [L2[1][0][jj, ii] + off for jj, ii in win if L2[1][0][jj, ii]]
        al = a0 + a1
        for q in al[1:]: parent[f(q)] = f(al[0])
    comp = np.zeros((2, NY, NX), np.int32)
    for l in (0, 1):
        lab = L2[l][0]; mk = lab > 0
        comp[l][mk] = np.vectorize(lambda v, o=(0 if l == 0 else off): f(v + o) if False else 0)(np.array([0])) if False else 0
    # map labels to roots
    roots = {}
    for l in (0, 1):
        lab = L2[l][0]; o = 0 if l == 0 else off
        idx = np.unique(lab[lab > 0])
        mp = np.zeros(lab.max() + 1, np.int32)
        for v in idx: mp[v] = f(int(v) + o)
        comp[l] = mp[lab]
    return comp


new_tracks_n = 0
new_tracks, new_vias = [], []
VIA_R = 0.225


def cells_near(n, x, y, r, rmax=1.5):
    while r <= rmax:
        m = np.zeros((2, NY, NX), bool)
        j0, j1, i0, i1 = max(int((y - r) / G), 0), min(int((y + r) / G) + 1, NY), max(int((x - r) / G), 0), min(int((x + r) / G) + 1, NX)
        sub = owner[:, j0:j1, i0:i1] == n
        circ = ((xs[j0:j1, i0:i1] - x) ** 2 + (ys[j0:j1, i0:i1] - y) ** 2) <= r * r
        m[:, j0:j1, i0:i1] = sub & circ[None]
        if m.any(): return m
        r *= 1.6
    return None


def route(net, p0, p1):
    n = nets[net]
    cls = B.GetDesignSettings().m_NetSettings.GetEffectiveNetClass(net)
    base_w = TM(cls.GetTrackWidth())
    for w, clr in ((min(base_w, 0.25), 0.15), (0.15, 0.13), (0.12, 0.11)):
        for r in (0.35, 0.2):
            s = cells_near(n, p0[0], p0[1], r); g = cells_near(n, p1[0], p1[1], r)
            if s is None or g is None: continue
            if (s & g).any(): s = s & ~g
            if not s.any(): continue
            for margin in (4.0, 15.0, 80.0):
                xs_ = [p0[0], p1[0]]; ys_ = [p0[1], p1[1]]
                i0, i1 = max(int((min(xs_) - margin) / G), 0), min(int((max(xs_) + margin) / G) + 1, NX)
                j0, j1 = max(int((min(ys_) - margin) / G), 0), min(int((max(ys_) + margin) / G) + 1, NY)
                ow = owner[:, j0:j1, i0:i1]
                obst = (ow != 0) & (ow != n)
                dist = np.stack([ndimage.distance_transform_edt(~obst[l]) for l in (0, 1)]) * G
                free = (dist >= clr + w / 2 + 0.02) | (ow == n)
                vr = clr + VIA_R + 0.02
                viaok = (dist[0] >= vr) & (dist[1] >= vr) & (ow[0] != -1) & (ow[1] != -1)
                st = np.ascontiguousarray(s[:, j0:j1, i0:i1], np.uint8); go = np.ascontiguousarray(g[:, j0:j1, i0:i1], np.uint8)
                if not st.any() or not go.any(): continue
                H_, W_ = j1 - j0, i1 - i0
                pen = np.zeros((2, H_, W_), np.uint8)
                outp = np.zeros(2_000_000, np.int32)
                k = lib.astar(W_, H_, np.ascontiguousarray(free, np.uint8).ravel(), np.ascontiguousarray(viaok, np.uint8).ravel(),
                              st.ravel(), go.ravel(), pen.ravel(), 160, outp, len(outp))
                if k > 0:
                    NN = W_ * H_
                    path = []
                    for c in outp[:k][::-1]:
                        l, rr = divmod(int(c), NN); jj, ii = divmod(rr, W_)
                        path.append((l, jj + j0, ii + i0))
                    return path, w
    return None


def commit(net, path, w):
    n = nets[net]
    wcells = max(2, int(round((w + 2 * EXP) / G)))
    for k, (l, j, i) in enumerate(path):
        if k and path[k - 1][0] != l:
            x, y = (i + .5) * G, (j + .5) * G
            new_vias.append((net, x, y))
            for ll in (0, 1): disc(ll, x, y, VIA_R + EXP, n)
    segs = []
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
        l = a[0]
        new_tracks.append((net, l, ((a[2] + .5) * G, (a[1] + .5) * G), ((b[2] + .5) * G, (b[1] + .5) * G), w))
        drw[l].line([a[2] + .5, a[1] + .5, b[2] + .5, b[1] + .5], fill=n, width=wcells)
    for (l, j, i) in path:
        owner[l, j, i] = n


# owner must reflect new copper: redraw via PIL images each commit is costly -> stamp cells directly
def commit2(net, path, w):
    n = nets[net]; rad = int(math.ceil((w / 2 + EXP) / G))
    for k, (l, j, i) in enumerate(path):
        owner[l, max(j - rad, 0):j + rad + 1, max(i - rad, 0):i + rad + 1][owner[l, max(j - rad, 0):j + rad + 1, max(i - rad, 0):i + rad + 1] == 0] = n
        if k and path[k - 1][0] != l:
            r2 = int(math.ceil((VIA_R + EXP) / G))
            for ll in (0, 1):
                sub = owner[ll, max(j - r2, 0):j + r2 + 1, max(i - r2, 0):i + r2 + 1]; sub[sub == 0] = n
    commit(net, path, w)


def route_masks(net, sm, gm):
    n = nets[net]
    cls = B.GetDesignSettings().m_NetSettings.GetEffectiveNetClass(net)
    base_w = TM(cls.GetTrackWidth())
    ys0, xs0 = np.nonzero(sm.any(0)); ys1, xs1 = np.nonzero(gm.any(0))
    for w, clr in ((min(base_w, 0.25), 0.15), (0.15, 0.13), (0.12, 0.11)):
        for margin in (3.0, 12.0, 80.0):
            i0 = max(min(xs0.min(), xs1.min()) - int(margin / G), 0); i1 = min(max(xs0.max(), xs1.max()) + int(margin / G) + 1, NX)
            j0 = max(min(ys0.min(), ys1.min()) - int(margin / G), 0); j1 = min(max(ys0.max(), ys1.max()) + int(margin / G) + 1, NY)
            ow = owner[:, j0:j1, i0:i1]
            obst = (ow != 0) & (ow != n)
            dist = np.stack([ndimage.distance_transform_edt(~obst[l]) for l in (0, 1)]) * G
            free = (dist >= clr + w / 2 + 0.02) | (ow == n)
            vr = clr + VIA_R + 0.02
            viaok = (dist[0] >= vr) & (dist[1] >= vr) & (ow[0] != -1) & (ow[1] != -1)
            st = np.ascontiguousarray(sm[:, j0:j1, i0:i1], np.uint8); go = np.ascontiguousarray(gm[:, j0:j1, i0:i1], np.uint8)
            H_, W_ = j1 - j0, i1 - i0
            pen = np.zeros((2, H_, W_), np.uint8)
            outp = np.zeros(3_000_000, np.int32)
            k = lib.astar(W_, H_, np.ascontiguousarray(free, np.uint8).ravel(), np.ascontiguousarray(viaok, np.uint8).ravel(),
                          st.ravel(), go.ravel(), pen.ravel(), 160, outp, len(outp))
            if k > 0:
                NN = W_ * H_; path = []
                for c in outp[:k][::-1]:
                    l, rr = divmod(int(c), NN); jj, ii = divmod(rr, W_)
                    path.append((l, jj + j0, ii + i0))
                return path, w
    return None


ok = fail = 0
failed_nets = []
for net in sorted(todo):
    n = nets[net]
    for guard in range(12):
        comp = components(n)
        ids = [c for c in np.unique(comp) if c > 0]
        if len(ids) <= 1: break
        # closest pair of components (by centroid distance of cells) -> connect smallest to nearest
        pts = {}
        for c in ids:
            jj, ii = np.nonzero((comp == c).any(0))
            pts[c] = (jj, ii)
        best = None
        for a_ in ids:
            for b_ in ids:
                if a_ >= b_: continue
                ja, ia = pts[a_]; jb, ib = pts[b_]
                sa = slice(None, None, max(1, len(ja) // 60)); sb = slice(None, None, max(1, len(jb) // 60))
                dd = ((ja[sa, None] - jb[None, sb]) ** 2 + (ia[sa, None] - ib[None, sb]) ** 2).min()
                if best is None or dd < best[0]: best = (dd, a_, b_)
        _, a_, b_ = best
        sm = comp == a_; gm = comp == b_
        r = route_masks(net, sm, gm)
        if r is None:
            fail += 1; failed_nets.append(net); print('FAIL', net, flush=True); break
        commit2(net, r[0], r[1]); ok += 1
print('routed links', ok, 'failed', fail, failed_nets, flush=True)

# ------------------------------------------------------------------ write to board
def add_track(net, l, a, c, w):
    t = pcbnew.PCB_TRACK(B); t.SetStart(pcbnew.VECTOR2I(FM(a[0]), FM(a[1]))); t.SetEnd(pcbnew.VECTOR2I(FM(c[0]), FM(c[1])))
    t.SetWidth(FM(w)); t.SetLayer(pcbnew.F_Cu if l == 0 else pcbnew.B_Cu); t.SetNet(B.FindNet(net)); B.Add(t)
for net, l, a, c, w in new_tracks: add_track(net, l, a, c, w)
for net, x, y in new_vias:
    v = pcbnew.PCB_VIA(B); v.SetPosition(pcbnew.VECTOR2I(FM(x), FM(y))); v.SetWidth(FM(0.45)); v.SetDrill(FM(0.2)); v.SetNet(B.FindNet(net)); B.Add(v)

# ------------------------------------------------------------------ GND stitching vias (zone islands -> inner GND planes)
g = nets.get('GND')
free_m = np.ones((NY, NX), bool)
obst = (owner[0] != 0) & (owner[0] != g) | ((owner[1] != 0) & (owner[1] != g))
dist = ndimage.distance_transform_edt(~obst) * G
okv = (dist >= 0.2 + VIA_R + 0.05)
STEP = 2.5
cnt = 0
for y in np.arange(1.0, L - 1.0, STEP):
    for x in np.arange(1.0, W - 1.0, STEP):
        j, i = int(y / G), int(x / G)
        if okv[j, i]:
            v = pcbnew.PCB_VIA(B); v.SetPosition(pcbnew.VECTOR2I(FM(x), FM(y))); v.SetWidth(FM(0.45)); v.SetDrill(FM(0.2)); v.SetNet(B.FindNet('GND')); B.Add(v)
            r2 = int(math.ceil((VIA_R + EXP) / G))
            for ll in (0, 1): owner[ll, max(j - r2, 0):j + r2 + 1, max(i - r2, 0):i + r2 + 1] = g
            obst[max(j - 10, 0):j + 11, max(i - 10, 0):i + 11] |= False
            cnt += 1
print('stitching vias', cnt)
pcbnew.ZONE_FILLER(B).Fill(B.Zones())
B.Save(out)
shutil = __import__('shutil'); shutil.copy(src.replace('.kicad_pcb', '.kicad_pro'), out.replace('.kicad_pcb', '.kicad_pro'))
print('saved', out)
