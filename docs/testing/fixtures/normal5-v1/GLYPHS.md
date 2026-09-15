# normal5-v1 雕文审计（含 heroic5-v1 / naxx-patchwerk，同一套雕文配置）

> 更新 2026-09-14。口径：Glyph ID 由 `GlyphProperties.dbc` 解出 Spell ID 与大小雕文标志，
> 名称由**运行中的 worldserver** 用 `lookup spell id <SpellID>` 打印（即当前服务端实际加载的 DBC），不依赖客户端是否在本机。

## 怎么核（别再踩的坑）

**`acore_world.glyphproperties_dbc` 表是空的，这不代表无法核验**——GlyphProperties 由核心在运行时从
`.dbc` 文件加载，SQL 里那张同名表只给自定义数据用。正确的两步：

```bash
# 1) 解 DBC：ID -> SpellID / SlotFlags（0=大雕文，1=小雕文）
python3 - <<'PY'
import struct
d=open('data/world/dbc/GlyphProperties.dbc','rb').read()
magic,rc,fc,rs,ss=struct.unpack('<4sIIII',d[:20])          # WDBC 362 4 16 1
for i in range(rc):
    gid,spell,flags,icon=struct.unpack('<4I', d[20+i*rs:20+i*rs+16])
    print(gid, spell, flags)
PY

# 2) 用运行中的核心查名字（控制台命令无前导点）
echo 'lookup spell id 63223' > /tmp/ac_world_fifo      # -> Glyph of Divine Plea
```

DBC 来源：`data/world/dbc/GlyphProperties.dbc`（362 条、字段 4、记录 16 字节，sha256 前 24 位 `11237852179c218efdba4ddb`，
与 `Spell.dbc` 同批，2026-09-03 提取）。**槽位顺序不等于「前 3 个大、后 3 个小」**，大小雕文只看 SlotFlags。

## 坦克 · 保护骑（Roster.0，`paladin_prot`）

| Glyph ID | Spell ID | 名称 | 类型 | 说明 |
|---|---|---|---|---|
| 190 | 54929 | 正义防御雕文 Glyph of Righteous Defense | **大** | 正义防御命中率 +8%（嘲讽抗性） |
| 561 | 56416 | 复仇圣印雕文 Glyph of Seal of Vengeance | **大** | 复仇圣印额外 +10 精准等级 |
| 705 | 63223 | 神圣恳求雕文 Glyph of Divine Plea | **大** | 神圣恳求期间受到伤害 −3% |
| 455 | 57955 | 圣疗术雕文 Glyph of Lay on Hands | 小 | 圣疗术冷却 −5 分钟 |
| 456 | 57947 | 侦测亡灵雕文 Glyph of Sense Undead | 小 | 对亡灵伤害 +1% |
| 457 | 57954 | 睿智雕文 Glyph of the Wise | 小 | 智慧圣印法力消耗 −50% |

**结论：三个大雕文就是防骑续蓝/仇恨的标准组合（神圣恳求 + 复仇圣印 + 正义防御），不需要动。**
坦克末段没蓝的原因不在雕文，见 [阿努巴拉克记录](../../bosses/heroic-an-anubarak/README.md) 第二十二轮：
天赋缺 精神协调 2/2 与 祈福 5/5，且神圣恳求因相关性被抢占（381 次推入队列、9 次执行）。

## 其余四人

| 角色 | Glyph ID → Spell ID | 名称（大 / 小） |
|---|---|---|
| 牧师 戒律（Roster.1） | 263→55672、255→55679、710→63235 / 460→58009、463→58228、458→57985 | **大**：真言术盾、快速治疗、苦修 / 小：坚韧、暗影魔、渐隐 |
| 盗贼 刺杀（Roster.2） | 399→56803、733→63268、791→64199 / 468→58039、469→58038、467→58033 | **大**：破甲、毁伤、毒伤 / 小：疾跑、消失、安全降落 |
| 法师 火焰（Roster.3） | 316→56368、697→63091、328→56382 / 445→57924、451→57925、611→62126 | **大**：火球术、活体炸弹、熔火之铠 / 小：奥术智慧、缓落术、冲击波 |
| 萨满 元素（Roster.4） | 226→55453、220→55451、752→63280 / 473→58059、475→58063、612→62132 | **大**：闪电箭、火舌武器、愤怒图腾 / 小：重生、水之护盾、雷霆风暴 |

（大/小按 SlotFlags 判定，不按配置里的书写顺序——本机 DBC 把冲击波/雷霆风暴标为小雕文，与常见资料站不同，以服务端加载的 DBC 为准；
`RosterBuilder` 会校验 `glyph->TypeFlags == glyphSlot->TypeFlags`，五个角色 6/6 全部应用成功，说明槽位类型与配置顺序一致。名称取自运行中服务端；效果描述为 3.3.5 标准文本，未逐条从服务端校验。）
