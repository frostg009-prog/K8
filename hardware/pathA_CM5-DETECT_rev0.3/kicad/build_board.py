# -*- coding: utf-8 -*-
"""Build CM5-DETECT rev0.3 PCB from design.py: outline, stack-up (Rezonit 4L 1.5 mm), placement, nets, rules.
Run with the KiCad python:  /usr/bin/python3 build_board.py  -> CM5-DETECT_rev03_placed.kicad_pcb
"""
import os, re, sys, math
import pcbnew
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from design import C, DIFF100, DIFF90, POWER_HI, POWER_MID

HERE = os.path.dirname(os.path.abspath(__file__))
W, L = 44.0, 134.0
FM = pcbnew.FromMM
V = lambda x, y: pcbnew.VECTOR2I(FM(x), FM(y))
LIBS = {'CM5IO': HERE + '/lib/CM5IO.pretty', 'lcsc': HERE + '/lib/lcsc.pretty', 'custom': HERE + '/lib/custom.pretty'}

# ---------------------------------------------------------------- fixed placement (x, y, rot, side)  side: F/B
P = {
    'M1': (5.5, 64.0, 0, 'F'),
    'J_CAM1': (32.0, 5.0, 180, 'F'), 'J_CAM2': (12.0, 5.0, 180, 'F'),
    'J_PCIE': (22.0, 4.6, 180, 'B'),
    # below CM5, top side
    'SW_BOOT': (13.5, 74.0, 0, 'F'), 'SW_PWR': (30.5, 74.0, 0, 'F'),
    'D_PWR': (18.8, 76.8, 0, 'F'), 'D_RUN': (22.0, 76.8, 0, 'F'), 'D_ERR': (25.2, 76.8, 0, 'F'),
    'J_USB1': (3.9, 73.2, 270, 'F'), 'J_USB2': (40.1, 73.2, 90, 'F'),
    'U_B1': (7.0, 86.0, 0, 'F'), 'L_B1': (16.5, 86.0, 90, 'F'), 'D_B1': (7.0, 94.0, 0, 'F'), 'D_B1IN': (17.0, 96.5, 0, 'F'),
    'U_B2': (37.0, 86.0, 0, 'F'), 'L_B2': (27.5, 86.0, 90, 'F'), 'D_B2': (36.0, 94.0, 0, 'F'),
    'J_BAT': (39.6, 117.0, 180, 'F'), 'J_BAT2': (9.5, 119.0, 180, 'F'),
    'F1': (23.5, 118.0, 90, 'F'), 'D_TVS': (16.5, 112.5, 0, 'B'), 'Q_RP': (36.0, 128.0, 0, 'B'),
    'C_BULK': (24.0, 128.0, 0, 'B'),
    # bottom side
    'J_SD': (9.3, 26.6, 90, 'B'),
    'J_S1': (40.6, 22.4, 270, 'B'), 'J_S2': (40.6, 31.6, 270, 'B'), 'J_S3': (40.6, 57.5, 270, 'B'), 'J_S4': (40.6, 89.0, 270, 'B'),
    'J_SPWR': (40.6, 98.5, 270, 'B'),
    'J_MATEK': (3.4, 57.5, 90, 'B'), 'J_GPS': (3.4, 89.0, 90, 'B'), 'J_I2C': (3.4, 99.0, 90, 'B'),
    'J_IO': (3.4, 112.0, 90, 'B'), 'J_THU': (3.4, 125.5, 90, 'B'),
    'J_THA': (22.0, 103.0, 0, 'B'), 'J_FAN': (40.6, 108.0, 270, 'B'), 'J_AIPWR': (30.0, 110.5, 0, 'B'),
    'SC1': (16.0, 69.6, 90, 'B'), 'SC2': (28.0, 69.6, 90, 'B'), 'L_HB': (19.0, 76.5, 0, 'B'), 'U_HB': (25.5, 75.5, 0, 'B'), 'U_CHG': (30.5, 76.5, 0, 'B'), 'D_CHG': (29.0, 80.8, 0, 'B'), 'U_MCU': (20.0, 38.0, 0, 'B'), 'U_TEMP': (30.0, 37.0, 0, 'B'), 'U_C33': (31.0, 11.0, 0, 'B'), 'L_C33': (31.5, 16.5, 0, 'B'),
    'U_AON': (17.0, 11.5, 0, 'B'), 'U_SD': (20.0, 27.0, 0, 'B'),
    'U_ESD1': (9.0, 76.0, 0, 'B'), 'U_ID1': (12.5, 79.5, 0, 'B'), 'U_ID2': (12.5, 83.0, 0, 'B'),
    'U_ESD2': (34.8, 79.4, 0, 'B'), 'U_VB2': (31.0, 89.0, 0, 'B'),
    'U_ESD3': (9.0, 98.0, 0, 'B'), 'U_VB3': (13.5, 99.0, 0, 'B'), 'U_VB4': (34.5, 96.0, 0, 'B'),
    'Q_PMIC': (14.0, 39.5, 0, 'B'), 'Q_PWB': (14.0, 43.5, 0, 'B'), 'JP_WDT': (24.0, 31.5, 0, 'B'), 'JP_MATEK': (8.5, 57.5, 90, 'B'), 'JP_SERVO': (34.5, 102.5, 90, 'B'),
    'H1': (2.0, 81.6, 0, 'F'), 'H2': (42.0, 81.6, 0, 'F'), 'H3': (2.0, 10.6, 0, 'F'), 'H4': (42.0, 10.6, 0, 'F'),
}
# top side area under the CM5 module is reserved (module sits 1.5 mm above the board)
CM5_KEEP = (1.5, 12.0, 42.5, 68.2)


