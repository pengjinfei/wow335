import re, collections, sys
path=sys.argv[1]; offset=int(sys.argv[2]) if len(sys.argv)>2 else 0
act=re.compile(r"(\w+) A:(.+?) - (OK|FAILED|IMPOSSIBLE|USELESS|PREREQ)\b")
yld=re.compile(r"cast-vs-move bot=(\w+) spell=(\d+) \((.*?)\) generator=(\d+) issuer=(.*?) intent=(\d) result=(\w+)")
a=collections.defaultdict(collections.Counter); by_spell=collections.Counter(); by_issuer=collections.Counter()
with open(path,errors='ignore') as f:
    f.seek(offset)
    for line in f:
        m=act.search(line)
        if m: a[(m.group(1),m.group(2).strip())][m.group(3)]+=1; continue
        m=yld.search(line)
        if m:
            by_spell[(m.group(1),m.group(3),m.group(7))]+=1
            by_issuer[(m.group(5),m.group(6),m.group(4),m.group(7))]+=1
keys=["greater heal on party","flash heal on party","penance on party","power word: shield on party","renew on party",
      "prayer of mending on party","shoot","anub'arak dodge impale","anub'arak dodge pound","combat formation move","flee","reach spell"]
print("=== action results (all bots, filtered)")
for (bot,name),c in sorted(a.items()):
    if name in keys: print(f"{bot:14s} {name:32s} OK={c['OK']:4d} FAILED={c['FAILED']:4d} IMPOSSIBLE={c['IMPOSSIBLE']:4d} USELESS={c['USELESS']:4d} PREREQ={c['PREREQ']:4d}")
print("=== cast-vs-move by bot/spell/result")
for k,v in sorted(by_spell.items(), key=lambda kv:-kv[1])[:30]: print(v, k)
print("=== cast-vs-move by issuer/intent/generator/result")
for k,v in sorted(by_issuer.items(), key=lambda kv:-kv[1])[:30]: print(v, k)
print("=== top OK actions per bot")
tot=collections.defaultdict(collections.Counter)
for (bot,name),c in a.items(): tot[bot][name]=c['OK']
for bot,c in sorted(tot.items()): print(bot, c.most_common(8))
