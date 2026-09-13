# normal5-v1：WLK 普通五人本毕业基线

用户 2026-09-10：「感觉现在击杀太容易了，把装备降低为普通5人副本毕业吧」。本档位与
[heroic5-v1](../heroic5-v1/README.md) **并存**，不覆盖、不替换；英雄档的既有证据全部保留。

阵容与 heroic5-disc-v1 完全相同（同职业、同种族、同天赋、同雕文、同附魔、同补给），
**只有装备档位不同**，因此两档之间的差异可以单独归因到装等。

| 槽位 | 专精 | 角色名 |
|---|---|---|
| 0 | 防护圣骑士（矮人） | Raidteanfive |
| 1 | 戒律牧师 | Raidtebnfive |
| 2 | 战斗潜行者 | Raidtecnfive |
| 3 | 火焰法师 | Raidtednfive |
| 4 | 元素萨满 | Raidteenfive |

## 装等口径

WLK 普通五人本掉落上限是 **ilvl 187**（英雄本才到 200）。蓝图 `MaxItemLevel = 187`，
夹具会对每件超标装备报错，所以这条线由框架强制，不靠人工核对。

- 85 件装备，装等分布：187×55、183×2、179×3、175×8、174×15、150×2。平均 180.4–183.6。
- 两件 ilvl 150 是圣契/图腾（38363 Libram of Protection、38361 Lightning Rod）：
  174–187 区间内没有非 PvP、非声望门槛的圣契/图腾，只能下探到 150。
- 品质全部 Quality=3（蓝色），无史诗、无团本、无冠军试炼/ICC。

## 来源核验

[ITEMS.json](ITEMS.json) 的 `sources` 全部来自本地世界库与 Spell.dbc，**85 件无一为空**：

| 类型 | 条数 | 查询依据 |
|---|---|---|
| drop | 40 | `creature_loot_template` + `reference_loot_template` → `creature_template.lootid` |
| quest | 34 | `quest_template.RewardItem*` / `RewardChoiceItemID*` |
| chest | 27 | `gameobject_loot_template`（含 reference 链）→ `gameobject_template.data1` |
| crafted | 26 | Spell.dbc `EffectItemType`（字段 107–109）反查制造法术名 |
| vendor | 4 | `npc_vendor` → `creature_template` |

一件物品可有多个来源，故条数之和大于 85。

选品是规则驱动而非逐件手挑：`ilvl 174–187 ∧ Quality=3 ∧ RequiredLevel≤80 ∧ 职业可用 ∧
护甲类型匹配 ∧ RequiredReputationFaction=RequiredSpell=RequiredHonorRank=RequiredCityRank=0`，
再按专精权重排序取最高分；武器按已验证的英雄档布局逐职业限定（坦克/潜行者单手+副手、
法师主手+副手、萨满单手+盾）。

原先选中的 44392 Necklace of Permeation 在本地世界库里**没有任何来源**（不掉落、不出售、
非工艺、非任务），已换成 36988 Chaotic Spiral Amulet（Loken 掉落）与 36943 Timeless Beads
of Eternos（Drakos the Interrogator 掉落），两者均 ilvl 187。

## 宝石与附魔

- 附魔 ID 与 heroic5-disc-v1 **逐槽相同**，保证只有装等一个变量。
- 宝石降一档：英雄档用 ilvl 80 稀有（40xxx Scarlet Ruby / Sky Sapphire / Monarch Topaz 等），
  本档用 ilvl 70 优秀（39xxx Bloodstone / Sun Crystal / Chalcedony / Shadow Crystal /
  Huge Citrine），切工尽量对应。
- 本档只有 5 个插槽（英雄档有 14 个），因为普通本装备带槽的比例低得多：
  slot0 头 1 槽、slot2 项链 1 槽 + 戒指 1 槽、slot3 戒指 1 槽、slot4 戒指 1 槽。
- 夹具要求**每个插槽必须填满**（`RosterBuilder.cpp` 的 `missing/invalid gem` 校验），
  所以带槽装备必须声明宝石；这不是为了增益，是入场完整性检查。紫色/橙色复合宝石
  同时满足红/蓝或红/黄插槽奖励，故优先选用。

