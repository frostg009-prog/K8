# -*- coding: utf-8 -*-
"""CM5-DETECT rev0.4 board generator (KiCad 9 python):  python3 build_rev04.py [out.kicad_pcb]
Builds the placed, un-routed board from design.py: outline 44 x 138 mm, Rezonit 4-layer stack-up,
explicit placement of every IC / connector / power part, pad-targeted placement of small passives,
net classes, inner-layer planes.  Routing is added by route04/ (diff pairs, autorouter, pours).
"""
import os, re, sys, math
import pcbnew
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
from design import C, NEAR, DIFF100, DIFF90, POWER_HI, POWER_MID

DX = 6.0                 # rev0.4b: board widened by DX; everything except the west-edge parts shifts right by DX
W, L = 44.0 + DX, 138.0
VIA = (0.45, 0.2)
FM = pcbnew.FromMM
TM = pcbnew.ToMM
V = lambda x, y: pcbnew.VECTOR2I(FM(x), FM(y))
LIBS = {'CM5IO': HERE + '/lib/CM5IO.pretty', 'lcsc': HERE + '/lib/lcsc.pretty', 'custom': HERE + '/lib/custom.pretty'}
MOD = (1.9 + DX, 12.4, 42.1 + DX, 67.6)          # CM5 module outline on the top side (no top parts under it)
MODHOLES = [(5.5 + DX, 16.0), (38.5 + DX, 16.0), (5.5 + DX, 64.0), (38.5 + DX, 64.0)]

