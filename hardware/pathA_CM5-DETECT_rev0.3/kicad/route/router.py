# -*- coding: utf-8 -*-
"""Grid router for CM5-DETECT (2 signal layers F.Cu/B.Cu + inner planes In1=GND, In2=GND/5V/VIN).
input: board.json (extract.py)  output: routes.json (tracks + vias) consumed by apply.py
Rules: Rezonit/JLC 4-layer: track >= 0.13 mm, clearance 0.125 mm (+0.07 mm grid safety), via 0.45/0.2 mm.
"""
import json, sys, os, ctypes, subprocess, math, time
import numpy as np
from scipy import ndimage

HERE = os.path.dirname(os.path.abspath(__file__))
so = HERE + '/libastar.so'
if not os.path.exists(so) or os.path.getmtime(so) < os.path.getmtime(HERE + '/astar.c'):
    subprocess.check_call(['gcc', '-O2', '-shared', '-fPIC', HERE + '/astar.c', '-o', so])
lib = ctypes.CDLL(so)
P8 = np.ctypeslib.ndpointer(np.uint8, flags='C_CONTIGUOUS')
lib.astar.argtypes = [ctypes.c_int, ctypes.c_int, P8, P8, P8, P8, P8, ctypes.c_int, np.ctypeslib.ndpointer(np.int32), ctypes.c_int]
lib.astar.restype = ctypes.c_int

G = 0.1
SAFE = 0.07
VIA_R = 0.225
D = json.load(open(sys.argv[1] if len(sys.argv) > 1 else HERE + '/board.json'))
W, L = D['W'], D['L']
NX, NY = int(round(W / G)), int(round(L / G))
nets = sorted(D['cls'].keys())
NID = {n: i + 1 for i, n in enumerate(nets)}
owner = np.zeros((2, NY, NX), np.int32)          # 0 free, >0 net copper, -1 keepout
xs = (np.arange(NX) + 0.5) * G
ys = (np.arange(NY) + 0.5) * G
LI = {'F': 0, 'B': 1}

# ---- edge keepout (copper to edge 0.3 mm)
e = int(round(0.3 / G))
owner[:, :e, :] = -1; owner[:, -e:, :] = -1; owner[:, :, :e] = -1; owner[:, :, -e:] = -1


def cells_rect(x0, y0, x1, y1):
    i0, i1 = int(math.ceil(x0 / G - 0.5)), int(math.floor(x1 / G - 0.5))
    j0, j1 = int(math.ceil(y0 / G - 0.5)), int(math.floor(y1 / G - 0.5))
    return max(j0, 0), min(j1, NY - 1), max(i0, 0), min(i1, NX - 1)


padcells = []   # (netid, layer, mask-slices)
for p in D['pads']:
    x0, y0, x1, y1 = p['bb']
    if 'HOLE' in p['layers']:
        r = p['drill'] / 2 + 0.2
        J, I = np.ogrid[:NY, :NX]
        m = (xs[None, :] - p['x']) ** 2 + (ys[:, None] - p['y']) ** 2 <= r * r
        owner[0][m] = -1; owner[1][m] = -1
        continue
    nid = NID.get(p['net'], -2) if p['net'] else -2
    j0, j1, i0, i1 = cells_rect(x0, y0, x1, y1)
    if j1 < j0 or i1 < i0:   # tiny pad: take nearest cell
        j0 = j1 = min(NY - 1, int(p['y'] / G)); i0 = i1 = min(NX - 1, int(p['x'] / G))
    for lname in p['layers']:
        l = LI[lname]
        sub = owner[l, j0:j1 + 1, i0:i1 + 1]
        if p['round']:
            yy, xx = np.meshgrid(ys[j0:j1 + 1], xs[i0:i1 + 1], indexing='ij')
            m = (xx - p['x']) ** 2 + (yy - p['y']) ** 2 <= (p['w'] / 2) ** 2
            sub[m] = nid
        else:
            sub[:] = nid
        if p['drill'] > 0:   # drilled pads: keep a little margin around hole for vias
            pass
    p['cells'] = (j0, j1, i0, i1)
    p['nid'] = nid

# ---- inner plane membership
def poly_mask(pts):
    from matplotlib.path import Path
    yy, xx = np.meshgrid(ys, xs, indexing='ij')
    return Path(pts).contains_points(np.c_[xx.ravel(), yy.ravel()]).reshape(NY, NX)

zone = {}
try:
    import matplotlib  # noqa
except ImportError:
    subprocess.check_call([sys.executable, '-m', 'pip', 'install', '-q', 'matplotlib'])
