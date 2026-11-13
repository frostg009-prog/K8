# -*- coding: utf-8 -*-
"""rev0.4 (KiCad python): current-path check. For each (net, source pad, load pad, current A) finds the widest path through
tracks/vias (max-bottleneck) and reports the bottleneck width and the IPC-2152 estimate of current for a 20 C rise
(outer layer 18 um + plating ~ 35 um).  python3 pathcheck.py board.kicad_pcb"""
import sys, math, heapq, collections
import pcbnew
b = pcbnew.LoadBoard(sys.argv[1]); TM = pcbnew.ToMM
CHECK = [  # net, from REF.pad, to REF.pad, design current A
    ('+5V_AUX', 'L_B2.2', 'U_VB4.5', 2.0), ('+5V_AUX', 'L_B2.2', 'U_VB2.5', 1.0), ('+5V_AUX', 'L_B2.2', 'U_VB3.5', 1.0),
    ('+5V_AUX', 'L_B2.2', 'J_FAN.1', 0.3), ('+5V_AUX', 'L_B2.2', 'J_GPS.1', 0.3), ('+5V_AUX', 'L_B2.2', 'J_THA.1', 0.5),
    ('+5V_AI', 'U_VB4.1', 'J_AIPWR.1', 2.0), ('+5V_AI', 'U_VB4.1', 'J_PCIE.1', 1.0),
    ('+5V_CM5', 'L_B1.2', 'M1.81', 5.0), ('+5V_CM5', 'L_B1.2', 'U_C33.4', 1.0), ('VIN_PROT', 'Q_RP.3', 'U_B2.2', 2.5),
    ('VIN_PROT', 'Q_RP.3', 'D_B1IN.2', 3.0), ('VSERVO', 'J_SPWR.1', 'J_S1.2', 2.0), ('VSERVO', 'J_SPWR.1', 'J_S4.2', 2.0),
    ('+3V3_CAM', 'L_C33.2', 'J_CAM1.22', 0.5), ('+3V3_CAM', 'L_C33.2', 'J_CAM2.22', 0.5),
]
PLANE_W = 6.0   # an In2 plane island counts as a 6 mm wide conductor (35 um inner copper is conservative: 18 um)


def amp(w_mm, inner=False):
    # IPC-2152 fit (external, 1 oz-equivalent ~35 um, 20 C rise): I = 0.0647 * dT^0.4281 * A^0.6732  (A in mil^2)
    t_mil = (0.018 if inner else 0.035) / 0.0254
    A = (w_mm / 0.0254) * t_mil
    return 0.0647 * 20 ** 0.4281 * A ** 0.6732


def graph(net):
    nodes = collections.defaultdict(list)
    def key(p, l):
        return (round(TM(p.x), 2), round(TM(p.y), 2), l)
    segs = []
    for t in b.GetTracks():
        if t.GetNetname() != net: continue
        if t.GetClass() == 'PCB_VIA':
            k = [key(t.GetPosition(), l) for l in ('F', 'B', 'I')]
            segs.append((k[0], k[1], 99)); segs.append((k[0], k[2], 99)); segs.append((k[1], k[2], 99))
        else:
            l = 'F' if t.GetLayer() == pcbnew.F_Cu else 'B'
            segs.append((key(t.GetStart(), l), key(t.GetEnd(), l), TM(t.GetWidth())))
    pads = {}
    for f in b.GetFootprints():
        for p in f.Pads():
            if p.GetNetname() != net: continue
            nm = '%s.%s' % (f.GetReference(), p.GetNumber())
            ls = ['F', 'B', 'I'] if p.GetAttribute() == pcbnew.PAD_ATTRIB_PTH else (['F'] if p.IsOnLayer(pcbnew.F_Cu) else ['B'])
            pads.setdefault(nm, []).append((p, ls))
    # pad <-> track endpoints touching the pad (99 = pad copper)
    for nm, lst in pads.items():
        for p, ls in lst:
            for (a, c, w) in list(segs):
                for e in (a, c):
                    if len(e) == 3 and e[2] in ls and p.HitTest(pcbnew.VECTOR2I(pcbnew.FromMM(e[0]), pcbnew.FromMM(e[1]))):
                        segs.append((('PAD', nm), e, 99))
            if 'I' in ls:
                segs.append((('PAD', nm), ('PLANE', net), PLANE_W))
    # vias / PTH that sit in this net's In2 island join the plane node
    for (a, c, w) in list(segs):
        for e in (a, c):
            if len(e) == 3 and isinstance(e[0], float) and e[2] == 'I':
                segs.append((e, ('PLANE', net), PLANE_W))
    for a, c, w in segs:
        nodes[a].append((c, w)); nodes[c].append((a, w))
    return nodes, pads


has_island = {z.GetNetname() for z in b.Zones() if z.GetLayer() == pcbnew.In2_Cu}
for net, s, d, I in CHECK:
    nodes, pads = graph(net)
    if net not in has_island:
        nodes.pop(('PLANE', net), None)
        for k in nodes: nodes[k] = [(c, w) for c, w in nodes[k] if c != ('PLANE', net)]
    src, dst = ('PAD', s), ('PAD', d)
    best = {src: 1e9}; cnt = 0; pq = [(-1e9, 0, src)]
    while pq:
        nw, _, n = heapq.heappop(pq); nw = -nw
        if n == dst: break
        for c, w in nodes.get(n, []):
            v = min(nw, w)
            if v > best.get(c, 0):
                best[c] = v; cnt += 1; heapq.heappush(pq, (-v, cnt, c))
    bw = best.get(dst, 0)
    cap = amp(bw) if bw < 50 else 99
    print('%-9s %-10s -> %-10s need %.1f A : bottleneck %s mm -> ~%.1f A  %s' % (net, s, d, I, ('%.2f' % bw) if bw else 'NOT CONNECTED', cap, 'OK' if cap >= I else 'LOW'))