# ------------------------------------------------------------------ explicit placement: ref -> (x, y, rot, side)
# connectors on a board edge are given as (x, y, opening direction, side): rotation is derived (pads inboard)
P = {
    # ---- top side
    'M1': (5.5, 64.0, 0, 'F'),
    'J_CAM1': (30.5, 5.0, 'N', 'F'), 'J_CAM2': (13.3, 5.0, 'N', 'F'),
    'J_USB1': (3.9, 75.5, 'W', 'F'), 'J_USB2': (40.1, 75.5, 'E', 'F'),
    'SW_BOOT': (13.0, 71.6, 0, 'F'), 'SW_PWR': (30.0, 71.6, 0, 'F'),
    'D_PWR': (18.5, 80.0, 0, 'F'), 'D_RUN': (22.0, 80.0, 0, 'F'), 'D_ERR': (25.5, 80.0, 0, 'F'),
    'L_B1': (9.0, 85.6, 180, 'F'), 'D_B1': (8.2, 92.4, 180, 'F'), 'U_B1': (16.0, 96.4, 0, 'F'), 'D_B1IN': (15.0, 104.4, 0, 'F'),
    'L_B2': (35.0, 103.9, 0, 'F'), 'D_B2': (35.8, 97.1, 0, 'F'), 'U_B2': (28.0, 93.1, 180, 'F'),
    'SC1': (26.4, 113.9, 180, 'F'), 'SC2': (26.4, 130.2, 180, 'F'),
    'J_BAT': (39.6, 121.0, 180, 'F'), 'C_BULK': (33.3, 112.6, 180, 'F'),
    'H1': (4.0, 122.05, 0, 'F'), 'H2': (41.3, 111.6, 0, 'F'), 'H3': (2.2, 4.0, 0, 'F'), 'H4': (41.8, 4.0, 0, 'F'),
    'H5': (2.4, 83.0, 0, 'F'), 'H6': (41.6, 83.0, 0, 'F'),
    # ---- bottom side: edge connectors
    'J_PCIE': (31.5, 4.6, 'N', 'B'), 'J_SD': (10.15, 23.4, 90, 'B'),
    'J_MATEK': (3.4, 41.4, 'W', 'B'), 'J_GPS': (3.4, 51.0, 'W', 'B'), 'J_I2C': (3.4, 90.35, 'W', 'B'),
    'J_IO': (3.4, 102.45, 'W', 'B'),
    'J_S1': (40.6, 22.1, 'E', 'B'), 'J_FAN': (40.6, 31.05, 'E', 'B'),
    'J_S2': (40.6, 40.0, 'E', 'B'), 'J_S3': (40.6, 48.4, 'E', 'B'), 'J_S4': (40.6, 56.8, 'E', 'B'),
    'J_THU': (40.6, 91.1, 'E', 'B'), 'J_SPWR': (40.6, 100.3, 'E', 'B'), 'J_RTC': (3.4, 114.0, 'W', 'B'),
    'J_THA': (7.6, 134.6, 'S', 'B'), 'J_AIPWR': (13.0, 3.4, 'N', 'B'),
    # ---- bottom side: under the module
    'U_C33': (19.0, 12.6, 0, 'B'), 'L_C33': (14.0, 12.6, 0, 'B'),
    'U_SD': (20.6, 22.0, 0, 'B'), 'U_SEC': (29.5, 27.0, 0, 'B'), 'U_TEMP': (29.5, 52.0, 0, 'B'),
    'U_MCU': (24.8, 41.0, 0, 'B'), 'U_AON': (14.5, 46.5, 0, 'B'),
    'Q_PMIC': (10.5, 55.5, 0, 'B'), 'Q_PWB': (10.5, 59.5, 0, 'B'),
    'JP_WDT': (31.6, 34.6, 0, 'B'), 
    # ---- bottom side: USB / switches
    'U_ESD1': (10.0, 72.5, 0, 'B'), 'U_ID1': (11.0, 77.0, 0, 'B'), 'U_ID2': (11.0, 81.0, 0, 'B'),
    'U_ESD2': (30.5, 72.5, 0, 'B'), 'U_VB2': (30.5, 78.5, 0, 'B'),
    'U_ESD3': (34.6, 96.6, 0, 'B'), 'U_VB3': (30.2, 96.6, 0, 'B'),
    # ---- bottom side: hold-up boost + charger (next to the supercap pins), battery input protection
    'L_HB': (20.4, 117.6, 180, 'B'), 'U_HB': (13.4, 117.6, 180, 'B'), 'U_CHG': (11.6, 124.6, 0, 'B'), 'D_CHG': (19.0, 124.2, 0, 'B'),
    'F1': (35.7, 128.3, 90, 'B'), 'Q_RP': (34.4, 111.4, 270, 'B'), 'D_TVS': (24.4, 105.4, 180, 'B'),
    'Q_AUX_OFF': (22.6, 86.5, 0, 'F'),
}
P.update({'FID1': (3.5, 40.0, 0, 'F'), 'FID2': (3.5, 62.0, 0, 'F'), 'FID3': (40.5, 86.5, 0, 'F'),
          'FID4': (21.0, 60.0, 0, 'B'), 'FID5': (27.0, 18.5, 0, 'B'), 'FID6': (27.0, 135.0, 0, 'B')})
WEST_FIXED = {'FID1', 'FID2', 'FID3', 'FID4', 'FID5', 'FID6', 'J_USB1', 'J_MATEK', 'J_GPS', 'J_I2C', 'J_IO', 'J_RTC', 'J_SD', 'H1', 'H3', 'H5'}
P = {k: (v if k in WEST_FIXED else (v[0] + DX,) + tuple(v[1:])) for k, v in P.items()}
GLOBAL = ('GND', '+5V_CM5', '+3V3_CM5', '+3V3_AON', '+5V_AUX', 'VIN_PROT')
# extra placement hints (ref -> 'REF.pad') on top of design.NEAR
HINT = dict(NEAR)
HINT.update({'TP_GND': 'U_MCU.7', 'TP_3V3': 'U_MCU.9', 'TP_5V': 'U_AON.1', 'TP_VIN': 'D_B1IN.2', 'TP_5VA': 'L_B2.2',
             'TP_SWIO': 'U_MCU.18', 'TP_RST': 'U_MCU.4', 'D_RPZ': 'Q_RP.1',
             'TP_SRVV': 'J_SPWR.1', 'JP_MATEK': 'J_MATEK.1', 'JP_SERVO': 'J_SPWR.2', 'U_VB4': 'J_AIPWR.1', 'TP_SRVG': 'J_SPWR.4', 'TP_AI5V': 'J_AIPWR.1', 'TP_AIGND': 'J_AIPWR.4'})


