# -*- coding: utf-8 -*-
"""CM5-DETECT rev0.4 factory package (run on a machine with kicad-cli 9):
   python3 make_fab_rev04.py CM5-DETECT_rev04.kicad_pcb fab_rev04
Outputs: Gerber X2 + Excellon (PTH/NPTH) zip, positions (KiCad + JLC CPL), BOM files, DRC report, renders, STEP."""
import os, sys, csv, json, zipfile, subprocess, collections
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
from design import C
pcb, out = os.path.abspath(sys.argv[1]), os.path.abspath(sys.argv[2])
run = lambda *a: subprocess.run(list(a), check=False, capture_output=True, text=True)
g = os.path.join(out, 'gerber'); os.makedirs(g, exist_ok=True)
for f in os.listdir(g):
    os.remove(os.path.join(g, f))
layers = 'F.Cu,In1.Cu,In2.Cu,B.Cu,F.Paste,B.Paste,F.Silkscreen,B.Silkscreen,F.Mask,B.Mask,Edge.Cuts'
r = run('kicad-cli', 'pcb', 'export', 'gerbers', '--layers', layers, '--subtract-soldermask', '-o', g + '/', pcb)
print('gerbers', r.returncode, r.stderr[-200:])
r = run('kicad-cli', 'pcb', 'export', 'drill', '--format', 'excellon', '--excellon-separate-th', '--generate-map', '--map-format', 'gerberx2', '-o', g + '/', pcb)
print('drill', r.returncode, r.stderr[-200:])
zp = os.path.join(out, 'CM5-DETECT_rev04_gerber.zip')
with zipfile.ZipFile(zp, 'w', zipfile.ZIP_DEFLATED) as z:
    for f in sorted(os.listdir(g)):
        z.write(os.path.join(g, f), f)
pos = os.path.join(out, 'positions_kicad.csv')
run('kicad-cli', 'pcb', 'export', 'pos', '--format', 'csv', '--units', 'mm', '--side', 'both', '--exclude-dnp', '-o', pos, pcb)
skip = lambda ref: ref not in C or C[ref].get('dnp') or ref.startswith(('H', 'TP_', 'JP_'))
with open(os.path.join(out, 'CPL_JLCPCB_rev04.csv'), 'w', newline='') as f:
    w = csv.writer(f); w.writerow(['Designator', 'Mid X', 'Mid Y', 'Layer', 'Rotation'])
    for p in csv.DictReader(open(pos)):
        if not skip(p['Ref']):
            w.writerow([p['Ref'], p['PosX'] + 'mm', p['PosY'] + 'mm', 'Top' if p['Side'] == 'top' else 'Bottom', p['Rot']])
subprocess.run([sys.executable, os.path.join(HERE, 'make_bom_rev04.py'), out], check=True)
rep = os.path.join(out, 'DRC_report.json')
run('kicad-cli', 'pcb', 'drc', '--format', 'json', '--severity-all', '-o', rep, pcb)
run('kicad-cli', 'pcb', 'drc', '--format', 'report', '--severity-all', '-o', rep.replace('.json', '.txt'), pcb)
d = json.load(open(rep))
cnt = collections.Counter('%s:%s' % (v['severity'], v['type']) for v in d['violations'])
summary = dict(errors=sum(v for k, v in cnt.items() if k.startswith('error')), unconnected=len(d.get('unconnected_items', [])), detail=dict(cnt))
json.dump(summary, open(os.path.join(out, 'DRC_summary.json'), 'w'), indent=1)
print('DRC', summary)
r = run('kicad-cli', 'pcb', 'export', 'step', '--subst-models', '--force', '-o', os.path.join(out, 'CM5-DETECT_rev04.step'), pcb)
print('step', r.returncode)
ph = os.path.join(out, 'renders'); os.makedirs(ph, exist_ok=True)
for name, args in [('top', ['--side', 'top']), ('bottom', ['--side', 'bottom'])]:
    r = run('kicad-cli', 'pcb', 'render', '-o', os.path.join(ph, name + '.png'), '--width', '900', '--height', '1600',
            '--quality', 'basic', '--background', 'opaque', '--zoom', '0.9', *args, pcb)
    print('render', name, r.returncode, r.stderr[-150:])