for z in sorted(D['zones'], key=lambda z: z['prio']):
    m = poly_mask(z['pts'])
    key = z['layer']
    if key not in zone:
        zone[key] = np.zeros((NY, NX), np.int32)
    zone[key][m] = NID[z['net']]
PLANE = {}   # net -> mask where a via of that net reaches its plane
for lay, arr in zone.items():
    for nid in np.unique(arr):
        if nid > 0:
            n = nets[nid - 1]
            PLANE[n] = PLANE.get(n, np.zeros((NY, NX), bool)) | (arr == nid)
# plane edges: keep vias 0.5 mm inside the plane
for n in PLANE:
    PLANE[n] = ndimage.binary_erosion(PLANE[n], iterations=5)

disc = {}
COMMITTED = {}
PADSTAMP = owner.copy()


def stamp(l, j, i, r, nid):
    k = int(math.ceil(r / G))
    if r not in disc:
        yy, xx = np.mgrid[-k:k + 1, -k:k + 1]
        disc[r] = (xx * xx + yy * yy) * G * G <= r * r + 1e-9
    d = disc[r]
    j0, j1, i0, i1 = j - k, j + k + 1, i - k, i + k + 1
    dj0, di0 = max(0, -j0), max(0, -i0)
    j0c, i0c, j1c, i1c = max(j0, 0), max(i0, 0), min(j1, NY), min(i1, NX)
    sub = owner[l, j0c:j1c, i0c:i1c]
    dd = d[dj0:dj0 + (j1c - j0c), di0:di0 + (i1c - i0c)]
    sub[dd & (sub == 0)] = nid


tracks, vias, failed = [], [], []
NETTR = {}  # net -> (n_tracks_start..) handled via tags



def width_of(n, try_i=0):
    c = D['cls'][n]
    w = c['w']
    if try_i == 1: w = min(w, 0.4)
    if try_i == 2: w = min(w, 0.2)
    if try_i == 3: w = 0.13
    return max(w, 0.13), max(c['clr'], 0.125)


def route_conn(nid, n, w, clr, start, goal, win, viaok_extra=None, pen=None, allow_via=True, goal_via=None):
    j0, j1, i0, i1 = win
    sl = (slice(None), slice(j0, j1), slice(i0, i1))
    ow = owner[sl]
    obst = (ow != 0) & (ow != nid)
    dist = np.stack([ndimage.distance_transform_edt(~obst[l]) for l in (0, 1)]) * G
    free = (dist >= clr + w / 2 + SAFE) | (ow == nid)
    vr = clr + VIA_R + SAFE
    viaok = (dist[0] >= vr) & (dist[1] >= vr) & (ow[0] != -1) & (ow[1] != -1)
    if not allow_via:
        viaok[:] = False
    st = np.ascontiguousarray(start[sl], np.uint8)
    go = np.ascontiguousarray(goal[sl], np.uint8)
    if goal_via is not None:   # goal also = plane cells where a via may be dropped
        gv = goal_via[j0:j1, i0:i1] & (dist[0] >= vr) & (dist[1] >= vr) & (ow[0] != -1) & (ow[1] != -1)
        go = np.ascontiguousarray(go | np.stack([gv & free[0], gv & free[1]]), np.uint8)
    if not st.any() or not go.any():
        return None
    pe = np.zeros_like(st) if pen is None else np.ascontiguousarray(pen[sl], np.uint8)
    H_, W_ = j1 - j0, i1 - i0
    out = np.zeros(400000, np.int32)
    fr = np.ascontiguousarray(free, np.uint8)
    n_ = lib.astar(W_, H_, fr.ravel(), np.ascontiguousarray(viaok, np.uint8).ravel(), st.ravel(), go.ravel(), pe.ravel(), 120, out, len(out))
    if n_ < 0:
        return None
    path = []
    N = W_ * H_
    for c in out[:n_][::-1]:
        l, r = divmod(int(c), N)
        jj, ii = divmod(r, W_)
        path.append((l, jj + j0, ii + i0))
    end_via = goal_via is not None and not goal[path[-1]]
    return path, end_via