def load_fp(spec):
    lib, name = spec.split(':', 1)
    fp = pcbnew.FootprintLoad(LIBS.get(lib, '/usr/share/kicad/footprints/%s.pretty' % lib), name)
    if fp is None:
        raise SystemExit('footprint not found ' + spec)
    return fp


def cy_box(fp):
    """courtyard bbox (falls back to pads+fab bbox) in mm"""
    for lay in (pcbnew.F_CrtYd, pcbnew.B_CrtYd):
        c = fp.GetCourtyard(lay)
        if c.OutlineCount():
            b = c.BBox()
            return [TM(b.GetX()), TM(b.GetY()), TM(b.GetRight()), TM(b.GetBottom())]
    b = fp.GetBoundingBox(False)
    return [TM(b.GetX()), TM(b.GetY()), TM(b.GetRight()), TM(b.GetBottom())]


def occ_box(fp):
    """courtyard united with the pad copper (some vendor footprints have a courtyard smaller than their pads)"""
    bb = cy_box(fp)
    for p in fp.Pads():
        b = p.GetBoundingBox()
        bb = [min(bb[0], TM(b.GetX()) - 0.1), min(bb[1], TM(b.GetY()) - 0.1), max(bb[2], TM(b.GetRight()) + 0.1), max(bb[3], TM(b.GetBottom()) + 0.1)]
    return bb


def put(fp, x, y, rot, side):
    if side == 'B' and not fp.IsFlipped():
        fp.Flip(fp.GetPosition(), False)
    fp.SetOrientationDegrees(rot)
    fp.SetPosition(V(x, y))
    fp.BuildCourtyardCaches()


def padpos(fp, num):
    pts = [(TM(p.GetPosition().x), TM(p.GetPosition().y)) for p in fp.Pads() if p.GetNumber() == num]
    return (sum(p[0] for p in pts) / len(pts), sum(p[1] for p in pts) / len(pts)) if pts else None


