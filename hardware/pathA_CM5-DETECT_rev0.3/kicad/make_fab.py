# -*- coding: utf-8 -*-
"""Factory outputs from the routed board: Gerber+drill (JLC & Rezonit), BOM (JLC format), CPL, DRC report, renders.
usage: python3 make_fab.py CM5-DETECT_rev03.kicad_pcb OUTDIR"""
import os, sys, csv, subprocess, json
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
from design import C
pcb, out = os.path.abspath(sys.argv[1]), os.path.abspath(sys.argv[2])
for d in ('01_Photos', '02_Components', '04_Gerber', '06_Checks_and_calculations'):
    os.makedirs(os.path.join(out, d), exist_ok=True)
run = lambda *a: subprocess.run(list(a), check=False, capture_output=True, text=True)
g = os.path.join(out, '04_Gerber', 'gerber')
os.makedirs(g, exist_ok=True)
layers = 'F.Cu,In1.Cu,In2.Cu,B.Cu,F.Paste,B.Paste,F.Silkscreen,B.Silkscreen,F.Mask,B.Mask,Edge.Cuts'
r = run('kicad-cli', 'pcb', 'export', 'gerbers', '--layers', layers, '--subtract-soldermask', '--use-drill-file-origin', '-o', g + '/', pcb)
print(r.stdout[-300:], r.stderr[-300:])
run('kicad-cli', 'pcb', 'export', 'drill', '--format', 'excellon', '--excellon-separate-th', '--generate-map', '--map-format', 'gerberx2', '-o', g + '/', pcb)
run('kicad-cli', 'pcb', 'export', 'pos', '--format', 'csv', '--units', 'mm', '--side', 'both', '-o', os.path.join(out, '04_Gerber', 'positions_kicad.csv'), pcb)
# zip for JLC / Rezonit
import zipfile
with zipfile.ZipFile(os.path.join(out, '04_Gerber', 'CM5-DETECT_rev03_gerber.zip'), 'w', zipfile.ZIP_DEFLATED) as z:
    for f in sorted(os.listdir(g)):
        z.write(os.path.join(g, f), f)
# BOM (JLCPCB format) + CPL
rows = {}
for ref, c in sorted(C.items()):
    if c.get('dnp') or ref.startswith(('H', 'TP_', 'JP_')):
        continue
    k = (c['val'], c['fp'], c['lcsc'])
    rows.setdefault(k, []).append(ref)
with open(os.path.join(out, '04_Gerber', 'BOM_JLCPCB.csv'), 'w', newline='') as f:
    w = csv.writer(f); w.writerow(['Comment', 'Designator', 'Footprint', 'LCSC Part #'])
    for (val, fp, lc), refs in sorted(rows.items(), key=lambda kv: kv[1][0]):
        w.writerow([val, ','.join(refs), fp.split(':')[1], lc])
pos = list(csv.DictReader(open(os.path.join(out, '04_Gerber', 'positions_kicad.csv'))))
with open(os.path.join(out, '04_Gerber', 'CPL_JLCPCB.csv'), 'w', newline='') as f:
    w = csv.writer(f); w.writerow(['Designator', 'Mid X', 'Mid Y', 'Layer', 'Rotation'])
    for p in pos:
        ref = p['Ref']
        if ref in C and not C[ref].get('dnp') and not ref.startswith(('H', 'TP_', 'JP_')):
            w.writerow([ref, p['PosX'] + 'mm', p['PosY'] + 'mm', 'Top' if p['Side'] == 'top' else 'Bottom', p['Rot']])
# DRC
rep = os.path.join(out, '06_Checks_and_calculations', 'DRC_report.json')
run('kicad-cli', 'pcb', 'drc', '--format', 'json', '--severity-error', '--schematic-parity', '-o', rep, pcb)
run('kicad-cli', 'pcb', 'drc', '--format', 'json', '--severity-error', '-o', rep, pcb)
run('kicad-cli', 'pcb', 'drc', '--format', 'report', '-o', rep.replace('.json', '.txt'), pcb)
d = json.load(open(rep))
import collections
cnt = collections.Counter(v['type'] for v in d['violations'])
print('DRC errors:', dict(cnt), 'unconnected:', len(d.get('unconnected_items', [])))
# renders (3D, raytraced)
ph = os.path.join(out, '01_Photos')
for name, args in [('top', ['--side', 'top']), ('bottom', ['--side', 'bottom']),
                   ('iso_top', ['--side', 'top', '--rotate', '-35,0,25']), ('iso_bottom', ['--side', 'bottom', '--rotate', '35,0,-25'])]:
    r = run('kicad-cli', 'pcb', 'render', '-o', os.path.join(ph, name + '.png'), '--width', '1400', '--height', '1800',
            '--quality', 'high', '--background', 'opaque', '--perspective', '--zoom', '0.72', *args, pcb)
    print(name, r.returncode, r.stderr[-200:])
