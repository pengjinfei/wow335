import re, sys, collections
log=sys.argv[1]
src=open('/Users/nowcoder/IdeaProjects/github/wow335/azerothcore-wotlk/src/server/shared/SharedDefines.h').read()
m=re.search(r'enum SpellCastResult[^{]*\{(.*?)\};', src, re.S)
val=0; names={}
for line in m.group(1).splitlines():
    line=line.split('//')[0].strip().rstrip(',')
    if not line or line.startswith('#'): continue
    if '=' in line:
        n,v=[x.strip() for x in line.split('=')]
        try: val=int(v,0)
        except: continue
    else: n=line
    names[val]=n; val+=1
pat=re.compile(r"Spell prepare failed(?: \(ground target\))?\. - (?:target name: (.*?), )?spellid: (\d+), bot name: (\w+), result: (\d+)")
byreason=collections.Counter(); byspell=collections.defaultdict(collections.Counter); bybot=collections.Counter()
for line in open(log,errors='ignore'):
    mm=pat.search(line)
    if not mm: continue
    tgt,spell,bot,res=mm.groups(); rn=names.get(int(res),res)
    byreason[rn]+=1; byspell[(bot,spell)][rn]+=1; bybot[bot]+=1
print("total prepare failures:",sum(byreason.values()), dict(bybot))
print("--- by reason"); [print(f"  {v:5d} {k}") for k,v in byreason.most_common()]
print("--- priest by spell/reason")
for (bot,spell),c in sorted(byspell.items(), key=lambda kv:-sum(kv[1].values())):
    if bot=='Raidtebnfivc': print(f"  {spell:6s}", dict(c))
print("--- others top 12")
for (bot,spell),c in sorted(byspell.items(), key=lambda kv:-sum(kv[1].values()))[:12]:
    if bot!='Raidtebnfivc': print(f"  {bot} {spell:6s}", dict(c))