def main(out):
    B = pcbnew.BOARD()
    B.SetCopperLayerCount(4)
    ds = B.GetDesignSettings()
    ds.SetBoardThickness(FM(1.5))
    ds.m_TrackMinWidth = FM(0.1); ds.m_MinClearance = FM(0.1); ds.m_ViasMinSize = FM(0.4); ds.m_MinThroughDrill = FM(0.2)
    ds.m_CopperEdgeClearance = FM(0.3); ds.m_HoleClearance = FM(0.2); ds.m_HoleToHoleMin = FM(0.25)
    ds.m_ViasMinAnnularWidth = FM(0.1)
    for a, b in zip([(0, 0), (W, 0), (W, L), (0, L)], [(W, 0), (W, L), (0, L), (0, 0)]):
        s = pcbnew.PCB_SHAPE(B); s.SetShape(pcbnew.SHAPE_T_SEGMENT); s.SetStart(V(*a)); s.SetEnd(V(*b))
        s.SetLayer(pcbnew.Edge_Cuts); s.SetWidth(FM(0.1)); B.Add(s)
    nets = {}

    def net(n):
        if n not in nets:
            ni = pcbnew.NETINFO_ITEM(B, n); B.Add(ni); nets[n] = ni
        return nets[n]

    occ = {'F': [], 'B': []}       # (x0,y0,x1,y1,ref)

    def overlaps(side, r, m=0.12):
        for o in occ[side]:
            if r[0] < o[2] + m and r[2] > o[0] - m and r[1] < o[3] + m and r[3] > o[1] - m:
                return o[4]
        return None

    placed = {}
    for ref in C:
        c = C[ref]
        fp = load_fp(c['fp'])
        fp.SetReference(ref); fp.SetValue(c['val'][:40])
        if hasattr(fp, 'SetField'):
            fp.SetField('LCSC', c['lcsc'])
        if c.get('dnp'):
            fp.SetDNP(True); fp.SetExcludedFromBOM(True); fp.SetExcludedFromPosFiles(True)
        B.Add(fp)
        placed[ref] = fp
    errors = []
    # ---- explicit parts
    for ref, (x, y, rot, side) in P.items():
        fp = placed[ref]
        if isinstance(rot, str):      # edge connector: choose the rotation that puts the signal pads inboard
            want = {'N': (0, 1), 'S': (0, -1), 'W': (1, 0), 'E': (-1, 0)}[rot]
            best = None
            for r in (0, 90, 180, 270):
                put(fp, x, y, r, side)
                sig = [p for p in fp.Pads() if p.GetNumber() not in ('MP', '', '13', '14') and p.GetAttribute() == pcbnew.PAD_ATTRIB_SMD]
                cx = sum(TM(p.GetPosition().x) for p in sig) / len(sig) - x
                cyy = sum(TM(p.GetPosition().y) for p in sig) / len(sig) - y
                sc = cx * want[0] + cyy * want[1]
                if best is None or sc > best[0]:
                    best = (sc, r)
            rot = best[1]
        put(fp, x, y, rot, side)
        P[ref] = (x, y, rot, side)
        bb = occ_box(fp)
        th = any(p.GetAttribute() == pcbnew.PAD_ATTRIB_PTH for p in fp.Pads())
        if not ref.startswith('H') and ref != 'M1':
            o = overlaps(side, bb, 0.0)
            if o:
                errors.append('OVERLAP %s / %s on %s' % (ref, o, side))
        if ref == 'M1':
            occ['F'].append(list(MOD) + ['M1'])
        elif ref.startswith('H'):
            for s_ in 'FB':
                occ[s_].append([x - 2.5, y - 2.5, x + 2.5, y + 2.5, ref])      # cap-head screw dia 4.5 + courtyard
        else:
            occ[side].append(bb + [ref])
        if th and ref != 'M1' and not ref.startswith('H'):          # through-hole pads block the other side too
            for p in fp.Pads():
                if p.GetAttribute() in (pcbnew.PAD_ATTRIB_PTH, pcbnew.PAD_ATTRIB_NPTH):
                    px, py = TM(p.GetPosition().x), TM(p.GetPosition().y)
                    r = max(TM(p.GetSizeX()), TM(p.GetSizeY()), TM(p.GetDrillSizeX())) / 2 + 0.35
                    occ['B' if side == 'F' else 'F'].append([px - r, py - r, px + r, py + r, ref + '.pin'])
    for x, y in MODHOLES:          # stand-off / nut of the CM5 screws on both sides
        for s_ in 'FB':
            occ[s_].append([x - 3.2, y - 3.2, x + 3.2, y + 3.2, 'M1.hole'])   # bare ring dia 6.1 for the stand-off
    # routing channels kept free of auto-placed parts (bottom side): PCIe bus, USB1 pair corridor
    for side_, box in KEEP:
        occ[side_].append(list(box))
    # ---- auto place small parts next to the pad they belong to
    def target_of(ref):
        if ref in HINT:
            r, pd = HINT[ref].split('.')
            return r, pd
        c = C[ref]
        cands = []
        for mynet in c['pins'].values():
            if not mynet or mynet in GLOBAL:
                continue
            for r2 in P:
                for pd, n2 in C[r2]['pins'].items():
                    if n2 == mynet:
                        pri = 0 if r2.startswith(('U_', 'Q_')) else (3 if r2 == 'M1' else (1 if r2.startswith(('L_', 'D_', 'SC', 'SW', 'JP')) else 2))
                        cands.append((pri, r2, pd))
        if cands:
            cands.sort(); return cands[0][1], cands[0][2]
        return None

    todo = [r for r in C if r not in P]
    # nets of passives that only meet other passives: resolve after their neighbours are placed
    pending, guard = list(todo), 0
    while pending and guard < 6:
        guard += 1
        nxt = []
        for ref in pending:
            t = target_of(ref)
            if t is None:
                nxt.append(ref); continue
            tr, tpd = t
            tfp = placed[tr]
            tp = padpos(tfp, tpd)
            if tp is None:
                raise SystemExit('no pad %s.%s for %s' % (tr, tpd, ref))
            tside = P[tr][3]
            if tr == 'M1':
                side = 'B'
            elif tr.startswith(('SC', 'J_BAT')):
                side = 'B'
            else:
                side = tside
            if side == 'F' and MOD[0] < tp[0] < MOD[2] and MOD[1] < tp[1] < MOD[3]:
                side = 'B'
            fp = placed[ref]
            c = C[ref]
            mynet = C[tr]['pins'].get(tpd)
            mypad = [pd for pd, n in c['pins'].items() if n == mynet]
            best = None
            rads = [0.0] + [i * 0.25 for i in range(1, 64)]
            for rad in rads:
                if best is not None and rad > best[0] + 1.2:
                    break
                steps = 1 if rad == 0 else max(8, int(rad * 14))
                for k in range(steps):
                    a = 2 * math.pi * k / steps
                    x, y = tp[0] + rad * math.cos(a), tp[1] + rad * math.sin(a)
                    for rot in (0, 90, 180, 270):
                        put(fp, x, y, rot, side)
                        bb = occ_box(fp)
                        if bb[0] < 0.7 or bb[1] < 0.7 or bb[2] > W - 0.7 or bb[3] > L - 0.7:
                            continue
                        if overlaps(side, bb):
                            continue
                        if mypad:
                            pp = padpos(fp, mypad[0]); cost = math.hypot(pp[0] - tp[0], pp[1] - tp[1])
                        else:
                            cost = rad
                        if best is None or cost < best[0] - 1e-6:
                            best = (cost, x, y, rot)
            if best is None:
                errors.append('COULD NOT PLACE ' + ref); continue
            put(fp, best[1], best[2], best[3], side)
            occ[side].append(occ_box(fp) + [ref])
            P[ref] = (round(best[1], 3), round(best[2], 3), best[3], side)
        pending = nxt
    for ref in pending:
        errors.append('NO TARGET ' + ref)
    for fp in placed.values():
        for pad in fp.Pads():
            if pad.GetAttribute() == pcbnew.PAD_ATTRIB_PTH and pad.GetNumber() == '' and pad.GetSizeX() <= pad.GetDrillSizeX() + FM(0.15):
                pad.SetAttribute(pcbnew.PAD_ATTRIB_NPTH); pad.SetLayerSet(pad.UnplatedHoleMask())
    # ---- silkscreen
    LABEL = {'J_CAM1': 'CAM1 day', 'J_CAM2': 'CAM2 night', 'J_PCIE': 'AI PCIe', 'J_USB1': 'USB PC/FW', 'J_USB2': 'USB HOST',
             'J_BAT': 'BAT 3-6S', 'J_SD': 'microSD', 'J_S1': 'S1', 'J_S2': 'S2', 'J_S3': 'S3', 'J_S4': 'S4',
             'J_SPWR': 'SERVO PWR', 'J_MATEK': 'MATEK', 'J_GPS': 'GPS', 'J_I2C': 'I2C', 'J_IO': 'GPIO', 'J_THU': 'TH USB',
             'J_THA': 'TH AUX', 'J_FAN': 'FAN', 'J_AIPWR': 'AI 5V', 'J_RTC': 'RTC', 'SW_BOOT': 'BOOT', 'SW_PWR': 'PWR',
             'D_PWR': 'PWR', 'D_RUN': 'RUN', 'D_ERR': 'ERR', 'JP_WDT': 'WDT OFF', 'JP_SERVO': 'S=5V', 'JP_MATEK': 'M 5V'}
    for ref, fp in placed.items():
        fp.Value().SetVisible(False)
        for f in fp.GetFields():
            if f.GetName() not in ('Reference', 'Value'):
                f.SetVisible(False)
        rt = fp.Reference(); rt.SetTextSize(V(1.0, 1.0)); rt.SetTextThickness(FM(0.15))
        rt.SetVisible(False)                 # references live on the Fab layer drawings; silk carries only the labels below
    # ---- 3D models for parts without vendor models
    MODELS = {'M1': ('CM5_with_cooler', (0, 0, 0)), 'J_USB1': ('USB_C_receptacle', (0, -0.5, 0)), 'J_USB2': ('USB_C_receptacle', (0, -0.5, 0)),
              'L_B1': ('Inductor_7x6', (0, 0, 0)), 'L_B2': ('Inductor_7x6', (0, 0, 0)), 'U_B1': ('SOP8_EP', (0, 0, 0)), 'U_B2': ('SOP8_EP', (0, 0, 0)),
              'SC1': ('SuperCap_D10_L20', (0, 0, 0)), 'SC2': ('SuperCap_D10_L20', (0, 0, 0)), 'F1': ('Fuse_2410', (0, 0, 0)), 'J_BAT': ('XT60PW', (0, 0, 0))}
    for ref, (m, off) in MODELS.items():
        fp = placed[ref]
        if ref != 'M1':
            fp.Models().clear()
        md = pcbnew.FP_3DMODEL(); md.m_Filename = '${KIPRJMOD}/lib/gen3d/%s.wrl' % m; md.m_Offset = pcbnew.VECTOR3D(*off)
        fp.Models().push_back(md)
    # ---- nets
    for ref, c in C.items():
        fp = placed[ref]
        for pad in fp.Pads():
            num = pad.GetNumber()
            n = c['pins'].get(num)
            if n is None and num.startswith('MP'):
                n = c['pins'].get('MP')
            if n:
                pad.SetNet(net(n))
    # ---- net classes
    ns = ds.m_NetSettings

    def ncls(name, w, clr, dpw=None, dpg=None, via=None):
        via = via or VIA
        nc = pcbnew.NETCLASS(name)
        nc.SetTrackWidth(FM(w)); nc.SetClearance(FM(clr)); nc.SetViaDiameter(FM(via[0])); nc.SetViaDrill(FM(via[1]))
        if dpw:
            nc.SetDiffPairWidth(FM(dpw)); nc.SetDiffPairGap(FM(dpg))
        ns.SetNetclass(name, nc)
    dflt = ns.GetDefaultNetclass(); dflt.SetTrackWidth(FM(0.15)); dflt.SetClearance(FM(0.125)); dflt.SetViaDiameter(FM(VIA[0])); dflt.SetViaDrill(FM(VIA[1]))
    ncls('DIFF100', 0.13, 0.125, 0.13, 0.17)
    ncls('DIFF90', 0.17, 0.125, 0.17, 0.15)
    ncls('PWR_HI', 0.8, 0.15, via=(0.6, 0.3))      # <= 25 V: 0.15 mm is ample (IPC-2221B, external, coated)
    ncls('PWR_MID', 0.4, 0.15, via=(0.6, 0.3))
    ncls('PLANE', 0.3, 0.15, via=(0.6, 0.3))
    for n in DIFF100: ns.SetNetclassPatternAssignment(n, 'DIFF100')
    for n in DIFF90: ns.SetNetclassPatternAssignment(n, 'DIFF90')
    PLANES = ('GND', '+5V_CM5', 'VIN_PROT')
    for n in POWER_HI:
        if n not in PLANES: ns.SetNetclassPatternAssignment(n, 'PWR_HI')
    for n in PLANES: ns.SetNetclassPatternAssignment(n, 'PLANE')
    for n in POWER_MID: ns.SetNetclassPatternAssignment(n, 'PWR_MID')

    def zone(netname, layer, pts, prio=0, clr=0.25):
        z = pcbnew.ZONE(B); z.SetLayer(layer); z.SetNet(net(netname)); z.SetAssignedPriority(prio)
        z.SetLocalClearance(FM(clr)); z.SetMinThickness(FM(0.2)); z.SetThermalReliefGap(FM(0.25)); z.SetThermalReliefSpokeWidth(FM(0.4))
        z.SetPadConnection(pcbnew.ZONE_CONNECTION_FULL)
        z.SetIslandRemovalMode(pcbnew.ISLAND_REMOVAL_MODE_ALWAYS)
        ol = z.Outline(); ol.NewOutline()
        for x, y in pts: ol.Append(FM(x), FM(y))
        B.Add(z); return z
    full = [(0.3, 0.3), (W - 0.3, 0.3), (W - 0.3, L - 0.3), (0.3, L - 0.3)]
    zone('GND', pcbnew.In1_Cu, full)                      # solid reference plane under the top layer
    zone('GND', pcbnew.In2_Cu, full)
    for name, pts in PLANE_ISLANDS.items():
        zone(name, pcbnew.In2_Cu, pts, 1)
    B.Save(out)
    print('saved', out, len(C), 'footprints', len(nets), 'nets')
    for e in errors:
        print('!!', e)
    return errors


