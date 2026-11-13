# -*- coding: utf-8 -*-
"""CM5-DETECT rev0.4 enclosure (2 printed parts: base + lid), generated from the board's mechanical data.
   python3 make_enclosure.py            -> base.stl, lid.stl, assembly_preview.stl (+ report)
Needs: pip install manifold3d trimesh numpy

Coordinate system: X = KiCad x, Y = 138 - KiCad y (KiCad y points down), Z up, board top side faces up (+Z).
Fixing: 6 screws M2.5 x 16 (DIN 912 / ISO 7380) from below: base stand-off -> board hole H1..H6 -> lid boss (self-tapping pilot).
        CM5 module: 4 screws M2.5 x 6 from above through the module into the 4 base stand-offs (brass pillar not needed).
"""
import json, os, math
import numpy as np
import manifold3d as m3d
import trimesh

HERE = os.path.dirname(os.path.abspath(__file__))
D = json.load(open(os.path.join(HERE, 'board_mech.json')))
BW, BL, BT = D['board']

# ---------------------------------------------------------------- parameters (mm)
WALL = 2.0          # side wall
FLOOR = 2.0         # base floor / lid roof
GAP = 0.8           # board edge to inner wall
UNDER = 6.0         # free height under the board (bottom parts <= 5.2 mm: L_HB 5.0, JST-SH 2.9, D_SMC 2.4)
ABOVE = 17.0        # free height above the board top (CM5 + Raspberry Pi CM5 Cooler ~14.5 mm, supercaps D10, XT60 8.2)
SPLIT = 4.0         # base walls rise this far above the board top; lid covers the rest
LIP = 1.2           # lid inner lip (fits inside the base walls)
CLR = 0.25          # print clearance lid lip <-> base wall
SEG = 48

Z_BB = FLOOR + UNDER            # board bottom
Z_BT = Z_BB + BT                # board top
Z_SPLIT = Z_BT + SPLIT
Z_TOP = Z_BT + ABOVE + FLOOR
X0, Y0 = -GAP - WALL, -GAP - WALL
OX, OY = BW + 2 * (GAP + WALL), BL + 2 * (GAP + WALL)
Y = lambda yk: BL - yk


def box(x0, y0, z0, x1, y1, z1):
    return m3d.Manifold.cube([x1 - x0, y1 - y0, z1 - z0]).translate([x0, y0, z0])


def cyl(x, y, z0, z1, r, seg=SEG):
    return m3d.Manifold.cylinder(z1 - z0, r, r, seg).translate([x, y, z0])


def rbox(x0, y0, z0, x1, y1, z1, r):
    """box with vertical rounded edges"""
    cs = m3d.CrossSection.square([x1 - x0 - 2 * r, y1 - y0 - 2 * r]).translate([x0 + r, y0 + r]).offset(r, m3d.JoinType.Round, 2.0, SEG)
    return cs.extrude(z1 - z0).translate([0, 0, z0])


def union(parts):
    out = None
    for p in parts:
        out = p if out is None else out + p
    return out


# ---------------------------------------------------------------- shells
R = 3.0
outer = rbox(X0, Y0, 0, X0 + OX, Y0 + OY, Z_TOP, R)
cavity = rbox(-GAP, -GAP, FLOOR, BW + GAP, BL + GAP, Z_TOP - FLOOR, R - WALL + 0.5)

