# G2 评委 harness（去模型化 · 出题/阅卷两端）

独立评委席位。设计出处：`docs/film-ir-context-architecture.md` §2.2——评委物理隔离、只读证据包、评分必须引用镜头 ID/时间码否则判无效、只产报告不改状态。

> **2026-07-24 去模型化**：本工具**不含任何模型/网关/凭据**。评委的"眼睛"是**宿主 harness 的模型**——`judge.py` 只做确定性两端（**出题** = 组织证据 + rubric；**阅卷** = 规则派生判词 + 引用校验），中间的**打分由 agent 自己派发的隔离 subagent 完成**。这样评委随宿主换模型、不锁死某个 API，也不给外挂带 key 摩擦。

## 三件套

| 脚本 | 干什么 |
|---|---|
| `build_evidence_pack.py <project> [--golden <项目>]` | 出证据包：contact sheet（整点 + 半步错位）+ 逐镜中点帧 + Golden 并排 + L0 报告 + **成片音轨 `audio.mp3`** + 隔离 `manifest.json`（镜头事实 + 旁白分节，**零创作理由**）。ffmpeg 走 PATH（`FFMPEG`/`FFPROBE` 可覆写） |
| `judge.py <pack> --node {hero_frames\|final\|audio} [--mode solo] --task` | **出题**：打印隔离评审任务（rubric + 证据文件绝对路径清单 + 镜头事实 + 引用纪律 + 输出 JSON schema），落 `<pack>/judge-task-<node>.md` |
| `judge.py <packA> --node ... --mode paired --vs <packB> --task` | **配对出题**：两臂盲化成 甲/乙 + 中立目录 + 强制选择 schema，落 `judge-task-<node>-paired.md` 与 `judge-armmap-<node>.json` |
| `judge.py <pack> --node ... [--mode ...] --finalize <scores.json>` | **阅卷**：读 subagent 打分 JSON → 规则派生判词 + 引用校验（视觉）/ 字符重合率≥0.95（音频）→ `<pack>/judge-report-<node>[-paired].json` |
| `judge.py <packA> --node ... --merge <配对报告> <单臂A> <单臂B>` | **两路合并**：方向 + 强度互证 → `judge-merge-<node>.json`（`decisive` / `weak` / `tie` / `inconclusive`） |
| `calibrate.py <scores.csv>` | 人工分 vs 评委分 Spearman 秩相关（CSV: `film,human_overall,judge_overall`） |

## 评审回路（agent 在 produce SOP 里跑）

```
build_evidence_pack.py <project>                 # 1. 出证据（含音轨、Golden 并排、镜头事实 manifest）
judge.py <pack> --node final --task              # 2. 出题（隔离任务 → stdout / judge-task-final.md）
  → agent 派发隔离 subagent：喂 [任务 + 证据文件]，subagent 看不到创作上下文，返回打分 JSON
judge.py <pack> --node final --finalize s.json   # 3. 阅卷：规则派生 verdict + 引用校验 → 报告
```

- **节点**：`hero_frames`（③b 品味门，vs Golden 下限，fail 禁铺开生产）/ `final`（⑨ 成片门，D1–D9 + 反模式）/ `audio`（音频真听：转写回验 + 混音 + BGM + 字幕校对）。
- **模式**：`--mode solo`（缺省）/ `--mode paired`——见下节，**先定问题类型再定模式**，不许随手选。
- **不含凭据**：本工具零 API key。scoring subagent 用的模型由宿主 harness 提供——**评委与导演不同模型家族**（同族自评共享盲区）由宿主在派发时保证。
- **规则派生判词**（`judge.py` `VERDICT_RULE`）：`overall<3.5 或命中任一反模式 或任一 hero frame 未过 → fail`，不信模型自报（自报存 `verdict_model` 作校准语料）。
- **引用纪律**：视觉报告 `notes` 里无镜头 ID/时间码引用的维度标 `citations_valid=false`（D9 网感可锚定标题/钩子/推荐流）——这样的报告不作数、整报重评。