# In2 power islands (the rest of In2 is GND). High-speed pairs on the bottom layer never cross an island edge.
PLANE_ISLANDS0 = {
    '+5V_CM5': [(0.6, 44.0), (16.5, 44.0), (16.5, 131.0), (0.6, 131.0)],
    '+5V_AUX': [(36.3, 34.0), (43.4, 34.0), (43.4, 108.0), (36.3, 108.0), (36.3, 93.5), (39.5, 93.5), (39.5, 88.0), (36.3, 88.0)],
    'VIN_PROT': [(17.5, 84.5), (33.5, 84.5), (33.5, 103.0), (39.0, 103.0), (39.0, 109.0), (17.5, 109.0)],
}
# routing corridors kept free of auto-placed parts: (side, [x0, y0, x1, y1, name])
# fan-out via bands of the CM5 GPIO connector (both sides kept free of parts): x already includes DX
FANOUT_BANDS = [(6.9 + 0.0, 31.8, 9.1, 53.2), (12.95, 31.8, 15.15, 53.2)]
KEEP0 = [
    ('B', [18.2, 30.4, 37.3, 32.6, 'USB1.bot']), ('B', [18.2, 30.4, 20.2, 72.5, 'USB1.bot']),
    ('F', [6.9, 74.3, 20.2, 75.7, 'USB1.top']), ('F', [18.2, 68.0, 20.2, 75.7, 'USB1.top']),
    ('B', [34.0, 44.0, 35.6, 92.5, 'THU.bot']), ('B', [34.0, 88.5, 37.5, 92.5, 'THU.bot']),
    ('F', [35.2, 67.8, 43.6, 69.6, 'USB2.top']), ('F', [35.2, 67.8, 37.0, 76.0, 'USB2.top']),
    ('F', [27.5, 7.7, 37.4, 12.3, 'CAM1.top']), ('F', [9.2, 7.7, 28.0, 19.5, 'CAM2.top']), ('F', [40.9, 10.0, 43.7, 12.4, 'PCIE.top']),
    ('B', [28.0, 7.2, 43.6, 14.6, 'PCIE.bot']), ('F', [12.8, 83.4, 17.2, 88.6, 'B1_SW']), ('F', [26.8, 100.9, 31.2, 106.1, 'B2_SW']),
]

PLANE_ISLANDS = {k: [((x + DX) if x > 1.0 else x, y) for x, y in v] for k, v in PLANE_ISLANDS0.items()}
KEEP = [(sd, [b[0] + DX, b[1], b[2] + DX, b[3], b[4]]) for sd, b in KEEP0]
KEEP += [(sd, [x0, y0, x1, y1, 'CM5.fanout']) for sd in 'FB' for x0, y0, x1, y1 in FANOUT_BANDS]

if __name__ == '__main__':
    errs = main(sys.argv[1] if len(sys.argv) > 1 else HERE + '/CM5-DETECT_rev04_placed.kicad_pcb')
    sys.exit(1 if errs else 0)
