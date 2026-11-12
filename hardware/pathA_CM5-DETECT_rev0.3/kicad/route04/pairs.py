# -*- coding: utf-8 -*-
"""rev0.4 step 2 (KiCad python): hand-planned differential pairs, locked so the autorouter keeps them.
   python3 pairs.py placed.kicad_pcb out.kicad_pcb
All pairs are planar (no crossings, no polarity swaps): see docs/AUDIT_rev0.4.md for the channel plan.
"""
import sys, math, json
import pcbnew
FM = pcbnew.FromMM; TM = pcbnew.ToMM
src, out = sys.argv[1:3]
B = pcbnew.LoadBoard(src)
LAY = {'F': pcbnew.F_Cu, 'B': pcbnew.B_Cu}
PAD = {}
for fp in B.GetFootprints():
    for p in fp.Pads():
        if p.GetNetname():
            PAD[(fp.GetReference(), p.GetNumber())] = (TM(p.GetPosition().x), TM(p.GetPosition().y))
LEN = {}


def seg(net, layer, a, b, w):
    if math.hypot(a[0] - b[0], a[1] - b[1]) < 1e-4:
        return
    t = pcbnew.PCB_TRACK(B); t.SetStart(pcbnew.VECTOR2I(FM(a[0]), FM(a[1]))); t.SetEnd(pcbnew.VECTOR2I(FM(b[0]), FM(b[1])))
    t.SetWidth(FM(w)); t.SetLayer(LAY[layer]); t.SetNet(B.FindNet(net)); t.SetLocked(True); B.Add(t)
    LEN[net] = LEN.get(net, 0) + math.hypot(a[0] - b[0], a[1] - b[1])


def via(net, p, dia=0.45, drill=0.2):
    v = pcbnew.PCB_VIA(B); v.SetPosition(pcbnew.VECTOR2I(FM(p[0]), FM(p[1]))); v.SetWidth(pcbnew.F_Cu, FM(dia)); v.SetDrill(FM(drill))
    v.SetNet(B.FindNet(net)); v.SetLocked(True); B.Add(v)
    LEN[net] = LEN.get(net, 0) + 1.5


def poly(net, layer, pts, w):
    for a, b in zip(pts, pts[1:]):
        seg(net, layer, a, b, w)


def offset(pts, d):
    """parallel polyline at signed distance d to the LEFT of the travel direction (mitred corners)"""
    n = len(pts); res = []
    dirs = []
    for a, b in zip(pts, pts[1:]):
        l = math.hypot(b[0] - a[0], b[1] - a[1]); dirs.append(((b[0] - a[0]) / l, (b[1] - a[1]) / l))
    left = lambda u: (u[1], -u[0])          # screen coords (y down): left of travel direction
    for i in range(n):
        if i == 0:
            nx, ny = left(dirs[0]); res.append((pts[0][0] + nx * d, pts[0][1] + ny * d))
        elif i == n - 1:
            nx, ny = left(dirs[-1]); res.append((pts[-1][0] + nx * d, pts[-1][1] + ny * d))
        else:
            n1, n2 = left(dirs[i - 1]), left(dirs[i])
            bx, by = n1[0] + n2[0], n1[1] + n2[1]
            k = d / (1 + n1[0] * n2[0] + n1[1] * n2[1])
            res.append((pts[i][0] + bx * k, pts[i][1] + by * k))
    return res


def pair(left_net, right_net, layer, center, w, gap, pre=None, post=None):
    """route both nets along `center`; left_net runs on the left of the travel direction.
    pre/post: {net: [points]} explicit lead-in (pad -> start) and lead-out (end -> pad) polylines"""
    d = (w + gap) / 2
    for net, sgn in ((left_net, 1), (right_net, -1)):
        pts = offset(center, sgn * d)
        if pre and net in pre:
            pts = list(pre[net]) + pts
        if post and net in post:
            pts = pts + list(post[net])
        poly(net, layer, pts, w)
        yield net, pts[0], pts[-1]


def run(*a, **k):
    return {n: (s, e) for n, s, e in pair(*a, **k)}


DX = 6.0      # board widened in rev0.4b: CM5 and everything right of it moved +DX
W100, G100 = 0.13, 0.17
W90, G90 = 0.17, 0.15
DV = 0.29            # half distance between the two vias of a pair (0.45 mm vias, 0.13 mm gap)

