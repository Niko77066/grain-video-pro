# vendor/upstream-skills — 官方 HyperFrames skill 的溯源凭据（内容已删）

**这里只剩两份文件：本说明 + `skills-lock.json`（25 个官方包的来源与内容哈希）。**
副本本身 2026-07-28 拉取（`heygen-com/hyperframes`，CLI 口径 0.7.77）、当天挖矿完毕、当天删除。

## 为什么删

挖矿已经做完（下表），知识以本仓 compose 合同的语言重写进了 `produce/references/`，
**副本留着不再增加任何信息**——它不进 `.claude/skills/` 所以不占模型注意力，但占 7.8MB / 720 个文件的
仓库体积与 git 历史。要对照上游时按下面一条命令重新拉，比背着走划算。

## 挖矿落点（2026-07-28）

| 官方包 | 挖进哪里 | 挖了什么 |
|---|---|---|
| `motion-doctrine` | `produce/references/motion-continuity.md` §1–3、§6–7 | 矢量律、全片主方向与保留矢量、承接物、因果运动、禁 idle wobble 与五条持续运动路线、高潮前静止、时长口径 |
| `cut-the-curve` | 同上 §4–5；`hyperframes-recipes.md` F16 / F01 | 五种接缝参数表、12% 部分位移、镜像 power4、淡出提前、blur 尺度规则、Z 符号纪律、瀑布入场分档、Nudge 三段位移 |
| `seam-craft` | 同上 §9；`compose-contract.md` §4 | 白闪守卫（`#root` 不透明）、同轨重叠非法、clip 门控坑 |
| `oversized-cursor` | `hyperframes-recipes.md` F04；`motion-continuity.md` §8 | 尺寸、物理进出场律、尖端命中与按压支点、1:2 点击、click 同帧引燃、drift aside、跨镜交接 |
| `captions-overlay` | `visual-selfcheck.md` 硬查 19 | 字幕是叠加层不是保留带、按真中心排版、大字强调的稀缺性原则 |

**当时刻意没搬的**：官方 `ledger.json` + `seam-stamp.mjs` / `seam-gate.mjs` 脚本（依赖 PLV injector 布局）、
house 默认主方向 LEFT、`cqw` 单位与 `#el-<sid>` 选择器、`drop/rail/embed` 里的 embed 层（本仓无真人主体）。
逐条理由见 `motion-continuity.md` §10。

## 要对照上游时怎么拉回来

```bash
npx skills add heygen-com/hyperframes --agent claude-code --skill '*' --copy -y   # 装进 .claude/skills/
```

拉回来后用新生成的 `skills-lock.json` 与本目录这份比哈希，就知道上游哪些包变了。
**看完记得删掉或移出 `.claude/skills/`**——那 25 个包会抢 `/produce` 的路由（官方 `hyperframes` 自称
mandatory entry point），且一半命令依赖 HeyGen 凭据。它们**不在交付面**，理由见 CLAUDE.md §交付面。