> **本次已验**：`--task` 出题 + `--finalize` 阅卷冒烟通过（规则派生把模型自报 pass 改判 fail、overall 自动汇总、引用缺失正确标 invalid）。纯 stdlib，系统 python 即可跑。
> **2026-07-27 已验**：配对盲化（哈希把后给的包排成甲臂）、四条模式护栏、`--merge` 四种判定，以及用实测数据回放选题 1/2 → `inconclusive` / `weak`。

## 评审模式协议（2026-07-27 定，`--mode`）

### 为什么必须定死

2026-07-27 的 A/C 风格包形态对照实验：**同一批 hero frame、同一批六位隔离评委**，配对与单臂给出相反胜负。

| | 配对路 | 单臂路 | 配对减单臂 |
|---|---|---|---|
| 选题 1 | A 15 : C 34（C 大胜） | A 23 : C 21（A 微胜） | A −8 / C +13 |
| 选题 2 | A 28 : C 32 | A 28 : C 29 | A 0 / C +3 |

- **对照会污染绝对分**：选题 1 的 C 臂对上一个明显更差的对手，四个维度各涨 3–4 分——涨的不是作品，是对手垫的。
- **污染强度本身不稳**：选题 2 的配对评委几乎没拉开（A-T2 四维一分不差）。所以"两边都用同一种模式"抵消不掉这个偏差，只能按问题类型分流，并在两路分歧时判不稳。

结论：**模式由问题类型决定，不由手边方便决定**。`judge.py` 现在在 CLI 层拦截混用（`--vs` 只在 `--mode paired` 下合法；`--mode paired` 必须给 `--vs`；`audio` 门拒绝配对）。

### 三条规则

**1. 绝对判断走单臂（`--mode solo`，缺省）**

"够不够出厂""过不过 Golden 下限""这一版能不能铺开生产"——三个既有门（`hero_frames` / `final` / `audio`）**全部**是绝对判断，所以 solo 是缺省。

- 证据里**不得出现竞争对手**。出题时会加一段单臂纪律：面前只有一件作品，禁止与未列在证据清单中的作品比较，禁止用"比一般的强/弱"代替对下限的判断。
- **Golden 是标尺，不是对手**：它是跨会话固定、水平已知的基准，作用是给下限定位，不参与"谁更好"。出题里现在显式写成「固定标尺，不是对手」。
- 只有 solo 报告产出 `verdict: pass|fail`。

**2. 相对判断走配对（`--mode paired --vs <另一个 pack>`）**

"新版比旧版好没好""A/B/C 哪个方案更好"——跨会话的绝对分不可比（不同批次、不同评委、不同锚点漂移），所以相对结论只认同席配对。

- **两臂盲化**：`_arm_order()` 用两个 pack 绝对路径的 SHA-256 决定谁是 甲 谁是 乙——确定性可复跑，且与"新/旧""A/C"的调用顺序脱钩。证据文件复制进 `<packA>/judge-paired-<node>/{arm_a,arm_b}/`，路径里不再出现项目名（文件名保留镜头 ID，引用纪律需要）。
- **对照表 `judge-armmap-<node>.json` 不得交给评委**。派发 subagent 时只交任务里逐条列出的文件路径，**不要把 pack 目录整体挂给它**。揭盲在阅卷时由 `judge.py` 做。
- **配对不产出 pass/fail**：报告的 `verdict` 恒为 `null`，另有 `absolute_verdict` 写明理由。要判出厂另跑 solo。
- 胜负由规则派生（`|Δoverall| < 0.3 → tie`，否则 overall 高者胜），模型的强制选择只存 `winner_model` 作校准语料——与 `verdict_model` 同源思路。
- 维度：`final` 用 D1–D9，`hero_frames` 用 H1–H4（风格贴合 / 版式克制 / 质感缝合 / Golden 下限把握）。**hero solo 也改成同一套 H1–H4 打分**，否则两路没有可合并的公共标尺。

**3. 两路都跑时的合并规则（`--merge`）**

尺度统一到 `overall`（1–5 分制，各维均值）。`Δ = overall(arm_b) − overall(arm_a)`，两路同向记法。

