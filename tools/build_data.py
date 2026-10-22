"""Merge Minecraft Dungeons II stat sources into one data.json.
Sources:
  MOD = operator1212/dungeons2-stats-mod stats.tsv (commit 2026-10-02)
  MB  = metabot.gg tables, game build 1.1.1.0 (raw HTML fetched by tools/fetch_sources.sh)
Every value is copied from a source; the only computed things are conflict flags.
"""
import re, html, json, sys

import os
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
RAW = os.path.join(ROOT, 'sources') + '/'
TSV = RAW + 'stats.tsv'
ARCH = ['Fighter', 'Mage', 'Ranger', 'Summoner', 'Support', 'Tank', 'Trickster', 'Utility']

def tables(f):
    s = open(RAW + f, encoding='utf-8').read()
    out = []
    for t in re.findall(r'<table.*?</table>', s, re.S):
        rows = []
        for r in re.findall(r'<tr.*?</tr>', t, re.S):
            rows.append([html.unescape(re.sub(r'<[^>]+>', '', c)).strip()
                         for c in re.findall(r'<t[hd][^>]*>(.*?)</t[hd]>', r, re.S)])
        rows = [r for r in rows if r and r[0] and r[0] != 'No Results']
        out.append((rows[0], rows[1:]))
    return out

def split_arch(s):
    found = re.findall('|'.join(ARCH), s)
    assert ''.join(found) == s.replace(' ', ''), s
    return found

def num(s):
    m = re.search(r'-?\d+(\.\d+)?', s or '')
    return float(m.group()) if m else None

# ---------- MOD ----------
mod = {}
for line in open(TSV, encoding='utf-8'):
    if line.startswith('#') or not line.strip():
        continue
    p = line.rstrip('\n').split('\t')
    mod[p[3]] = p[4].split('\\n')

def parse_mod_melee(lines):
    d = {}
    m = re.match(r'Damage: (.*?)(?: \((\d+(?:\.\d+)?) per combo\))?$', lines[0])
    d['hits'] = m.group(1)
    if m.group(2):
        d['combo'] = float(m.group(2))
    else:  # "40 per hit" single attack
        d['combo'] = num(m.group(1))
    m = re.match(r'Combo time: ([\d.]+)s \| Base DPS: ([\d.]+)', lines[1])
    d['combo_time'] = float(m.group(1)); d['dps'] = float(m.group(2))
    m = re.match(r'Reach: (\d+) \| Jump attack: ([\d.]+)', lines[2])
    d['reach'] = int(m.group(1)) / 100.0; d['jump'] = float(m.group(2))
    return d

def parse_mod_ranged(lines):
    d = {}
    m = re.match(r'Damage: ([\d.]+) per arrow(?: x(\d+) arrows)?', lines[0])
    d['per_arrow'] = float(m.group(1)); d['arrows'] = int(m.group(2) or 1)
    d['shot'] = d['per_arrow'] * d['arrows']
    m = re.match(r'Fire rate: ([\d.]+)s \| Ammo: (\d+) \| Reload: ([\d.]+)s', lines[1])
    d['rate'] = float(m.group(1)); d['ammo'] = int(m.group(2)); d['reload'] = float(m.group(3))
    if len(lines) > 2:
        m = re.match(r'Charged shot: ([\d.]+)s \(x(\d+) dmg\)', lines[2])
        d['charge'] = f"{m.group(1)}s charge, x{m.group(2)} damage"
    return d

# ---------- MB ----------
wt = tables('weapons.html')
mel_hdr, mel = wt[1]; rng_hdr, rng = wt[2]
assert mel_hdr[:6] == ['Weapon', 'Weight', 'Archetype', 'Combo damage', 'Attacks', 'DPS']
assert rng_hdr[:5] == ['Weapon', 'Type', 'Shot damage', 'Time between shots', 'Burst DPS']

ut = tables('uniques.html')[0]
assert ut[0] == ['Item', 'Type', 'Base item', 'Effect']
uniq = {r[0]: {'base': r[2], 'effect': r[3], 'type': r[1]} for r in ut[1]}
unique_of = {v['base']: k for k, v in uniq.items()}

conflicts_log = []
def cmp(name, field, a, b, tol):
    if a is None or b is None:
        return None
    if abs(a - b) > tol:
        conflicts_log.append(f"{name}: {field} mod={a} metabot={b}")
        return {'field': field, 'mod': a, 'mb': b}
    return None

weapons = []
for r in mel:
    name, weight, arch, combo, attacks, dps, reach, arc = r[:8]
    w = {'name': name, 'kind': 'melee', 'weight': weight if weight != '—' else None,
         'arch': split_arch(arch),
         'mb': {'combo': num(combo), 'attacks': int(num(attacks)), 'dps': num(dps),
                'dps_est': dps.startswith('≈'), 'reach': num(reach), 'arc': arc}}
    if name in mod:
        w['mod'] = parse_mod_melee(mod[name])
    c = []
    if 'mod' in w:
        for f, tol in (('combo', 0.01), ('dps', 0.15), ('reach', 0.06)):
            x = cmp(name, f, w['mod'][f], w['mb'][f], tol)
            if x: c.append(x)
    w['conflicts'] = c
    weapons.append(w)