# ---------------------------------------------------------------- connector windows in the walls
H_F = {'J_USB1': 3.6, 'J_USB2': 3.6, 'J_CAM1': 2.6, 'J_CAM2': 2.6, 'J_BAT': 8.8}
H_B = {'J_PCIE': 2.6, 'J_SD': 2.2, 'J_SPWR': 4.8, 'J_AIPWR': 4.8}     # GH body 4.25 mm + wires from the solder pads
SH_H = 3.4            # JST-SH horizontal body height 2.9 + margin
cuts = []
report = []
for p in D['parts']:
    r = p['ref']
    if not r.startswith('J_'):
        continue
    x0, y0, x1, y1 = p['bb']
    side = p['side']
    h = (H_F if side == 'F' else H_B).get(r, SH_H)
    m = 0.6
    if r.startswith(('J_USB',)):               # USB-C plug overmould ~ 12.5 x 6.5: window 13 x 7 centred on the receptacle
        cy = (y0 + y1) / 2; y0, y1 = cy - 6.5, cy + 6.5
        z0, z1 = Z_BT + 1.65 - 3.5, Z_BT + 1.65 + 3.5
    elif r == 'J_BAT':                          # XT60 plug: body 16 x 8.2 -> window
        z0, z1 = Z_BT - 0.2, Z_BT + h
    elif side == 'F':
        z0, z1 = Z_BT - 0.2, Z_BT + h
    else:
        z0, z1 = Z_BB - h, Z_BB + 0.2
    if r in ('J_CAM1', 'J_CAM2', 'J_PCIE'):     # FFC slots: cable 0.3 mm + bend room
        x0, x1 = x0 + 1.0, x1 - 1.0
    if r == 'J_BAT':                            # XT60PW mating face points to the south board edge
        cuts.append(box(x0 - m, Y0 - 1, z0, min(x1 + m, BW + GAP - 0.2), Y(BL) + 0.5, z1)); wall = 'S'
    elif x0 < 1.5:
        cuts.append(box(X0 - 1, Y(y1) - m, z0, 0.5, Y(y0) + m, z1)); wall = 'W'
    elif x1 > BW - 1.5:
        cuts.append(box(BW - 0.5, Y(y1) - m, z0, X0 + OX + 1, Y(y0) + m, z1)); wall = 'E'
    elif y0 < 1.5:
        cuts.append(box(x0 - m, Y(0) - 0.5, z0, x1 + m, Y0 + OY + 1, z1)); wall = 'N'
    elif y1 > BL - 1.5:
        cuts.append(box(x0 - m, Y0 - 1, z0, x1 + m, Y(BL) + 0.5, z1)); wall = 'S'
    else:
        continue
    report.append('%-8s %s-wall  %s side  z %.1f..%.1f' % (r, wall, side, z0, z1))
# microSD: finger notch so the push-push card can be reached
sd = [p for p in D['parts'] if p['ref'] == 'J_SD'][0]
cuts.append(box(X0 - 1, Y(sd['bb'][3]) + 4, Z_BB - 6, 1.0, Y(sd['bb'][1]) - 4, Z_BB - 2.0))

# ---------------------------------------------------------------- base
base = outer - cavity
base = base - box(X0 - 5, Y0 - 5, Z_SPLIT, X0 + OX + 5, Y0 + OY + 5, Z_TOP + 5)
for c in cuts:
    base = base - c
hole_board = [h for h in D['holes'] if len(h) == 2]
hole_cm5 = [h for h in D['holes'] if len(h) == 3]
for x, y in [(h[0], h[1]) for h in hole_board]:
    base = base + cyl(x, Y(y), FLOOR - 0.01, Z_BB, 2.6)
    base = base - cyl(x, Y(y), -1, Z_BB + 1, 1.45)                    # M2.5 clearance through
    base = base - cyl(x, Y(y), -1, 1.6, 2.6)                          # recess for the screw head (dia 5.2 x 1.6)
for x, y, _ in hole_cm5:
    base = base + cyl(x, Y(y), FLOOR - 0.01, Z_BB, 2.9)
    base = base - cyl(x, Y(y), FLOOR + 1.0, Z_BB + 1, 1.05)           # pilot for M2.5 self-tapping (or M2.5 heat-set insert: drill 3.6)
M1 = [p for p in D['parts'] if p['ref'] == 'M1'][0]['bb']     # CM5 module outline (KiCad coords)
# ventilation slots in the floor (under the CM5 area: bottom parts are low there)
for i in range(7):
    xs = M1[0] + 7.0 + i * 4.0
    base = base - box(xs, Y(60.0), -1, xs + 1.8, Y(20.0), FLOOR + 0.5)
# ---------------------------------------------------------------- lid
lid = outer - cavity
lid = lid - box(X0 - 5, Y0 - 5, -5, X0 + OX + 5, Y0 + OY + 5, Z_SPLIT)
# inner lip that slides into the base walls
lip_o = rbox(-GAP + CLR, -GAP + CLR, Z_SPLIT - 3.0, BW + GAP - CLR, BL + GAP - CLR, Z_SPLIT + 0.01, R - WALL + 0.3)
lip_i = rbox(-GAP + CLR + LIP, -GAP + CLR + LIP, Z_SPLIT - 4, BW + GAP - CLR - LIP, BL + GAP - CLR - LIP, Z_SPLIT + 1, 0.8)
lid = lid + (lip_o - lip_i)
for c in cuts:
    lid = lid - c
