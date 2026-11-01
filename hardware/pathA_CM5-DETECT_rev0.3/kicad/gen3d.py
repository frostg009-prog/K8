# Generate simple VRML 3D models (boxes / cylinders) for parts without vendor models. KiCad VRML unit = 2.54 mm.
import os
OUT = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'lib', 'gen3d')
os.makedirs(OUT, exist_ok=True)
U = 2.54


def box(cx, cy, z0, sx, sy, sz, rgb, shin=0.3):
    return ('Transform { translation %.4f %.4f %.4f children [ Shape { appearance Appearance { material Material { diffuseColor %s specularColor 0.3 0.3 0.3 shininess %s } } '
            'geometry Box { size %.4f %.4f %.4f } } ] }\n' % (cx / U, cy / U, (z0 + sz / 2) / U, ' '.join('%.3f' % c for c in rgb), shin, sx / U, sy / U, sz / U))


def cyl_x(cx, cy, cz, r, l, rgb):   # cylinder lying along X
    return ('Transform { translation %.4f %.4f %.4f rotation 0 0 1 1.5708 children [ Shape { appearance Appearance { material Material { diffuseColor %s } } '
            'geometry Cylinder { radius %.4f height %.4f } } ] }\n' % (cx / U, cy / U, cz / U, ' '.join('%.3f' % c for c in rgb), r / U, l / U))


def write(name, parts):
    open(os.path.join(OUT, name + '.wrl'), 'w').write('#VRML V2.0 utf8\n' + ''.join(parts))


GREEN = (0.05, 0.35, 0.15); BLACK = (0.08, 0.08, 0.08); METAL = (0.75, 0.75, 0.78); ALU = (0.55, 0.57, 0.62); GOLD = (0.85, 0.7, 0.2)
# CM5 module 55 x 40 mm with cooler: origin = footprint origin (hole bottom-left), module spans x -3.5..51.5? use hole pattern 33x48 centred
# footprint: holes at (0,0),(33,0),(0,-48),(33,-48) => centre (16.5,-24); KiCad y up in 3D => +24
cm5 = [box(16.5, 24, 1.5, 40, 55, 1.0, GREEN), box(16.5, 30, 2.5, 15, 15, 1.0, (0.2, 0.2, 0.22)),
       box(16.5, 14, 2.5, 13, 10, 1.0, BLACK), box(16.5, 42, 2.5, 10, 8, 1.0, BLACK)]
# cooler: base + fins (Raspberry Pi CM5 Cooler style)
cm5.append(box(16.5, 24, 3.5, 38, 50, 2.0, ALU))
for k in range(13):
    cm5.append(box(16.5 - 18 + 1.4 + k * 2.8, 24, 5.5, 1.2, 50, 9.0, ALU))
write('CM5_with_cooler', cm5)
write('USB_C_receptacle', [box(0, 0, 0, 8.94, 7.3, 3.26, METAL, 0.8)])
write('Inductor_7x6', [box(0, 0, 0, 7.0, 6.6, 3.0, (0.25, 0.25, 0.27))])
write('SOP8_EP', [box(0, 0, 0, 4.9, 3.9, 1.6, BLACK)])
write('SuperCap_D10_L20', [cyl_x(13.5, 0, 5.2, 5.0, 20.0, (0.1, 0.25, 0.6)), box(1.5, 0, 0, 3, 5.5, 0.8, METAL)])
write('FFC_22', [box(0, 0, 0, 17, 5.0, 2.0, (0.9, 0.9, 0.85)), box(0, -1.5, 2.0, 15, 2.0, 0.4, (0.45, 0.25, 0.1))])
write('FFC_16', [box(0, 0, 0, 14, 5.0, 2.0, (0.9, 0.9, 0.85)), box(0, -1.5, 2.0, 12, 2.0, 0.4, (0.45, 0.25, 0.1))])
write('TF_card', [box(0, 0, 0, 14.5, 15.0, 1.85, METAL, 0.8)])
write('Fuse_2410', [box(0, 0, 0, 6.1, 2.6, 2.6, (0.95, 0.95, 0.9))])
print('models in', OUT)
# RK3576 CM5-format module (Radxa CM4 / ArmSoM CM5 style): dark blue PCB, SoC, LPDDR, eMMC, smaller cooler
BLUE = (0.05, 0.12, 0.35)
rk = [box(16.5, 24, 1.5, 40, 55, 1.0, BLUE), box(16.5, 30, 2.5, 14, 14, 1.2, (0.15, 0.15, 0.17)),
      box(9.0, 14, 2.5, 10, 12, 1.0, BLACK), box(24.0, 14, 2.5, 10, 12, 1.0, BLACK), box(16.5, 44, 2.5, 11.5, 13, 1.0, BLACK),
      box(16.5, 30, 3.7, 30, 30, 2.0, (0.15, 0.15, 0.16))]
for k in range(9):
    rk.append(box(16.5 - 14 + 1.5 + k * 3.2, 30, 5.7, 1.2, 30, 7.0, (0.15, 0.15, 0.16)))
write('RK3576_module_with_cooler', rk)
YEL = (0.95, 0.8, 0.1)
write('XT60PW', [box(3.6, 8.5, 0, 15.6, 16.0, 8.2, YEL), box(3.6, 16.2, 1.5, 12, 1.0, 5.5, (0.8, 0.65, 0.05))])
write('XT30PW', [box(-2.5, 7.0, 0, 10.2, 13.0, 5.2, YEL)])