def commit(nid, n, w, path, end_via=False):
    seg = []
    COMMITTED.setdefault(n, []).append((w, path, end_via))
    for k, (l, j, i) in enumerate(path):
        stamp(l, j, i, w / 2, nid)
        if k and path[k - 1][0] != l:
            vias.append((n, (i + 0.5) * G, (j + 0.5) * G))
            stamp(0, j, i, VIA_R, nid); stamp(1, j, i, VIA_R, nid)
    if end_via:
        l, j, i = path[-1]
        vias.append((n, (i + 0.5) * G, (j + 0.5) * G)); stamp(0, j, i, VIA_R, nid); stamp(1, j, i, VIA_R, nid)
    # compress into segments
    cur = [path[0]]
    for a in path[1:]:
        b = cur[-1]
        if a[0] != b[0]:
            if len(cur) > 1: tracks.append((n, 'FB'[b[0]], cur[0], cur[-1], w))
            cur = [a]; continue
        if len(cur) >= 2:
            d1 = (cur[-1][1] - cur[-2][1], cur[-1][2] - cur[-2][2]); d2 = (a[1] - b[1], a[2] - b[2])
            if d1 != d2:
                tracks.append((n, 'FB'[b[0]], cur[0], cur[-1], w)); cur = [b]
        cur.append(a)
    if len(cur) > 1:
        tracks.append((n, 'FB'[cur[0][0]], cur[0], cur[-1], w))


def pad_mask(p, nid):
    m = np.zeros((2, NY, NX), bool)
    j0, j1, i0, i1 = p['cells']
    for lname in p['layers']:
        l = LI[lname]
        m[l, j0:j1 + 1, i0:i1 + 1] = owner[l, j0:j1 + 1, i0:i1 + 1] == nid
    return m


def window(masks, margin):
    js, is_ = [], []
    for m in masks:
        jj, ii = np.nonzero(m.any(0))
        js += [jj.min(), jj.max()]; is_ += [ii.min(), ii.max()]
    k = int(margin / G)
    return max(min(js) - k, 0), min(max(js) + k + 1, NY), max(min(is_) - k, 0), min(max(is_) + k + 1, NX)


PADS = {}
for p in D['pads']:
    if p.get('nid', 0) and p['nid'] > 0:
        PADS.setdefault(p['net'], []).append(p)

HI = {'+5V_CM5', '+5V_AUX', 'VIN_PROT', 'GND'}


def plane_fanout(n):
    """drop vias from every SMD pad of a plane net to its inner plane"""
    nid = NID[n]; ok = 0; bad = 0
    for p in PADS.get(n, []):
        if len(p['layers']) == 2:
            continue   # PTH reaches the plane itself
        pm = pad_mask(p, nid)
        if not pm.any():
            continue
        if not PLANE[n][pm.any(0)].any() and not PLANE[n][max(p['cells'][0] - 15, 0):p['cells'][1] + 15, max(p['cells'][2] - 15, 0):p['cells'][3] + 15].any():
            continue
        area = (p['bb'][2] - p['bb'][0]) * (p['bb'][3] - p['bb'][1])
        nv = 3 if (n in HI and area > 2.0) else 1
        for _ in range(nv):
            win = window([pm], 3.0)
            w = 0.3 if n in HI else 0.2
            r = route_conn(nid, n, w, 0.125, pm, np.zeros_like(pm), win, allow_via=False, goal_via=PLANE[n])
            if r is None:
                r = route_conn(nid, n, 0.13, 0.125, pm, np.zeros_like(pm), win, allow_via=False, goal_via=PLANE[n])
                w = 0.13
            if r is None:
                bad += 1; break
            commit(nid, n, w, r[0], end_via=True); ok += 1
    return ok, bad


def route_net(n, pen=None):
    nid = NID[n]
    ps = PADS.get(n, [])
    plane = PLANE.get(n)
    if plane is not None:   # only pads not already tied to the plane
        ps = [p for p in ps if not (len(p['layers']) == 2 and plane[p['cells'][0]:p['cells'][1] + 1, p['cells'][2]:p['cells'][3] + 1].any())]
        ps = [p for p in ps if not any(v[0] == n and abs(v[1] - p['x']) < 3.5 and abs(v[2] - p['y']) < 3.5 for v in vias)]
        if not ps:
            return True
    if len(ps) < 2 and plane is None:
        return True
    masks = [pad_mask(p, nid) for p in ps]
    masks = [m for m in masks if m.any()]
    if not masks:
        return True
    tree = masks[0].copy()
    todo = masks[1:]
    if plane is not None and not todo:
        todo = []
    while todo or plane is not None:
        goal = np.zeros_like(tree)
        for m in todo:
            goal |= m
        gv = plane if plane is not None else None
        done = False
        for tr in range(4):
            w, clr = width_of(n, tr)
            for margin in (4.0, 12.0, 60.0):
                win = window([tree] + todo, margin) if todo else window([tree], margin)
                r = route_conn(nid, n, w, clr, tree, goal, win, pen=pen, goal_via=gv)
                if r is not None:
                    break
            if r is not None:
                break
        if r is None:
            failed.append((n, len(todo)))
            return False
        path, endvia = r
        commit(nid, n, w, path, end_via=endvia)
        last = path[-1]
        tree[last] = True
        for l, j, i in path:
            tree[l, j, i] = True
        if endvia:
            plane = None
        hit = [m for m in todo if m[last]]
        todo = [m for m in todo if not m[last]]
        for m in hit:
            tree |= m
        if plane is None and not todo:
            break
    return True