def load_fp(spec):
    lib, name = spec.split(':', 1)
    path = LIBS.get(lib, '/usr/share/kicad/footprints/%s.pretty' % lib)
    fp = pcbnew.FootprintLoad(path, name)
    if fp is None:
        raise SystemExit('footprint not found ' + spec)
    return fp


def bbox(fp):
    b = fp.GetBoundingBox(False, False)
    return [pcbnew.ToMM(b.GetX()), pcbnew.ToMM(b.GetY()), pcbnew.ToMM(b.GetRight()), pcbnew.ToMM(b.GetBottom())]


def main(out):
    B = pcbnew.BOARD()
    B.SetCopperLayerCount(4)
    ds = B.GetDesignSettings()
    ds.SetBoardThickness(FM(1.5))
    # ---- Rezonit 4L "1,5mm 18um Tg150 Impedance" + JLC: 0.125/0.125 mm, via 0.45/0.2
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

    occ = {'F': [], 'B': []}

    def overlaps(side, r, m=0.25):
        for o in occ[side]:
            if r[0] < o[2] + m and r[2] > o[0] - m and r[1] < o[3] + m and r[3] > o[1] - m:
                return True
        return False

    def put(fp, x, y, rot, side):
        if side == 'B' and not fp.IsFlipped():
            fp.Flip(fp.GetPosition(), False)
        fp.SetOrientationDegrees(rot)
        fp.SetPosition(V(x, y))

    placed = {}
    order = sorted(C.keys(), key=lambda r: (r not in P, r))
    for ref in order:
        c = C[ref]
        fp = load_fp(c['fp'])
        fp.SetReference(ref); fp.SetValue(c['val'][:40])
        fp.SetField('LCSC', c['lcsc']) if hasattr(fp, 'SetField') else None
        if c.get('dnp'):
            fp.SetDNP(True)
        B.Add(fp)
        placed[ref] = fp
        if ref in P:
            x, y, rot, side = P[ref]
            put(fp, x, y, rot, side)
            bb = bbox(fp)
            th = any(p.GetAttribute() == pcbnew.PAD_ATTRIB_PTH for p in fp.Pads())
            occ[side].append(bb)
            if th:
                occ['B' if side == 'F' else 'F'].append([bb[0] + 0.0, bb[1], bb[2], bb[3]] if ref.startswith(('SC', 'J_BAT')) else bb)
    for r in ('SC1', 'SC2'):
        fp = placed[r]; bb = bbox(fp)
        if bb[3] > P[r][1] + 3:          # body points down -> turn it round
            fp.SetOrientationDegrees(P[r][2] + 180); bb = bbox(fp)
        occ['B'].append(bb)
    for fp in placed.values():
        for pd in fp.Pads():
            if pd.GetAttribute() == pcbnew.PAD_ATTRIB_NPTH and pd.GetDrillSizeX() > FM(1.5):
                x, y, r = pcbnew.ToMM(pd.GetPosition().x), pcbnew.ToMM(pd.GetPosition().y), (3.0 if pd.GetDrillSizeX() >= FM(2.5) else pcbnew.ToMM(pd.GetDrillSizeX()) / 2 + 0.4)
                occ['F'].append([x - r, y - r, x + r, y + r]); occ['B'].append([x - r, y - r, x + r, y + r])
    occ['F'].append(list(CM5_KEEP))
    occ['B'].append([0.5, 30.0, 10.5, 56.0]); occ['B'].append([33.5, 30.0, 43.5, 56.0])
    # ---- auto place small parts near the IC/connector they connect to
    big = [r for r in P if r in placed]

    def anchor(ref):
        ns = [n for n in C[ref]['pins'].values() if n and n not in ('GND', '+5V_CM5', '+3V3_CM5', '+3V3_AON', '+5V_AUX')]
        if not ns:
            ns = [n for n in C[ref]['pins'].values() if n and n != 'GND']
        best = None
        for b in big:
            if b in ('M1',) and ref.startswith(('C', 'R_VREF')) is False:
                pass
            if set(ns) & set(v for v in C[b]['pins'].values()):
                pri = 0 if b.startswith(('U_', 'Q_')) else (1 if b.startswith(('J_', 'L_', 'D_')) else 2)
                if best is None or pri < best[0]:
                    best = (pri, b)
        return best[1] if best else 'U_MCU'

    for ref in order:
        if ref in P:
            continue
        fp = placed[ref]
        a = anchor(ref)
        ax, ay, _, aside = P[a]
        side = aside
        if a == 'M1':                       # CM5 support parts go underneath on the bottom
            side = 'B'; ax, ay = 22.0, 60.0
        if a in ('J_CAM1', 'J_CAM2'):
            side = 'B'; ay = 11.0
        if side == 'F' and CM5_KEEP[1] < ay < CM5_KEEP[3]:
            side = 'B'
        ok = False
        for rad in [i * 0.6 for i in range(1, 70)]:
            for k in range(max(8, int(rad * 10))):
                t = 2 * math.pi * k / max(8, int(rad * 10))
                x, y = ax + rad * math.cos(t), ay + rad * math.sin(t)
                for rot in (0, 90):
                    put(fp, x, y, rot, side)
                    bb = bbox(fp)
                    if bb[0] < 0.6 or bb[1] < 0.6 or bb[2] > W - 0.6 or bb[3] > L - 0.6:
                        continue
                    if overlaps(side, bb):
                        continue
                    occ[side].append(bb); ok = True
                    break
                if ok:
                    break
            if ok:
                break
        if not ok:
            print('COULD NOT PLACE', ref)
    for fp in placed.values():
        for pad in fp.Pads():
            if pad.GetAttribute() == pcbnew.PAD_ATTRIB_PTH and pad.GetNumber() == '' and pad.GetSizeX() <= pad.GetDrillSizeX() + FM(0.15):
                pad.SetAttribute(pcbnew.PAD_ATTRIB_NPTH); pad.SetLayerSet(pad.UnplatedHoleMask())
    # ---- silkscreen: only references of ICs/connectors + human labels; values on fab layer
    LABEL = {'J_CAM1': 'CAM1 (day)', 'J_CAM2': 'CAM2 (night)', 'J_PCIE': 'AI / Hailo PCIe', 'J_USB1': 'USB-C PC/FW', 'J_USB2': 'USB-C HOST',
             'J_BAT': 'BAT 3-6S XT60', 'J_BAT2': 'XT30 alt', 'J_SD': 'microSD', 'J_S1': 'SERVO1', 'J_S2': 'SERVO2', 'J_S3': 'SERVO3', 'J_S4': 'SERVO4',
             'J_SPWR': 'SERVO PWR (BEC)', 'J_MATEK': 'MATEK UART0', 'J_GPS': 'GPS UART2', 'J_I2C': 'I2C', 'J_IO': 'GPIO', 'J_THU': 'THERMAL USB',
             'J_THA': 'THERMAL AUX', 'J_FAN': 'FAN 5V', 'J_AIPWR': 'AI 5V', 'J_RTC': 'RTC BAT', 'SW_BOOT': 'BOOT', 'SW_PWR': 'POWER',
             'D_PWR': 'PWR', 'D_RUN': 'RUN', 'D_ERR': 'ERR', 'JP_WDT': 'WDT OFF', 'JP_SERVO': 'SERVO=5V', 'JP_MATEK': 'MATEK 5V'}
    for ref, fp in placed.items():
        fp.Value().SetVisible(False)
        for f in fp.GetFields():
            if f.GetName() not in ('Reference', 'Value'): f.SetVisible(False)
        rt = fp.Reference(); rt.SetTextSize(V(0.8, 0.8)); rt.SetTextThickness(FM(0.15))
        if re.match(r'^(R|C|L_|D_|Q_|U_ESD|U_ID|TP_|H)\d*', ref) and ref not in LABEL:
            rt.SetVisible(False)
        if ref in LABEL:
            rt.SetText(LABEL[ref] if not ref.startswith('D_') else LABEL[ref]); rt.SetVisible(True)
    # ---- 3D models for parts without vendor models
    G3 = HERE + '/lib/gen3d/'
    MODELS = {'M1': ('CM5_with_cooler', (0, 0, 0)), 'J_USB1': ('USB_C_receptacle', (0, -0.5, 0)), 'J_USB2': ('USB_C_receptacle', (0, -0.5, 0)),
              'L_B1': ('Inductor_7x6', (0, 0, 0)), 'L_B2': ('Inductor_7x6', (0, 0, 0)), 'U_B1': ('SOP8_EP', (0, 0, 0)), 'U_B2': ('SOP8_EP', (0, 0, 0)),
              'SC1': ('SuperCap_D10_L20', (0, 0, 0)), 'SC2': ('SuperCap_D10_L20', (0, 0, 0)), 'F1': ('Fuse_2410', (0, 0, 0)), 'J_BAT': ('XT60PW', (0, 0, 0)), 'J_BAT2': ('XT30PW', (0, 0, 0))}
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
            if n is None and num in ('', ) :
                continue
            if n is None and (num.startswith('MP') or num in ('MP',)):
                n = c['pins'].get('MP')
            if n is None and c['fp'].startswith('Connector_JST') and num == 'MP':
                n = 'GND'
            if n:
                pad.SetNet(net(n))
    # ---- net classes
    ns = ds.m_NetSettings
    def ncls(name, w, clr, dpw=None, dpg=None, via=(0.45, 0.2)):
        nc = pcbnew.NETCLASS(name)
        nc.SetTrackWidth(FM(w)); nc.SetClearance(FM(clr)); nc.SetViaDiameter(FM(via[0])); nc.SetViaDrill(FM(via[1]))
        if dpw: nc.SetDiffPairWidth(FM(dpw)); nc.SetDiffPairGap(FM(dpg))
        ns.SetNetclass(name, nc)
        return nc
    dflt = ns.GetDefaultNetclass(); dflt.SetTrackWidth(FM(0.15)); dflt.SetClearance(FM(0.125)); dflt.SetViaDiameter(FM(0.45)); dflt.SetViaDrill(FM(0.2))
    ncls('DIFF100', 0.13, 0.15, 0.13, 0.17)
    ncls('DIFF90', 0.17, 0.15, 0.17, 0.15)
    ncls('PWR_HI', 0.8, 0.2, via=(0.6, 0.3))
    ncls('PWR_MID', 0.4, 0.15, via=(0.6, 0.3))
    for n in DIFF100: ns.SetNetclassPatternAssignment(n, 'DIFF100')
    for n in DIFF90: ns.SetNetclassPatternAssignment(n, 'DIFF90')
    for n in POWER_HI:
        if n != 'GND': ns.SetNetclassPatternAssignment(n, 'PWR_HI')
    for n in POWER_MID: ns.SetNetclassPatternAssignment(n, 'PWR_MID')
    def zone(netname, layer, pts, prio=0, clr=0.25):
        z = pcbnew.ZONE(B); z.SetLayer(layer); z.SetNet(net(netname)); z.SetAssignedPriority(prio)
        z.SetLocalClearance(FM(clr)); z.SetMinThickness(FM(0.2)); z.SetThermalReliefGap(FM(0.25)); z.SetThermalReliefSpokeWidth(FM(0.4))
        z.SetPadConnection(pcbnew.ZONE_CONNECTION_THERMAL)
        ol = z.Outline(); ol.NewOutline()
        for x, y in pts: ol.Append(FM(x), FM(y))
        B.Add(z); return z
    full = [(0.3, 0.3), (W - 0.3, 0.3), (W - 0.3, L - 0.3), (0.3, L - 0.3)]
    zone('GND', pcbnew.In1_Cu, full)
    zone('GND', pcbnew.In2_Cu, full)
    zone('+5V_CM5', pcbnew.In2_Cu, [(0.5, 30), (13.5, 30), (13.5, 80), (21.5, 80), (21.5, 99.5), (0.5, 99.5)], 1)
    zone('+5V_AUX', pcbnew.In2_Cu, [(22.5, 80), (43.5, 80), (43.5, 99.5), (22.5, 99.5)], 1)
    zone('VIN_PROT', pcbnew.In2_Cu, [(0.5, 100.5), (43.5, 100.5), (43.5, 133.7), (0.5, 133.7)], 1)
    B.Save(out)
    print('saved', out, len(C), 'footprints', len(nets), 'nets')


if __name__ == '__main__':
    main(sys.argv[1] if len(sys.argv) > 1 else HERE + '/CM5-DETECT_rev03_placed.kicad_pcb')
