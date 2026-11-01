# -*- coding: utf-8 -*-
"""BOM cost from live JLCPCB/LCSC price tiers for 10 and 10 000 boards -> ../docs/BOM_cost.csv + summary"""
import sys, os, csv, json
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE); sys.path.insert(0, HERE + '/../../../tools')
from design import C
import jlc

groups = {}
for ref, c in C.items():
    if c.get('dnp') or not c['lcsc']:
        continue
    k = (c['lcsc'], c['val'])
    groups.setdefault(k, []).append(ref)
cache_f = HERE + '/.price_cache.json'
cache = json.load(open(cache_f)) if os.path.exists(cache_f) else {}
EXTRA = {   # parts not orderable through JLC API: market prices (2026-11, LCSC / AliExpress / Chip-Dip)
    'SCCDQR2R7106': [(1, 0.90), (1000, 0.45)],                 # 10F 2.7V supercap (Jianghai / Kamcap)
    'Amphenol 10164227-1001A1RLF x2 (C6782225)': [(1, 2 * 2.60), (1000, 2 * 1.40)],
}


def price(code, qty):
    if code in EXTRA:
        tiers = EXTRA[code]
    else:
        if code not in cache:
            r = jlc.lookup(code)
            cache[code] = dict(tiers=r['prices'] if r else [], stock=r['stock'] if r else 0, mpn=r['mpn'] if r else '', mfr=r['mfr'] if r else '')
        tiers = cache[code]['tiers']
    p = None
    for q, pr in tiers:
        if qty >= q:
            p = pr
    return p if p is not None else (tiers[0][1] if tiers else None)


rows = []
tot = {10: 0.0, 10000: 0.0}
for (code, val), refs in sorted(groups.items(), key=lambda kv: kv[1][0]):
    n = len(refs)
    r = {'refs': ' '.join(sorted(refs)), 'qty': n, 'value': val, 'lcsc': code}
    for B in (10, 10000):
        p = price(code, n * B)
        r['unit_%d' % B] = p
        if p:
            tot[B] += p * n
    r['mfr'] = cache.get(code, {}).get('mfr', ''); r['mpn'] = cache.get(code, {}).get('mpn', ''); r['stock'] = cache.get(code, {}).get('stock', '')
    rows.append(r)
json.dump(cache, open(cache_f, 'w'))
os.makedirs(HERE + '/../docs', exist_ok=True)
with open(HERE + '/../docs/BOM_cost.csv', 'w', newline='') as f:
    w = csv.DictWriter(f, fieldnames=['refs', 'qty', 'value', 'lcsc', 'mfr', 'mpn', 'stock', 'unit_10', 'unit_10000'])
    w.writeheader(); w.writerows(rows)
print('BOM components (no CM5) per board: $%.2f @10 boards, $%.2f @10000 boards' % (tot[10], tot[10000]))
print('lines', len(rows), 'low stock:', [(r['lcsc'], r['value'][:30], r['stock']) for r in rows if isinstance(r['stock'], int) and r['stock'] < 10 * r['qty'] * 2])
