# -*- coding: utf-8 -*-
"""Build the 3 order packages (V1 RU Rezonit, V2 CN JLCPCB, V3 Hybrid RK3576) from the routed board.
usage: /usr/bin/python3 make_packages.py CM5-DETECT_rev03.kicad_pcb ../../packages"""
import os, sys, shutil, subprocess, zipfile, json, glob
HERE = os.path.dirname(os.path.abspath(__file__))
pcb = os.path.abspath(sys.argv[1]); OUT = os.path.abspath(sys.argv[2])
ROOT = os.path.dirname(HERE)
os.makedirs(OUT, exist_ok=True)
run = lambda *a: subprocess.run(list(a), capture_output=True, text=True)

# common fab outputs once
common = os.path.join(OUT, '_common')
if os.path.exists(common): shutil.rmtree(common)
r = run(sys.executable, HERE + '/make_fab.py', pcb, common); print(r.stdout[-1500:], r.stderr[-800:])

# hybrid render: same board with an RK3576 module model
import pcbnew
b = pcbnew.LoadBoard(pcb)
m1 = b.FindFootprintByReference('M1')
for md in m1.Models():
    if 'CM5_with_cooler' in md.m_Filename:
        md.m_Filename = md.m_Filename.replace('CM5_with_cooler', 'RK3576_module_with_cooler')
hyb = os.path.join(HERE, 'CM5-DETECT_rev03_hybrid_render.kicad_pcb')
b.Save(hyb)
hyb_ph = os.path.join(OUT, '_hyb_photos'); os.makedirs(hyb_ph, exist_ok=True)
for name, args in [('top', ['--side', 'top']), ('iso_top', ['--side', 'top', '--rotate', '-35,0,25'])]:
    run('kicad-cli', 'pcb', 'render', '-o', os.path.join(hyb_ph, name + '.png'), '--width', '1400', '--height', '1800',
        '--quality', 'high', '--background', 'opaque', '--perspective', *args, hyb)
os.remove(hyb)

VAR = {
    'V1_RU_Rezonit_CM5': dict(module='Raspberry Pi CM5 (CM5108032: 8 GB LPDDR4X, 32 GB eMMC, Wi-Fi)', fab='Резонит (Россия)',
                              stack='Резонит «4 Layers (1,5mm 18um Tg150 Impedance)», толщина 1,5 мм', photos=None),
    'V2_CN_JLCPCB_CM5': dict(module='Raspberry Pi CM5 (CM5108032: 8 GB LPDDR4X, 32 GB eMMC, Wi-Fi)', fab='JLCPCB (Китай)',
                             stack='JLC04161H-3313, 1,6 мм, Impedance Control = Yes (100 Ом диф / 90 Ом USB)', photos=None),
    'V3_HYBRID_RK3576': dict(module='CM5-совместимый модуль RK3576: Radxa CM4 / ArmSoM CM5 / Geniatech XPI-3576-CM5 (8 ГБ, eMMC 32–64 ГБ, NPU 6 TOPS)',
                             fab='Резонит или JLCPCB (та же плата)', stack='как V1 или V2', photos=hyb_ph),
}
for name, v in VAR.items():
    d = os.path.join(OUT, name)
    if os.path.exists(d): shutil.rmtree(d)
    os.makedirs(d)
    # 01 photos
    shutil.copytree(os.path.join(common, '01_Photos'), os.path.join(d, '01_Photos'))
    if v['photos']:
        for f in glob.glob(v['photos'] + '/*.png'):
            shutil.copy(f, os.path.join(d, '01_Photos', 'hybrid_RK3576_' + os.path.basename(f)))
    # 02 components
    os.makedirs(os.path.join(d, '02_Components'))
    shutil.copy(os.path.join(common, '04_Gerber', 'BOM_JLCPCB.csv'), os.path.join(d, '02_Components', 'BOM.csv'))
    if os.path.exists(os.path.join(ROOT, 'docs', 'BOM_cost.csv')):
        shutil.copy(os.path.join(ROOT, 'docs', 'BOM_cost.csv'), os.path.join(d, '02_Components', 'BOM_with_prices.csv'))
    open(os.path.join(d, '02_Components', 'MODULE.md'), 'w').write('# Вычислительный модуль\n\n' + v['module'] +
        '\n\nМодуль покупается отдельно и вставляется в разъёмы 2×100 pin (Amphenol 10164227), 4 винта M2.5.\n')
    # 03 functionality
    os.makedirs(os.path.join(d, '03_Functionality'))
    for f in ('FUNCTIONALITY.md', 'FAB_NOTES.md'):
        shutil.copy(os.path.join(ROOT, 'docs', f), os.path.join(d, '03_Functionality', f))
    for f in ('VARIANTS.md', 'COST.md'):
        shutil.copy(os.path.join(ROOT, '..', f), os.path.join(d, '03_Functionality', f))
    shutil.copytree(os.path.join(ROOT, 'firmware'), os.path.join(d, '03_Functionality', 'firmware'))
    # 04 gerber
    shutil.copytree(os.path.join(common, '04_Gerber'), os.path.join(d, '04_Gerber'))
    # 05 kicad project
    kd = os.path.join(d, '05_KiCad_project'); os.makedirs(kd)
    shutil.copy(pcb, os.path.join(kd, 'CM5-DETECT_rev03.kicad_pcb'))
    for f in ('design.py', 'build_board.py', 'make_fab.py', 'cost.py', 'impedance.py', 'gen3d.py'):
        shutil.copy(os.path.join(HERE, f), kd)
    shutil.copytree(os.path.join(HERE, 'lib'), os.path.join(kd, 'lib'), ignore=shutil.ignore_patterns('*.zip'))
    shutil.copytree(os.path.join(HERE, 'CM5IO.3dshapes'), os.path.join(kd, 'CM5IO.3dshapes'))
    # 06 checks
    shutil.copytree(os.path.join(common, '06_Checks_and_calculations'), os.path.join(d, '06_Checks_and_calculations'))
    r = run(sys.executable, HERE + '/impedance.py'); open(os.path.join(d, '06_Checks_and_calculations', 'impedance.txt'), 'w').write(r.stdout)
    open(os.path.join(d, 'README.md'), 'w').write(
        '# CM5-DETECT rev0.3 — %s\n\n* Завод: %s\n* Стек: %s\n* Модуль: %s\n\n'
        'Папки: 01_Photos (рендеры), 02_Components (BOM), 03_Functionality (функции, подключение, заказ, прошивки),\n'
        '04_Gerber (Gerber/сверловка/BOM/CPL для завода), 05_KiCad_project (KiCad 9 + генераторы), 06_Checks_and_calculations (DRC, импеданс).\n'
        % (name, v['fab'], v['stack'], v['module']))
    z = os.path.join(OUT, name + '.zip')
    with zipfile.ZipFile(z, 'w', zipfile.ZIP_DEFLATED) as zf:
        for root, _, files in os.walk(d):
            for f in files:
                p = os.path.join(root, f); zf.write(p, os.path.join(name, os.path.relpath(p, d)))
    print(name, os.path.getsize(z) // 1024, 'KB')
