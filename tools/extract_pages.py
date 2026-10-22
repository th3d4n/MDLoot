import re,html,sys,glob,os
def lines(f):
    s=open(f).read()
    t=re.sub(r'<script.*?</script>','',s,flags=re.S)
    t=re.sub(r'<style.*?</style>','',t,flags=re.S)
    t=re.sub(r'<[^>]+>','\n',t)
    t=html.unescape(t)
    return [l.strip() for l in t.split('\n') if l.strip()]
for f in sorted(glob.glob(sys.argv[1])):
    L=lines(f)
    # start at second occurrence breadcrumb "Artifacts"/"Armor" then item
    try: i=L.index('Search')
    except: i=0
    out=L[i:]
    # cut ad block & enchantments/effects
    txt='\n'.join(out)
    txt=re.sub(r'MetaBot Desktop\nFree · Windows.*?More info\nValidated by Overwolf — anti-cheat safe\n','',txt,flags=re.S)
    txt=re.sub(r'MetaBot Desktop\nFind the best place.*?Items, sets & books to farm\n\d+\n','',txt,flags=re.S)
    txt=re.sub(r'Enchantments that fire when you use.*?(?=Where to find|Similar to|$)','[ENCH/EFFECTS CUT]\n',txt,flags=re.S)
    txt=re.sub(r'\nSimilar to .*','',txt,flags=re.S)
    print('=====',os.path.basename(f)); print(txt)