for r in rng:
    name, typ, shot, rate, bdps, ammo, rnge = r[:7]
    w = {'name': name, 'kind': 'ranged', 'weight': typ, 'arch': [],
         'mb': {'shot': num(shot), 'rate': num(rate), 'dps': num(bdps), 'ammo': int(num(ammo)), 'range': num(rnge)}}
    if name in mod:
        w['mod'] = parse_mod_ranged(mod[name])
    c = []
    if 'mod' in w:
        for f, tol in (('shot', 0.01), ('rate', 0.001), ('ammo', 0)):
            x = cmp(name, f, w['mod'][f], w['mb'][f], tol)
            if x: c.append(x)
    w['conflicts'] = c
    weapons.append(w)

for w in weapons:
    if w['name'] in uniq:
        w['unique'] = True; w['base'] = uniq[w['name']]['base']; w['effect'] = uniq[w['name']]['effect']
    elif w['name'] in unique_of:
        w['unique_version'] = unique_of[w['name']]

# Unique vs base differences (from MOD and MB raw values; both reported, no inference)
byname = {w['name']: w for w in weapons}
for w in weapons:
    if not w.get('unique'): continue
    b = byname.get(w['base'])
    if not b: continue
    diffs = []
    keys = ('combo', 'dps', 'reach') if w['kind'] == 'melee' else ('shot', 'rate', 'ammo')
    for k in keys:
        if w['mb'].get(k) != b['mb'].get(k):
            diffs.append({'field': k, 'unique': w['mb'].get(k), 'base': b['mb'].get(k), 'src': 'mb'})
    if 'mod' in w and 'mod' in b:
        for k in (('hits', 'combo_time', 'jump') if w['kind'] == 'melee' else ('reload',)):
            if w['mod'].get(k) != b['mod'].get(k):
                diffs.append({'field': k, 'unique': w['mod'].get(k), 'base': b['mod'].get(k), 'src': 'mod'})
    w['vs_base'] = diffs

# ---------- ARMOR ----------
at = tables('armor.html')[0]
assert at[0] == ['Armor piece', 'Slot', 'Weight', 'Archetype', 'Set']
st = tables('sets.html')
best_area = {r[0]: r[1] for r in st[2][1]}
armor = []
for r in at[1]:
    name, slot, weight, arch, aset = r
    a = {'name': name, 'slot': slot, 'weight': weight, 'arch': split_arch(arch), 'set': aset,
         'best_area': best_area.get(aset)}
    # mod archetype cross-check (case-insensitive name match; "Disciple mask" in mod)
    mk = next((k for k in mod if k.lower() == name.lower()), None)
    if mk:
        ma = re.match(r'Archetypes: (.*?) \(', mod[mk][0]).group(1).split(' + ')
        if sorted(ma) != sorted(a['arch']):
            conflicts_log.append(f"{name}: archetypes mod={ma} metabot={a['arch']}")
            a['conflicts'] = [{'field': 'archetypes', 'mod': ' + '.join(ma), 'mb': ' + '.join(a['arch'])}]
    else:
        conflicts_log.append(f"{name}: not in mod file")
    if name in uniq:
        a['unique'] = True; a['base'] = uniq[name]['base']; a['effect'] = uniq[name]['effect']
    elif name in unique_of:
        a['unique_version'] = unique_of[name]
    armor.append(a)

pool_hdr, pool_rows = tables('armor.html')[1]
assert pool_hdr == ['Archetype', 'Sets', 'Effects in pool'], pool_hdr
pools = {r[0]: int(r[2]) for r in pool_rows}

# ---------- ARTIFACTS ----------
arts = json.load(open(os.path.join(ROOT, 'data', 'artifacts.json'), encoding='utf-8'))['artifacts']

# ---------- coverage checks ----------
mod_weapons = [k for k, v in mod.items() if v[0].startswith('Damage')]
missing_mb = [k for k in mod_weapons if k not in byname]
assert not missing_mb, missing_mb
print('melee', sum(w['kind'] == 'melee' for w in weapons), 'ranged', sum(w['kind'] == 'ranged' for w in weapons))
print('armor', len(armor), 'artifacts', len(arts), 'uniques', len(uniq))
print('uniques matched', sum(1 for w in weapons if w.get('unique')) + sum(1 for a in armor if a.get('unique')))
print('--- conflicts/notes ---'); print('\n'.join(conflicts_log))
print('--- unique vs base differences ---')
for w in weapons:
    if w.get('vs_base'): print(w['name'], 'vs', w['base'], w['vs_base'])

json.dump({'weapons': weapons, 'armor': armor, 'artifacts': arts,
           'pools': pools, 'meta': {'mod_commit': '2026-10-02', 'mb_build': '1.1.1.0', 'pulled': '2026-10-22'}},
          open(os.path.join(ROOT, 'data', 'data.json'), 'w', encoding='utf-8'), ensure_ascii=False)
