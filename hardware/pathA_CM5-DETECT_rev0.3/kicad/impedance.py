# Impedance for Rezonit "4 Layers (1,5mm 18um Tg150 Impedance)" stack (from the supplied .stackup):
# L1 18 um + 27 um plating | prepreg 5 mil (0.127 mm) er 4.2 | L2 GND | core 1.2 mm er 4.6 | L3 | 0.127 mm | L4 ; mask 25 um er 3.5
# IPC-2141A closed forms (+ solder-mask correction ~ -2.5 ohm on coated microstrip). Factory fine-tunes width (+-10%).
import math
H, ER, T = 0.127, 4.2, 0.045


def z0(w):
    return 87 / math.sqrt(ER + 1.41) * math.log(5.98 * H / (0.8 * w + T)) - 2.5


def zdiff(w, s):
    return 2 * z0(w) * (1 - 0.48 * math.exp(-0.96 * s / H))


rows = [('MIPI CSI-2 camera pairs, PCIe (target 100 / 85-100 ohm)', 0.13, 0.17),
        ('USB 2.0 pairs (target 90 ohm)', 0.15, 0.15),
        ('single-ended 50 ohm reference', 0.22, None)]
if __name__ == '__main__':
    for name, w, s in rows:
        if s:
            print('%-58s w=%.2f s=%.2f mm  Zdiff=%.1f ohm (Z0=%.1f)' % (name, w, s, zdiff(w, s), z0(w)))
        else:
            print('%-58s w=%.2f mm        Z0=%.1f ohm' % (name, w, z0(w)))