# ---------------------------------------------------------------- CAM1 (top layer, CM5 inner row -> west -> north)
#   bus order west->east: D3 D2 C D1 D0, N east of P in every pair (matches FH12 pins, no swaps)
for lane, yc, xc, pn, pp, cn, cp in [('D0', 35.7, 35.0, '115', '117', '2', '3'), ('D1', 36.9, 33.5, '121', '123', '5', '6'),
                                     ('C', 38.1, 32.0, '127', '129', '8', '9'), ('D2', 39.3, 30.5, '133', '135', '11', '12'),
                                     ('D3', 40.5, 29.0, '139', '141', '14', '15')]:
    N, P = 'CAM1_%s_N' % lane, 'CAM1_%s_P' % lane
    xc = (PAD[('J_CAM1', cn)][0] + PAD[('J_CAM1', cp)][0]) / 2
    c = [(36.75 + DX, yc), (xc + 0.6, yc), (xc, yc - 0.6), (xc, 8.35)]
    # heading west: N is the northern (right-hand) track
    run(P, N, 'F', c, W100, G100,
        pre={N: [PAD[('M1', pn)]], P: [PAD[('M1', pp)]]},
        post={N: [(xc + 0.25, 7.95), PAD[('J_CAM1', cn)]], P: [(xc - 0.25, 7.95), PAD[('J_CAM1', cp)]]})
# ---------------------------------------------------------------- CAM2 (top layer)
CAM2_S, CAM2_YJ = 8.0, 10.6
for lane, yc, xc, pn, pp, cn, cp in [('D0', 47.7, 16.5, '175', '177', '2', '3'), ('D1', 48.9, 15.0, '181', '183', '5', '6'),
                                     ('C', 50.1, 13.5, '187', '189', '8', '9'), ('D2', 51.3, 12.0, '193', '195', '11', '12')]:
    N, P = 'CAM2_%s_N' % lane, 'CAM2_%s_P' % lane
    xc = (PAD[('J_CAM2', cn)][0] + PAD[('J_CAM2', cp)][0]) / 2
    xv = xc + CAM2_S        # vertical run shifted east: keeps the CM5 GPIO pocket open for escapes
    c = [(36.75 + DX, yc), (xv + 0.6, yc), (xv, yc - 0.6), (xv, CAM2_YJ + CAM2_S), (xc, CAM2_YJ), (xc, 8.35)]
    run(P, N, 'F', c, W100, G100,
        pre={N: [PAD[('M1', pn)]], P: [PAD[('M1', pp)]]},
        post={N: [(xc + 0.25, 7.95), PAD[('J_CAM2', cn)]], P: [(xc - 0.25, 7.95), PAD[('J_CAM2', cp)]]})
# CAM2 D3 sits on the outer row: leave through the channel between the two pad rows, round the connector end
N, P = 'CAM2_D3_N', 'CAM2_D3_P'
xc = (PAD[('J_CAM2', '14')][0] + PAD[('J_CAM2', '15')][0]) / 2
xv = xc + CAM2_S
c = [(39.4 + DX, 51.75), (39.4 + DX, 52.6), (39.0 + DX, 53.0), (xv + 0.6, 53.0), (xv, 52.4), (xv, CAM2_YJ + CAM2_S), (xc, CAM2_YJ), (xc, 8.35)]
# heading south in the channel: P east (left of travel), N west
pN, pP = PAD[('M1', '194')], PAD[('M1', '196')]
run(P, N, 'F', c, W100, G100,
    pre={N: [pN, (39.25 + DX, pN[1])], P: [pP, (39.55 + DX, pP[1])]},
    post={N: [(xc + 0.25, 7.95), PAD[('J_CAM2', '14')]], P: [(xc - 0.25, 7.95), PAD[('J_CAM2', '15')]]})
# ---------------------------------------------------------------- PCIe (top: east strip north; vias; bottom: west, north to FFC)
for name, yp, x0, xs, yv, yw, pinp, pinn, cp, cn in [('CLK', 34.5, 41.77, 41.385, 13.5, 12.7, '110', '112', '4', '5'),
                                                     ('RX', 35.7, 42.52, 42.285, 12.5, 11.7, '116', '118', '7', '8'),
                                                     ('TX', 36.9, 43.27, 43.185, 11.5, 10.7, '122', '124', '10', '11')]:
    P, N = 'PCIE_%s_P' % name, 'PCIE_%s_N' % name
    x0, xs = x0 + DX, xs + DX
    xd = (PAD[('J_PCIE', cp)][0] + PAD[('J_PCIE', cn)][0]) / 2
    yj = {'CLK': 14.75, 'RX': 14.3, 'TX': 14.0}[name]      # staggered jogs keep the pair-to-pair gap
    c = [(41.0 + DX, yp), (x0 - 0.35, yp), (x0, yp - 0.35), (x0, yj), (xs, yj - (x0 - xs)), (xs, yv + 0.5)]
    # heading east: P is the northern (left-hand) track; after the left turn P runs on the west
    e = run(P, N, 'F', c, W100, G100, pre={P: [PAD[('M1', pinp)]], N: [PAD[('M1', pinn)]]},
            post={P: [(xs - DV, yv)], N: [(xs + DV, yv)]})
    via(P, (xs - DV, yv)); via(N, (xs + DV, yv))
    c = [(xs, yv - 0.45), (xs, yw + 0.35), (xs - 0.35, yw), (xd + 0.5, yw), (xd, yw - 0.5), (xd, 7.75)]
    run(P, N, 'B', c, W100, G100, pre={P: [(xs - DV, yv)], N: [(xs + DV, yv)]},
        post={P: [(xd - 0.25, 7.35), PAD[('J_PCIE', cp)]], N: [(xd + 0.25, 7.35), PAD[('J_PCIE', cn)]]})
