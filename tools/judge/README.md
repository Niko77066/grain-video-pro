# G2 评委 harness（去模型化 · 出题/阅卷两端）

独立评委席位。设计出处：`docs/film-ir-context-architecture.md` §2.2——评委物理隔离、只读证据包、评分必须引用镜头 ID/时间码否则判无效、只产报告不改状态。

> **2026-07-24 去模型化**：本工具**不含任何模型/网关/凭据**。评委的"眼睛"是**宿主 harness 的模型**——`judge.py` 只做确定性两端（**出题** = 组织证据 + rubric；**阅卷** = 规则派生判词 + 引用校验），中间的**打分由 agent 自己派发的隔离 subagent 完成**。这样评委随宿主换模型、不锁死某个 API，也不给外挂带 key 摩擦。

## 三件套

| 脚本 | 干什么 |
|---|---|
| `build_evidence_pack.py <project> [--golden <项目>]` | 出证据包：contact sheet（整点 + 半步错位）+ 逐镜中点帧 + Golden 并排 + L0 报告 + **成片音轨 `audio.mp3`** + 隔离 `manifest.json`（镜头事实 + 旁白分节，**零创作理由**）。ffmpeg 走 PATH（`FFMPEG`/`FFPROBE` 可覆写） |
| `judge.py <pack> --node {hero_frames\|final\|audio} --task` | **出题**：打印隔离评审任务（rubric + 证据文件绝对路径清单 + 镜头事实 + 引用纪律 + 输出 JSON schema），落 `<pack>/judge-task-<node>.md` |
| `judge.py <pack> --node ... --finalize <scores.json>` | **阅卷**：读 subagent 打分 JSON → 规则派生判词 + 引用校验（视觉）/ 字符重合率≥0.95（音频）→ `<pack>/judge-report-<node>.json` |
| `calibrate.py <scores.csv>` | 人工分 vs 评委分 Spearman 秩相关（CSV: `film,human_overall,judge_overall`） |

## 评审回路（agent 在 produce SOP 里跑）

```
build_evidence_pack.py <project>                 # 1. 出证据（含音轨、Golden 并排、镜头事实 manifest）
judge.py <pack> --node final --task              # 2. 出题（隔离任务 → stdout / judge-task-final.md）
  → agent 派发隔离 subagent：喂 [任务 + 证据文件]，subagent 看不到创作上下文，返回打分 JSON
judge.py <pack> --node final --finalize s.json   # 3. 阅卷：规则派生 verdict + 引用校验 → 报告
```

- **节点**：`hero_frames`（③b 品味门，vs Golden 下限，fail 禁铺开生产）/ `final`（⑨ 成片门，D1–D9 + 反模式）/ `audio`（音频真听：转写回验 + 混音 + BGM + 字幕校对）。
- **不含凭据**：本工具零 API key。scoring subagent 用的模型由宿主 harness 提供——**评委与导演不同模型家族**（同族自评共享盲区）由宿主在派发时保证。
- **规则派生判词**（`judge.py` `VERDICT_RULE`）：`overall<3.5 或命中任一反模式 → fail`，不信模型自报（自报存 `verdict_model` 作校准语料）。
- **引用纪律**：视觉报告 `notes` 里无镜头 ID/时间码引用的维度标 `citations_valid=false`（D9 网感可锚定标题/钩子/推荐流）——这样的报告不作数、整报重评。

> **本次已验**：`--task` 出题 + `--finalize` 阅卷冒烟通过（规则派生把模型自报 pass 改判 fail、overall 自动汇总、引用缺失正确标 invalid）。纯 stdlib，系统 python 即可跑。

## 校准协议（先校准后放权）

1. 拿**带人工分的片库**盲评：M0 校准语料 + 2026-07-20 五片对照实验（同 brief、质量分布已知、人工排序已知——天然考卷）；
2. `calibrate.py` 出 Spearman ρ 与逐片偏差；
3. **ρ ≥ 0.7 且评委无系统性放水（均分偏高 ≤ +0.3）之前，评委分只并行记录、不拿否决权**；hero-frame 门在校准期出 fail 时降级为"警示 + 记 ledger"；
4. 达标后放权：`hero_frames` fail = 禁止铺开生产；`final` fail = 禁止 delivered。放权决定由作者拍板，记入本 README。

## 纪律红线

- 评委报告里无镜头 ID/时间码引用的判断会被 `citations_valid=false` 标记——这样的报告不作数，重评；
- 评委只写报告文件；往 `ledger.gates` 登记由 EP 执行（附报告路径为证据）；
- 禁止把评委降级成纯文本评委（无图片/音轨 = 无效评审）；禁止拿创作过程解释去说服评委（隔离 manifest 本就零创作理由）。
