import re,json,os
ROOT=os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
T=os.path.join(ROOT,'tools'); SRC=os.path.join(ROOT,'sources')
ARCH={'Fighter','Mage','Summoner','Support','Tank','Trickster'}
TYPES={'Offensive','Quiver'}
ELEM={'Fire','Frost','Lightning','Poison','Soul'}
names=[l.strip() for l in open(os.path.join(T,'artifact_names.txt')) if l.strip()]
slug=lambda n:n.lower().replace("'","").replace(' ','-')
blocks={b.split('\n')[0].strip():b for b in open(os.path.join(SRC,'art.txt')).read().split('===== ')[1:]}
arts=[];notes=[]
def kv(seq):
    return [(seq[i],seq[i+1]) for i in range(0,len(seq)-1,2)]
for n in names:
    b=blocks['a_'+slug(n)+'.html']; L=b.split('\n')
    i=L.index('Artifacts'); assert L[i+1]==n and L[i+2]==n,(n,L[i+1:i+3])
    j=L.index('Cooldown',i); tags=L[i+3:j]
    hdr=L[j:L.index('Methodology',j)]
    h=dict(kv(hdr))
    ri=L.index('Read More'); desc=L[ri-1]; summ=L[ri-2]
    assert summ.startswith(n) and ('cooldown' in summ),(n,summ)
    tbl=re.search(r'Stat\nValue\n(.*?)\nData from the',b,re.S).group(1).split('\n')
    card=re.search(r'Read Less\n(.*?)\nHow .* works',b,re.S).group(1).split('\n')
    applies=None
    if 'Applies' in card: applies=[x.strip() for x in card[card.index('Applies')+1].split(',')]
    pairs=kv(tbl); t=dict(pairs)
    details=[];status=[]
    for k,v in pairs:
        if k in ('Cooldown','Soul cost','Activation','Type','Element'): continue
        if applies and k in applies: status.append(f"{k}: {v}"); continue
        details.append(f"{k}: {v}")
    # card-only extras
    if 'Charge levels 1–3' in card:
        ci=card.index('Charge levels 1–3'); details.append(f"{card[ci-2]} (charge levels 1–3): {card[ci-1]}")
    if 'Damage per hit' in card:
        ci=card.index('Damage per hit')
        if card[ci+2].startswith("×"): details=[d if not d.startswith("Damage per hit") else f"Damage per hit: {card[ci+1]} {card[ci+2]}" for d in details]
    m=re.search(r'by charge level\nGame data\n.*?\nCharge level\n(.*?)\nHow .* compares',b,re.S)
    if m:
        rows=m.group(1).split('\n'); cols=[]
        while not rows[0].startswith('Level'): cols.append(rows.pop(0))
        w=len(cols)+1
        for r in range(0,len(rows),w):
            seg=rows[r:r+w]; details.append(seg[0]+': '+', '.join(f"{c} {v}" for c,v in zip(cols,seg[1:])))
    # where found
    wf=[]
    m=re.search(r'Share of item drops\n(.*?)\nShare = ',b,re.S)
    if m:
        r=m.group(1).split('\n')
        for x in range(0,len(r),3): wf.append(f"{r[x]} (rec. lvl {r[x+1]}, {r[x+2]} of item drops)")
    for q in re.findall(r'Quest reward\n(.*)',b): wf.append(f"Quest reward: {q}")
    elem=t.get('Element') or h.get('Element')
    tagelem=[x for x in tags if x in ELEM]
    if elem is None and tagelem: elem=None
    typ=t.get('Type')
    unknown=[x for x in tags if x not in ARCH|TYPES|ELEM]
    if unknown: notes.append(f"{n}: unrecognized header tags {unknown}")
    if tagelem and elem and tagelem!=[elem]: notes.append(f"{n}: tag element {tagelem} vs table element {elem}")
    if tagelem and not elem: notes.append(f"{n}: element tag {tagelem} but no Element row")
    sc=h.get('Soul cost'); 
    if 'Soul cost' in t and t['Soul cost']!=sc: notes.append(f"{n}: soul cost mismatch")
    if t.get('Cooldown')!=h.get('Cooldown'): notes.append(f"{n}: cooldown mismatch")
    num=lambda s: None if s is None else (float(s.replace(' s','')) if '.' in s else int(s.replace(' s','')))
    act=h.get('Activation')
    a=dict(name=n,url=f"https://metabot.gg/en/minecraft-dungeons-2/artifacts/{slug(n)}",
        description=desc,cooldown_s=num(h.get('Cooldown')),soul_cost=None if sc is None else int(sc),
        activation=None if act in (None,'—') else act, type=typ,element=elem,
        archetypes=[x for x in tags if x in ARCH], applies_status=status or None,
        details=details, where_found='; '.join(wf) if wf else None)
    if act=='—': notes.append(f"{n}: Activation shown as '—' on page; recorded null")
    if sc is None: notes.append(f"{n}: page shows no Soul cost field (artifacts index lists 0); recorded null")
    arts.append(a)
armor=[]
ab={b.split('\n')[0].strip():b for b in open(os.path.join(SRC,'arm.txt')).read().split('===== ')[1:]}
for n in [l.strip() for l in open(os.path.join(T,'armor_extra_names.txt')) if l.strip()]:
    L=ab['r_'+slug(n)+'.html'].split('\n')
    assert n in L
    si=L.index('Slot'); wi=L.index('Weight')
    armor.append(dict(name=n,slot=L[si+1],weight=L[wi+1]))
notes.append("All 40 artifact pages and 12 armor pages returned HTTP 200 at the guessed slugs; data from game build 1.1.1.0 per page footer.")
notes.append("Archetype vs type split uses the artifacts index filters: Type = Offensive/Quiver, Archetype = Fighter/Mage/Summoner/Support/Tank/Trickster. 'type' is null when the page's stat table shows no Type row.")
notes.append("No artifact page shows heal % or buff % values; status-effect rows are text descriptions only (in applies_status).")
json.dump(dict(artifacts=arts,armor_extra=armor,notes=notes),open(os.path.join(ROOT,'data','artifacts.json'),'w'),indent=2,ensure_ascii=False)
print(len(arts),len(armor)); print('\n'.join(notes))