# ---------------------------------------------------------------- USB2 host (CM5 USB3-0 D+/D-): top layer only
P, N = 'USB2_DP', 'USB2_DN'
pP, pN = PAD[('M1', '134')], PAD[('M1', '136')]
c = [(x + DX, y) for x, y in [(41.1, 39.3), (41.45, 39.3), (41.8, 39.65), (41.8, 68.2), (41.4, 68.6), (36.6, 68.6), (36.2, 69.0), (36.2, 74.6), (36.6, 75.0), (36.95, 75.0)]]
# heading east: DP north = left
run(P, N, 'F', c, W90, G90, pre={P: [pP], N: [pN]}, post={P: [PAD[('J_USB2', 'B6')]], N: [PAD[('J_USB2', 'A7')]]})
# ---------------------------------------------------------------- USB1 device (CM5 USB2 OTG): top stub, bottom run, top landing
P, N = 'USB1_DP', 'USB1_DN'
pN, pP = PAD[('M1', '103')], PAD[('M1', '105')]
xv, yv = 36.3 + DX, 32.15
# heading north: DN east (right), DP west (left)
poly(N, 'F', [pN, (xv + 0.16, pN[1]), (xv + 0.16, yv + 0.45), (xv + DV, yv)], W90)
poly(P, 'F', [pP, (xv - 0.16, pP[1]), (xv - 0.16, yv + 0.45), (xv - DV, yv)], W90)
via(P, (xv - DV, yv)); via(N, (xv + DV, yv))
x2 = 19.2 + DX
c = [(xv, yv - 0.45), (xv, 31.3), (xv - 0.4, 30.9), (x2 + 0.4, 30.9), (x2, 31.3), (x2, 71.0)]
run(P, N, 'B', c, W90, G90, pre={P: [(xv - DV, yv)], N: [(xv + DV, yv)]}, post={P: [(x2 + DV, 71.45)], N: [(x2 - DV, 71.45)]})
via(P, (x2 + DV, 71.45)); via(N, (x2 - DV, 71.45))
# heading south: DP east (left)
c = [(x2, 71.9), (x2, 74.6), (x2 - 0.4, 75.0), (6.95, 75.0)]
run(P, N, 'F', c, W90, G90, pre={P: [(x2 + DV, 71.45)], N: [(x2 - DV, 71.45)]},
    post={P: [PAD[('J_USB1', 'A6')]], N: [PAD[('J_USB1', 'B7')]]})
# ---------------------------------------------------------------- thermal camera USB (CM5 USB3-1 D+/D-): via at the pads, bottom run
P, N = 'THU_DP', 'THU_DN'
pP, pN = PAD[('M1', '163')], PAD[('M1', '165')]
xv = 36.35 + DX
poly(P, 'F', [pP, (36.9 + DX, pP[1]), (xv, 45.3 - DV)], W90)
poly(N, 'F', [pN, (36.9 + DX, pN[1]), (xv, 45.3 + DV)], W90)
via(P, (xv, 45.3 - DV)); via(N, (xv, 45.3 + DV))
xs = 34.8 + DX
c = [(xv - 0.45, 45.3), (xs + 0.4, 45.3), (xs, 45.7), (xs, 90.7), (xs + 0.4, 91.1), (37.0 + DX, 91.1)]
# heading west: DP north = right
run(N, P, 'B', c, W90, G90, pre={P: [(xv, 45.3 - DV)], N: [(xv, 45.3 + DV)]},
    post={P: [(37.5 + DX, PAD[('J_THU', '3')][1]), PAD[('J_THU', '3')]], N: [(37.5 + DX, PAD[('J_THU', '2')][1]), PAD[('J_THU', '2')]]})
B.Save(out)
rep = {}
for n in sorted(LEN):
    rep[n] = round(LEN[n], 2)
json.dump(rep, open(out.replace('.kicad_pcb', '_lengths.json'), 'w'), indent=1)
pairs = {}
for n, l in rep.items():
    pairs.setdefault(n[:-2], {})[n[-1]] = l
for k, v in sorted(pairs.items()):
    a, b = list(v.values())
    print('%-10s %7.2f %7.2f  skew %.2f mm' % (k, a, b, abs(a - b)))