| 判定 | 条件 | 可否声称胜负 | 棘轮动作 |
|---|---|---|---|
| `inconclusive` | 两路**原始朝向相反**，且至少一路 \|Δ\| ≥ 0.3 | ❌ 记"无定论" | revert |
| `tie` | 两路 \|Δ\| 都 < 0.3 | ❌ 判平 | revert |
| `weak` | 同向但只有一路拉开；或同向但 \|Δ配对 − Δ单臂\| ≥ 0.5 | ❌ 只能写"倾向 X" | revert |
| `decisive` | 两路同向、都 ≥ 0.3、对照效应 < 0.5 | ✅ | keep |
| `invalid` | 任一报告 `citations_valid=false` | ❌ 整报重评 | — |

- **翻转优先于强弱**：选题 1 正是配对 Δ 大、单臂 Δ 小却反向；先判翻转才不会被"配对那路更显著"带走。
- `conservative_margin` 取两路 \|Δ\| 的**较小值**——报告胜幅时用保守的一路，不用好看的一路。
- `claim_allowed` 只在 `decisive` 为 true；`ratchet_action` 除 `decisive` 外一律 `revert`（「没证明更好」≠「更好」，对齐 `styles/_iteration.md` 规则 6）。
- 阈值来源：0.3 ≈ 1–5 分制上小于一个 0.5 步进的可辨差；0.5 ≈ 每维半档的对照漂移。两者都写在报告的 `thresholds` 里，改动要连同校准语料一起复核。
- **两份 solo 分不构成相对结论**：跨会话直接比 overall 是本节明令禁止的用法；`--merge` 因此强制要求一份配对报告。

### 回放校验

用上表的实测数据回放（原始四维 0–10 分制按 `x/10*4+1` 归一到 1–5）：选题 1 → `inconclusive`（配对 Δ=−1.9 / 单臂 Δ=+0.2，对照效应 2.1）；选题 2 → `weak`（配对 Δ=−0.4 / 单臂 Δ=−0.1，倾向 C 但不得声称胜负）。与作者对这两轮的读法一致。

### 下游接线

- `styles/_iteration.md` 的 keep/revert 棘轮：改动后必须跑 **paired（新 vs 旧）+ 两条 solo**，按 `ratchet_action` 落 keep/revert；只有 `decisive` 才 keep。
- 风格包准入考片制（3–5 条样片盲评赢基线）：**赢基线 = 相对判断 → 配对**；同时每条样片仍要单臂过出厂下限。两者分别记录，不得互相顶替。

## 校准协议（先校准后放权）

1. 拿**带人工分的片库**盲评：M0 校准语料 + 2026-07-20 五片对照实验（同 brief、质量分布已知、人工排序已知——天然考卷）；
2. `calibrate.py` 出 Spearman ρ 与逐片偏差；
3. **ρ ≥ 0.7 且评委无系统性放水（均分偏高 ≤ +0.3）之前，评委分只并行记录、不拿否决权**；hero-frame 门在校准期出 fail 时降级为"警示 + 记 ledger"；
4. 达标后放权：`hero_frames` fail = 禁止铺开生产；`final` fail = 禁止 delivered。放权决定由作者拍板，记入本 README。

## 纪律红线

- 评委报告里无镜头 ID/时间码引用的判断会被 `citations_valid=false` 标记——这样的报告不作数，重评；
- 评委只写报告文件；往 `ledger.gates` 登记由 EP 执行（附报告路径为证据）；
- 禁止把评委降级成纯文本评委（无图片/音轨 = 无效评审）；禁止拿创作过程解释去说服评委（隔离 manifest 本就零创作理由）；
- **禁止拿配对分当出厂判词**，也**禁止拿两份跨会话 solo 分当胜负结论**——这是 2026-07-27 实验直接买来的教训，两种误用都会得到反向答案；
- **禁止把 `judge-armmap-*.json` 或 pack 目录整体交给评委 subagent**：配对的盲化只靠"评委不知道谁是谁"成立；
- 合并结论不是 `decisive` 时，**汇报里不得出现"X 比 Y 好"**——写"无定论"或"倾向 X（未达声称门槛）"。
