# 英雄岩石大厅整本通关（本机，2026-10-07/08）

> 场景 `heroic-hos-run-h5g`（ilvl 200 档），检查点 `heroic-hos-run-from-brann-h5g`；路线 `599-halls-of-stone.route` 由 `tools/route-gen/overrides/599-halls-of-stone.{txt,skeleton}` 生成（骨架手拼：旅行节点路径 + Maiden 直线 + Brann 护送路径 280701）。playerbots `backlog/vh`（未合并），raidtest `backlog/vh`。

## 结果

整本通关 **7 次**：2339、2345、2363、2364、2365、2369、2370（2276–2750 秒）。最近两批（2360–2370，改完 Krystallus 后）11 次有效 5 次通关；进入 Tribunal 的 5 次全部打过。失败：Krystallus 偶发多人 Shatter（2360、2368）、开局走廊/大厅多拉（2361、2362、2367）、北侧 (1001,862) 掉出地图（2366）。

## 打法与修正

- **Brann 四次对话**用路线条目 `gossip`（对话不可用时在他身边等）：护送 → 开 Tribunal → 离开 → Sjonnir 门口开门。Tribunal 的波次用 `summoned repeat=1`。
- **护送前先清护送路线上的 Construct**：Brann 护送中进战斗后脱战，脚本清掉他的路点移动（`brann_bronzebeard.cpp` EnterEvadeMode），他停在原地，护送永远走不完（2331、2332）。
- **入口第一组**在门口远拉（等巡逻 Theurgist 走开），否则巡逻与两只 Construct 一起来（2336）。
- **走廊两组**（Giant 组、Warrior 组）去程就清（2344）。
- **中央大厅三组巡逻**：先 Construct/Shardling，再东走廊拉东西走的一对，再从 (1048,668) 拉南组、(1038,668) 拉北组（2330、2342、2361）。
- **Krystallus**（`HoS` 策略）：
  - 散开限定在他 35 码内、不往低处也不往高处走、主坦克不散（无界散开把人推下平台、坦克爬上岩坡掉出地图：2333、2334、2343、2350、2341）；
  - 禁用召唤帮手（火元素/镜像等会被石化并对全队 Shatter 8–25k：2347、2351、2352）。
  - 带房间隔离 `heroic-hos-krystallus-evidenced-room-h5g` 5/5（每场 1–3 死）。

## 遗留

- Tribunal 仍是装等压线点（整本里约一半能过）。
- Krystallus 偶发 2 人同时被 Shatter（2360）。
- 中央大厅北/南组偶发一起来；2361 后改为先南后北（待验证）。
