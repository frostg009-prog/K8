# -*- coding: utf-8 -*-
"""CM5-DETECT rev0.4: bill of materials from design.py (single source of truth).
   python3 make_bom_rev04.py OUTDIR
Writes:
  BOM_rev04_full.csv      - every board position grouped by part (qty, refs, value, footprint, LCSC, MPN/notes, DNP)
  BOM_JLCPCB_rev04.csv    - JLCPCB PCBA format (Comment, Designator, Footprint, LCSC Part #), DNP excluded
  BUY_LIST_rev04.csv      - everything to buy for one complete unit: board parts + module, cooler, cables, screws, enclosure
"""
import os, sys, csv
from collections import OrderedDict
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
from design import C

out = sys.argv[1] if len(sys.argv) > 1 else os.path.join(HERE, 'fab_rev04')
os.makedirs(out, exist_ok=True)

# hand-placed / not-from-LCSC positions
NOT_SMT = {'SC1', 'SC2', 'J_BAT'}            # through-hole: wave / hand soldering
NO_PART = lambda r: r.startswith(('H', 'TP_', 'JP_'))   # holes, test pads, solder jumpers: copper only

groups = OrderedDict()
for ref, c in C.items():
    if NO_PART(ref):
        continue
    key = (c['val'], c['fp'].split(':')[1], c['lcsc'], bool(c.get('dnp')))
    groups.setdefault(key, []).append(ref)


def natkey(r):
    import re
    m = re.match(r'([A-Za-z_]+)(\d*)', r)
    return (m.group(1), int(m.group(2) or 0))


rows = []
for (val, fp, lcsc, dnp), refs in groups.items():
    refs = sorted(refs, key=natkey)
    rows.append(dict(qty=len(refs), refs=','.join(refs), val=val, fp=fp, lcsc=lcsc, dnp='DNP' if dnp else '',
                     mount='THT' if set(refs) & NOT_SMT else 'SMD', side='', note=C[refs[0]]['note']))
rows.sort(key=lambda r: (r['dnp'] != '', natkey(r['refs'].split(',')[0])))
with open(os.path.join(out, 'BOM_rev04_full.csv'), 'w', newline='', encoding='utf-8') as f:
    w = csv.writer(f)
    w.writerow(['#', 'Qty', 'Designators', 'Value / description', 'Footprint', 'LCSC', 'Mount', 'DNP', 'Note'])
    for i, r in enumerate(rows, 1):
        w.writerow([i, r['qty'], r['refs'], r['val'], r['fp'], r['lcsc'], r['mount'], r['dnp'], r['note']])
with open(os.path.join(out, 'BOM_JLCPCB_rev04.csv'), 'w', newline='', encoding='utf-8') as f:
    w = csv.writer(f)
    w.writerow(['Comment', 'Designator', 'Footprint', 'LCSC Part #'])
    for r in rows:
        if r['dnp']:
            continue
        lc = r['lcsc'] if r['lcsc'].startswith('C') and r['lcsc'][1:].isdigit() else ''
        w.writerow([r['val'], r['refs'], r['fp'], lc])

# ---------------------------------------------------------------- everything else needed for one working unit
EXTRA = [
    ('Module', 1, 'Raspberry Pi Compute Module 5 (CM5108032: 8 GB RAM, 32 GB eMMC, no Wi-Fi) - or CM5 Lite + microSD', 'M1', 'Raspberry Pi distributor'),
    ('Module', 1, 'Raspberry Pi CM5 Cooler (SC1748) - heatsink for CM5', 'M1', 'Raspberry Pi distributor'),
    ('Module', 4, 'Screw M2.5 x 6 mm (CM5 to base stand-offs, through the module)', 'M1 holes', 'any'),
    ('Board', 2, 'Supercapacitor 10 F 2.7 V D10 x L20, radial (SCCDQR2R7106 or Kamcap SP-2R7-106) - lay flat, glue', 'SC1,SC2', 'LCSC / ChipDip'),
    ('Board', 1, 'XT60PW-M (AMASS) right-angle PCB male', 'J_BAT', 'LCSC C98732'),
    ('Cable', 2, 'Camera FFC 22-pin 0.5 mm, same-side contacts (Pi 5 / CM camera cable), 200-400 mm', 'J_CAM1,J_CAM2', 'Raspberry Pi / AliExpress'),
    ('Cable', 1, 'PCIe FFC 16-pin 0.5 mm (Pi 5 PCIe cable, supplied with AI HAT+) <= 50 mm', 'J_PCIE', 'with Hailo AI HAT+'),
    ('Cable', 11, 'JST-SH 1.0 mm pre-crimped cable sets (SHR-xxV-S housing): 2p x1, 3p x4, 4p x6, 6p x1, 8p x1', 'J_*', 'AliExpress / LCSC'),
    ('Cable', 1, 'XT60 battery lead (female), 12-14 AWG', 'J_BAT', 'any'),
    ('Cable', 1, 'USB-C cable (PC <-> board) for rpiboot flashing / USB gadget', 'J_USB1', 'any'),
    ('Accessory', 1, 'RTC coin cell CR2032 with 2-pin JST-SH lead (or ML2032 rechargeable)', 'J_RTC', 'any'),
    ('Accessory', 1, 'Fan 5 V 25 x 25 mm or 30 x 30 mm with 4-pin PWM (optional, JST-SH 4p)', 'J_FAN', 'optional'),
    ('Accessory', 1, 'microSD card A2 32-128 GB (only for CM5 Lite)', 'J_SD', 'optional'),
    ('Accessory', 1, 'Hailo-8L / Hailo-8 AI HAT+ (26/13 TOPS) or M.2 HAT+ with Hailo module', 'J_PCIE,J_AIPWR', 'optional'),
    ('Enclosure', 1, 'base.stl  - PETG / ASA, 0.2 mm layer, 3 walls, 25 % infill, no supports', 'enclosure_rev04', 'print'),
    ('Enclosure', 1, 'lid_print_orientation.stl - PETG / ASA, roof down, supports only under the side vents', 'enclosure_rev04', 'print'),
    ('Enclosure', 6, 'Screw M2.5 x 16 mm cap head (DIN 912 / ISO 7380), from below: base -> board -> lid boss', 'H1..H6', 'any'),
    ('Tools', 1, 'WCH-LinkE programmer (flashes the CH32V003 supervisor via TP_SWIO/TP_3V3/TP_GND)', 'U_MCU', 'LCSC / AliExpress'),
]
with open(os.path.join(out, 'BUY_LIST_rev04.csv'), 'w', newline='', encoding='utf-8') as f:
    w = csv.writer(f)
    w.writerow(['Group', 'Qty', 'Item', 'For', 'Source'])
    for r in rows:
        if r['dnp']:
            continue
        w.writerow(['PCB assembly (factory)', r['qty'], '%s [%s]' % (r['val'], r['fp']), r['refs'], 'LCSC ' + r['lcsc'] if r['lcsc'] else ''])
    for e in EXTRA:
        w.writerow(list(e))
n_parts = sum(r['qty'] for r in rows if not r['dnp'])
print('BOM: %d lines, %d placed parts, %d DNP lines, %d extra items -> %s' % (len(rows), n_parts, sum(1 for r in rows if r['dnp']), len(EXTRA), out))