def ripup(n):
    nid = NID[n]
    m = owner == nid
    owner[m] = PADSTAMP[m]
    COMMITTED.pop(n, None)
    tracks[:] = [t for t in tracks if t[0] != n]
    vias[:] = [v for v in vias if v[0] != n]

def recommit(n):
    for w, path, ev in COMMITTED.get(n, []):
        pass

t0 = time.time()
pairs = [n for n in nets if n.endswith('_P') or n.endswith('_DP')]
hs = []
for p in sorted(pairs):
    q = p[:-2] + '_N' if p.endswith('_P') else p[:-3] + '_DN'
    hs += [p, q]
hs = [n for n in hs if n in PADS]
def hp(n):
    ps = PADS.get(n, [])
    if not ps: return 0
    xs_ = [p['x'] for p in ps]; ys_ = [p['y'] for p in ps]
    return max(xs_) - min(xs_) + max(ys_) - min(ys_)
rest = [n for n in nets if n not in hs and n not in PLANE]
power = [n for n in rest if D['cls'][n]['cls'].startswith('PWR')]
sig = [n for n in rest if n not in power]
order = hs + sorted(sig, key=hp) + sorted(power, key=hp)

def pen_for(n):
    if n.endswith('_N') or n.endswith('_DN'):
        partner = n[:-2] + '_P' if n.endswith('_N') else n[:-3] + '_DP'
        if partner in NID:
            pm = (owner == NID[partner])
            d = np.stack([ndimage.distance_transform_edt(~pm[l]) for l in (0, 1)]) * G
            return np.where((d > 0.25) & (d < 0.45), 0, 6).astype(np.uint8)
    return None

def run(n):
    failed[:] = [f for f in failed if f[0] != n]
    return route_net(n, pen_for(n))

status = {}
for n in order:
    status[n] = run(n)
    print(('OK  ' if status[n] else 'FAIL') + ' %-16s %.0fs' % (n, time.time() - t0), flush=True)
# rip-up and reroute: failed net first, then the nets it displaced
for it in range(4):
    bad = [n for n in order if not status[n]]
    print('pass', it, 'failed', len(bad), flush=True)
    if not bad: break
    for n in bad:
        ps = PADS[n]
        x0 = min(p['x'] for p in ps) - 2; x1 = max(p['x'] for p in ps) + 2
        y0 = min(p['y'] for p in ps) - 2; y1 = max(p['y'] for p in ps) + 2
        j0, j1, i0, i1 = int(y0 / G), int(y1 / G), int(x0 / G), int(x1 / G)
        sub = owner[:, max(j0, 0):j1, max(i0, 0):i1]
        victims = [nets[k - 1] for k in np.unique(sub) if k > 0 and nets[k - 1] in status and nets[k - 1] != n
                   and status[nets[k - 1]] and nets[k - 1] not in hs[:0]]
        victims = [v for v in victims if v not in PLANE][:12]
        ripup(n)
        for v in victims: ripup(v)
        status[n] = run(n)
        for v in victims:
            status[v] = run(v)
# planes last: fanout vias from SMD pads, then the remaining plane connections
for n in ['+5V_CM5', '+5V_AUX', 'VIN_PROT', 'GND']:
    if n in PLANE:
        print('fanout', n, plane_fanout(n), '%.0fs' % (time.time() - t0), flush=True)
        status[n] = run(n)
bad = [n for n in status if not status[n]]
print('FINAL failed', len(bad), bad, flush=True)
json.dump(dict(tracks=[(n, l, [(a[2] + .5) * G, (a[1] + .5) * G], [(b[2] + .5) * G, (b[1] + .5) * G], w) for n, l, a, b, w in tracks],
               vias=vias, failed=failed), open(HERE + '/routes.json', 'w'))
print('tracks', len(tracks), 'vias', len(vias), 'failed', failed)