## 与英雄档的差距（同专精对比）

| 指标 | heroic5 防骑 | normal5 防骑 | 变化 |
|---|---|---|---|
| 平均装等 | 200.0 | 183.6 | −8.2% |
| 耐力 | 1248 | 977 | **−21.7%** |
| 力量 | 646 | 563 | −12.8% |
| 护甲 | 19976 | 19200 | −3.9% |
| 防御等级 | 610 | 648 | +6.2%（普通档蓝装堆防御更多） |

| 指标 | heroic5 潜行者 | normal5 潜行者 | 变化 |
|---|---|---|---|
| 平均装等 | 200.0 | 182.2 | −8.9% |
| 敏捷 | 637 | 584 | −8.3% |
| 耐力 | 732 | 584 | −20.2% |
| 命中等级 | 350 | 136 | **−61.1%** |

实测生命上限（run 316 快照，与英雄档 Ingvar 记录里的坦克 28,884 对照）：

| 槽位 | 专精 | 生命上限 | 防御技能 | 有效 cheat |
|---|---|---:|---:|---:|
| 0 | paladin_prot | 20,974（英雄档 28,884，**−27.4%**） | 550（门槛 535） | 0 |
| 1 | priest_disc | 14,270 | 400 | 0 |
| 2 | rogue_combat | 14,644 | 400 | 0 |
| 3 | mage_fire | 13,963 | 400 | 0 |
| 4 | shaman_elemental | 14,119 | 400 | 0 |

坦克生命上限下降 27%、DPS 命中大幅缩水，是本档位难度上升的主要来源。P2 的
`59709` effect 0（暗影，26,249–33,750）现在**超过坦克满血**，英雄档时它只是逼近上限。

## 配置文件

- 阵容：`modules/mod-raidtest/conf/mod-raidtest-roster-normal5-v1.conf.dist`
- 场景：`modules/mod-raidtest/conf/mod-raidtest-scenario-heroic-uk-ingvar-n5.conf.dist`
  （scenario key `heroic-uk-ingvar-n5`，与 `heroic-uk-ingvar-disc` 除阵容外完全一致）

运行时必须核对安装后的 `env/dist/etc/modules/*.conf`，`.conf.dist` 不会自动生效。

## 实测状态

装备夹具已通过：run 315 的 2 场 × 5 份快照全部 `valid=true`（宝石、附魔、装等上限、
物品可用性、声望门槛均过）。

run 316 的 attempt 1（团灭）与 attempt 4（击杀）共 10 份实际快照存于
[snapshots](snapshots)，汇总为 [AUDIT.json](AUDIT.json)：五人均 17 件装备、
最高装等 187、6 雕文、有效 cheat = 0，两场逐角色指纹一致。

击杀率：**run 316 = 1/5（20%）**，对照英雄档同场景 8/8。详见
[../../bosses/heroic-uk-ingvar/README.md](../../bosses/heroic-uk-ingvar/README.md)。

## 基线改动记录

- **2026-09-13（用户拍板）**：戒律牧师槽 `Supplies` 加 **33448 符文法力药水**（原 `44615,33443,33445` → 加 `33448`）。
  起因：阿努巴拉克 run 460 证实牧师 150–210 秒耗尽法力、`mana potion` 动作 187 次 IMPOSSIBLE 是包里没药水。
  药水受一场一瓶限制，约 +4.3k 蓝。其他四槽未加；法师槽同样缺药水且 90–120 秒见底，是下一候选。
  此前所有 run（≤460）都是无药水基线，对比时注意。详见 [阿努巴拉克记录第五轮](../../bosses/heroic-an-anubarak/README.md)。
- **2026-09-13（用户拍板）**：火法槽 `Supplies` 也加 **33448**（原 `17020,17031,33443,33445` → 加 `33448`）。
  起因：run 461 法师每场 90–120 秒法力归零（活体炸弹铺小怪 + 暴风雪 74% 基础法力）。配合 AN 层群攻归零后 run 462 击杀场法师 DPS 1243。
