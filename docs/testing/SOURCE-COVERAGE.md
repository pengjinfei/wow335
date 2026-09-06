# WLK 策略源码初查

基线 mod-playerbots 2f7d9f77，2026-09-06。这是静态初查，不是整本机制完整性审计或通关认证。

源码入口 `src/Ai/Raid/RaidStrategyContext.h` 和 `src/Ai/Dungeon/DungeonStrategyContext.h`（相对 mod-playerbots）。

| 团本目录 | 已发现覆盖 | 边界 |
|---|---|---|
| ICC | 12 场战斗均有专用动作，含炮艇、教授、绿龙、冰龙、巫妖王 | 覆盖广，存在直接加减光环/击杀单位等辅助路径 |
| RS | 三小首领及海里昂的内外场、传送门、切割、燃烧等 | 覆盖广，部分直接移除光环/添加加速效果 |
| Naxx | 多 boss 的站位、选目标、极性、水晶等 | Heigan 跳舞触发器和 Patchwerk 专用站位被注释；不能因有 Action 文件就认定启用 |
| Uld | 载具、鱼叉、多个守护者、米米尔隆、尤格萨隆等 | 覆盖不均，存在 cheat；未证明全 boss 覆盖 |
| OS | 火墙、裂隙、传送门、站位 | 三龙模式未实测认证 |
| EoE | 玛里苟斯站位/选目标、骑龙 | 部分火花动作被注释 |
| Ony | 深呼吸、龙尾/龙蛋、小龙等 | 未实测认证 |
| VoA | 埃玛隆多项机制及科拉隆火抗 | 局部覆盖 |
| 团本 ToC/ToGC | 未发现专用注册和成体系动作 | Dungeon/TOC 是五人冠军试炼，不能混淆 |

五人本注册了 UK/Nex/AN/AK/DTK/VH/GD/HoS/HoL/OC/UP/CoS/TOC/FoS/PoS 共 15 个入口；未见倒映大厅专用注册。入口存在不证明机制完整或当前框架支持五人编排。

## 正常规则审计的已知线索

- `Uld/UldActions.cpp`：MimironCheatAction 直接击杀地雷/炸弹机器人；VezaxCheatAction 回满法力；对应 UldTriggers.cpp 的触发器检查 BotCheatMask::raid。
- `ICC/Action/ICCActions_PP.cpp`：同类软泥多于一个时直接 Kill 多余单位；需检查当前遭遇中是否触发。
- `ICC/Action/ICCActions_LDW.cpp`：直接移除坦克 Touch of Insignificance 等光环路径。
- `RS/Action/RSActions_HAL.cpp`：燃烧到指定位置后直接移除相关光环，另有直接 AddAura 加速路径。
- 当前磁盘 playerbots.conf 的 BotCheats 为 food,taxi,raid。尚未逐 bot 核验运行时有效掩码，也未证明这些路径在 run77/78 中触发。

进入每个 boss 前沿注册→触发→动作及附加脚本核验开关与运行条件。只关闭 raid cheat 不能自动证明消除了全部辅助。源码更新后重做相关条目核验。
