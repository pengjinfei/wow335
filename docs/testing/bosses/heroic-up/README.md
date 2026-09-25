# 英雄乌特加德之巅（Utgarde Pinnacle，map 575）/ campaign

口径：ilvl 200 档（`mod-raidtest-roster-heroic5gear-n5talents-v1.conf`），英雄、5 人、`BotCheats=""`。勘测见 [SURVEY.md](SURVEY.md)。
**关键**：UP 实例脚本不用 boss 状态，进度存在自己的 `Encounters[]`（SetData/GetData：Svala=0、Gortok=1、Skadi=2、Ymiron=3）。为此 raidtest `953dab7` 新增 `FixtureInstanceData`、`EngageConfirmInstanceData`、`EngageTrigger=gameobject`、`EngageTrigger=areatrigger`。策略键 `wotlk-up`。

## Encounter 矩阵

| encounter | 场景 | 当前结论 | 状态 |
|---|---|---|---|
| Svala Sorrowgrave | `heroic-up-svala-h5g` | v2 **5/5 kill、1 死，129–137 秒**（run1109–1113）；v1 高台站位 1/3 | **完成（ilvl 200 档，完整遭遇含剧情）** |
| Gortok Palehoof | `heroic-up-gortok-h5g` | **5/5 kill、0 死，166–171 秒**（run1101–1105）；宝珠开战、四只野兽依次解冻（16/44/70/100 秒）后 Gortok 约 129 秒醒来 | **完成（ilvl 200 档，完整遭遇）** |
| Skadi the Ruthless | 未建 | 需 playerbots 实现鱼叉链（捡 GO 192539 → 在 Grauf 悬停 10 秒窗口内用东端发射器 192175–192177，三发打下）；源码 TODO；另 HARD_RESET、坦克仇恨校验需调 | **跳过，待用户确认**（改动大） |
| King Ymiron | `heroic-up-ymiron-h5g` | 基线 **1/5**（Bane 反伤占承伤 70%）→ playerbots `bef4c908` 修 Bane 停手后 **4/5**（run1096–1100，Bane 占比 39%） | **完成（ilvl 200 档，隔离：`FixtureInstanceData=2:3`）** |

## Ymiron：Bane 停手修复（playerbots `bef4c908`）

- Bane（英雄 59301）期间每次命中伊米隆都触发 59302 打全队（每次 4 人各 4–5k）。基线 run1087–1091 仅 1/5，59302 占承伤 53–70%。
- 原策略：trigger 调通用 "drop target"，但它是 AttackAction，被同一策略的 Bane multiplier 置 0，从未执行；且只清目标值，不停近战自动攻击与读条。
- 修复：新增 "ymiron bane stop attack"（停对伊米隆的自动攻击、打断对他的读条、清目标），multiplier 另压“对当前目标施法且目标是伊米隆”。已上的 DoT 仍会跳（真人同样躲不掉）。
- 结果：4/5（152–165 秒），59302 每场 104k→73k。

## Gortok：宝珠开战（raidtest `EngageTrigger=gameobject`）

- 坦克在宝珠旁 4 码的开怪点，框架代它 `GameObject::Use` Stasis Generator（188593，spawn 65513）一次 → DoAction(START) → `SetData(1, IN_PROGRESS)`，以 `EngageConfirmInstanceData=1:1` 确认；之后不 hold、不要求坦克仇恨，战斗全交 bot。横穿房间的巡逻编队 126086 组夹具移除。
- 四只小 boss 死亡不产生死亡事件（脚本以其它方式处理），但伤害/施法记录完整。

## Svala：AreaTrigger 开战（raidtest `EngageTrigger=areatrigger`）

- 唯一开关是 AT 5140（SmartTrigger）。bot 不发 CMSG_AREATRIGGER、核心无服务端扫描，框架让站在盒内的坦克走一遍 `HandleAreaTriggerOpcode`（核心自己校验盒子），`EngageConfirmInstanceData=0:1`；约 72 秒剧情后她变身 26668（guid 不变）自行攻击。
- **v1（准备点=开怪点=AT 高台）**：run1106–1108 为 1/3——她献祭后回到自己平台，全队仍站高台，双方互相够不着，NO_PATH evade（boss 3% 复位两次）。
- **v2**：准备点=AT 触发点，开怪点=她房间地面 (296.6,-335,85.78)；触发后框架在开战前让全队按 mmap 寻路**走**到开怪点（不传送，开战后不干预）。已验证 40 秒时 5 人全到位。**5/5**（run1109–1113，129–137 秒）。
- bot 缺口（记录）：献祭期间不会优先打 Ritual Channeler，被献祭者会死（run1095/1106 各 1 死）。