# bosses pressing the board down at H1..H6 (screws come from below)
for x, y in [(h[0], h[1]) for h in hole_board]:
    lid = lid + cyl(x, Y(y), Z_BT + 0.05, Z_TOP - FLOOR + 0.01, 2.3)
    lid = lid - cyl(x, Y(y), Z_BT - 1, Z_BT + 8.0, 1.05)              # M2.5 self-tapping pilot, 8 mm deep
# button pushers: holes over BOOT / POWER (press with a 2 mm pin / paper clip), light pipes over LEDs
for p in D['parts']:
    cx, cy = (p['bb'][0] + p['bb'][2]) / 2, (p['bb'][1] + p['bb'][3]) / 2
    if p['ref'] in ('SW_BOOT', 'SW_PWR'):
        lid = lid - cyl(cx, Y(cy), Z_TOP - FLOOR - 1, Z_TOP + 1, 1.6)
    if p['ref'] in ('D_PWR', 'D_RUN', 'D_ERR'):
        lid = lid - cyl(cx, Y(cy), Z_TOP - FLOOR - 1, Z_TOP + 1, 1.0)
# ---- fan 40 x 40 mm (5 V, 2/3/4-wire) on top of the lid, blowing down onto the CM5 cooler
#      opening dia 37 with a cross guard (2 mm bars), 4 x M3 holes on the standard 32 mm pattern
FAN, FAN_HOLE, FAN_PITCH = 40.0, 37.0, 32.0
FCX, FCY = (M1[0] + M1[2]) / 2, (M1[1] + M1[3]) / 2          # centre of the CM5 module (KiCad coords)
opening = cyl(FCX, Y(FCY), Z_TOP - FLOOR - 1, Z_TOP + 1, FAN_HOLE / 2, 96)
guard = (box(FCX - 1.0, Y(FCY) - FAN_HOLE / 2, Z_TOP - FLOOR, FCX + 1.0, Y(FCY) + FAN_HOLE / 2, Z_TOP) +
         box(FCX - FAN_HOLE / 2, Y(FCY) - 1.0, Z_TOP - FLOOR, FCX + FAN_HOLE / 2, Y(FCY) + 1.0, Z_TOP) +
         (cyl(FCX, Y(FCY), Z_TOP - FLOOR, Z_TOP, 10.0, 96) - cyl(FCX, Y(FCY), Z_TOP - FLOOR - 1, Z_TOP + 1, 8.5, 96)))
lid = lid - opening + guard
for dx in (-FAN_PITCH / 2, FAN_PITCH / 2):
    for dy in (-FAN_PITCH / 2, FAN_PITCH / 2):
        lid = lid - cyl(FCX + dx, Y(FCY) + dy, Z_TOP - FLOOR - 1, Z_TOP + 1, 1.7)      # M3 clearance
# hot air leaves through the side vents (both walls, along the module and past it)
for yk in (20.0, 32.0, 44.0, 56.0, 68.0):
    for xs, xe in ((X0 - 1, 0.5), (BW - 0.5, X0 + OX + 1)):
        lid = lid - box(xs, Y(yk + 8), Z_BT + 9, xe, Y(yk), Z_BT + 14)

# ---------------------------------------------------------------- board dummy for the preview
board = box(0, 0, Z_BB, BW, BL, Z_BT)
# reference models (NOT for printing): 40x40x10 fan on the lid, CM5 module + Raspberry Pi CM5 Cooler on the board
FT = 10.0
fan = rbox(FCX - FAN / 2, Y(FCY) - FAN / 2, Z_TOP, FCX + FAN / 2, Y(FCY) + FAN / 2, Z_TOP + FT, 2.5)
fan = fan - cyl(FCX, Y(FCY), Z_TOP - 1, Z_TOP + FT + 1, 19.0, 96)
fan = fan - box(FCX - FAN / 2 + 1.5, Y(FCY) - FAN / 2 + 1.5, Z_TOP + 1.5, FCX + FAN / 2 - 1.5, Y(FCY) + FAN / 2 - 1.5, Z_TOP + FT - 1.5)
for dx in (-FAN_PITCH / 2, FAN_PITCH / 2):
    for dy in (-FAN_PITCH / 2, FAN_PITCH / 2):
        fan = fan - cyl(FCX + dx, Y(FCY) + dy, Z_TOP - 1, Z_TOP + FT + 1, 1.7)
hub = cyl(FCX, Y(FCY), Z_TOP + 1.0, Z_TOP + FT - 0.5, 9.0, 64)
blades = None
import math as _m
for k in range(7):
    a_ = 2 * _m.pi * k / 7
    bl = box(0, -1.4, 0, 9.5, 1.4, FT - 3.0).rotate([18, 0, 0]).rotate([0, 0, _m.degrees(a_)]).translate([FCX + 8.5 * _m.cos(a_), Y(FCY) + 8.5 * _m.sin(a_), Z_TOP + 1.5])
    blades = bl if blades is None else blades + bl
spokes = (box(FCX - 0.8, Y(FCY) - 19.5, Z_TOP + FT - 1.2, FCX + 0.8, Y(FCY) + 19.5, Z_TOP + FT) +
          box(FCX - 19.5, Y(FCY) - 0.8, Z_TOP + FT - 1.2, FCX + 19.5, Y(FCY) + 0.8, Z_TOP + FT))
fan = fan + hub + (blades ^ cyl(FCX, Y(FCY), Z_TOP, Z_TOP + FT, 18.8, 96)) + spokes
cm5 = box(M1[0], Y(M1[3]), Z_BT + 3.0, M1[2], Y(M1[1]), Z_BT + 4.2)                         # module on its 2 x 100 pin connectors
cooler = box(M1[0] + 1.0, Y(M1[3]) + 2.0, Z_BT + 4.2, M1[2] - 1.0, Y(M1[1]) - 2.0, Z_BT + 6.2)
for i in range(13):
    xf = M1[0] + 2.0 + i * (M1[2] - M1[0] - 4.0) / 12
    cooler = cooler + box(xf - 0.6, Y(M1[3]) + 2.0, Z_BT + 6.2, xf + 0.6, Y(M1[1]) - 2.0, Z_BT + 14.5)


def save(man, name):
    mesh = man.to_mesh()
    t = trimesh.Trimesh(vertices=np.asarray(mesh.vert_properties)[:, :3], faces=np.asarray(mesh.tri_verts), process=True)
    t.export(os.path.join(HERE, name))
    return t


tb = save(base, 'base.stl')
tl = save(lid, 'lid.stl')
# lid printed upside down: provide a print-oriented copy
lid_print = lid.rotate([180, 0, 0]).translate([0, Y0 * 2 + OY, Z_TOP])
save(lid_print, 'lid_print_orientation.stl')
save(base + lid + board + cm5 + cooler + fan, 'assembly_preview.stl')
save(fan, 'REFERENCE_fan_4010_do_not_print.stl')
save(cm5 + cooler, 'REFERENCE_cm5_cooler_do_not_print.stl')
print('clearance fan bottom -> cooler fins: %.1f mm (roof %.1f mm)' % (Z_TOP - FLOOR - (Z_BT + 14.5), FLOOR))
rep = []
rep.append('Outer size  %.1f x %.1f x %.1f mm' % (OX, OY, Z_TOP))
rep.append('base: watertight=%s volume=%.1f cm3 ; lid: watertight=%s volume=%.1f cm3' % (tb.is_watertight, tb.volume / 1000, tl.is_watertight, tl.volume / 1000))
rep.append('board bottom z=%.1f, board top z=%.1f, split z=%.1f' % (Z_BB, Z_BT, Z_SPLIT))
rep.append('fan 40x40 on lid: centre KiCad (%.1f, %.1f), opening dia %.0f, M3 holes 32 mm pitch' % (FCX, FCY, FAN_HOLE))
rep += report
open(os.path.join(HERE, 'enclosure_report.txt'), 'w').write('\n'.join(rep) + '\n')
print('\n'.join(rep))
