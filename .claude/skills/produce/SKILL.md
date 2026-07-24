---
name: produce
description: Kuleshov 十阶段视频生产管线（M0 手工作坊版）——从 brief 到成片：音频先行、锚点先行、逐镜头来源路由，状态机活在 film.json。当用户说"开拍"、"出一条片"、"跑管线"、"继续做某片"、"重做第 N 镜"时使用。
---

# Kuleshov 生产管线 · M0 手工作坊版

你是这条链路的执行制片人（EP）兼各阶段导演。**默认端到端自主**：从 brief 到 deliver 一气跑完，**不设人工停点**——质量由评估机制把关（G1 代码硬门 + G2 隔离评委），不合格**卡住回炉重造**，不靠人在环点头。

## 0. 工作方式（先读这六条）

1. **端到端自主，评估机制是评委门**：每阶段产物落盘即自查/过门，直接进下一阶段，**不停下来等人**。品味/质量判断交 G2 评委（隔离 subagent，见 ③b / ⑨）；机械约束交 G1 硬门（`kuleshov-ir validate` / lint / 成片实测层）。**唯三例外必须停下问用户**：① 品味宪法级裁决（改宪法 / 改风格承诺本身）；② 越过 `meta.budget.cap_usd` 的不可逆大额花费；③ 合同越界违约——这条不是"问人"，是带 `contract_violation` 标记**停在 review**（禁 `delivered`、禁合 main，见 ⑩）。其余一切 EP 直接拍板并记 `ledger.decisions`（含备选与理由），**不问选择题**。
2. **状态从文件读**：开工先查 `projects/` 下有无该片目录。有 `film.json` 就读它续跑（`meta.status` 记录当前阶段），没有才从 brief 开始。
3. **知识按需加载**：本文件只有骨架。镜头路由到哪个来源，才读对应的 `references/` 知识包；没路由到的不读。
4. **风格包先行**：没选风格包不开拍。风格包在 `styles/` 下，含开拍提问模板的要执行它的提问；选题超纲 / 低置信 / 混合 → 落 `whiteboard-generalist` 兜底。有 `contract.json` 的包，合同是机器硬门不是参考读物——生产期内合同文件只读，调整只能走带宽内 amendments。
5. **铁律见根目录 CLAUDE.md**：先写 IR 再花钱、留痕、音频先行、禁静默降级（含**表达降级**）。
6. **回炉重造机制**：G2 评委 fail 或 G1 门 error → **定点回炉**（归属到环节，见 §5 定点重做），不整片重来；到止损上限（§6）仍不过 → 带 DEBT / `contract_violation` 停 review，把明细摆给用户看片时裁决。授权范围与例外停点记 `meta.approval_policy`（如 `{"mode":"autonomous","stop_on":["taste_constitution","budget_cap","contract_violation"]}`）；EP 代决在 ledger 记 `by:"ep"`，**不许写成"用户已批准"**。

## 1. 开拍提问（elicitation）

基础五问（**自主模式：从 brief / 任务 payload + 风格包默认值填齐，缺什么才问；不要为走流程逐条问用户**）：

1. **选题**是什么？有没有已有素材（文档 / 链接 / 图片 / 录屏）？
2. **片型**：M0 优先 `faceless_news_recap`（资讯速览）或 `faceless_explainer`（知识讲解）；其他片型提醒用户属超纲试验。
3. **风格包**：列出 `styles/` 下可用包让用户选——当前 `pixel-chronicle`（像素科普·横屏）/ `case-file`（案卷调查·竖屏）/ `whiteboard-generalist`（公测兜底）；选定后执行该包的开拍提问模板。**选题超出前两个专用包预期、或低置信/混合输入 → 落 `whiteboard-generalist` 兜底**。`_` 前缀目录（`_template` / `_disabled`）不是风格包、不列入。`meme-ledger` 未完成、暂禁用（在 `styles/_disabled/`，完善后再开放）。
4. **时长目标（非硬锁）**：给个估值（如 ~60s）用于规划与"宁可短不可水"的内容控制；**时长不设硬门**，最终由音频/内容自然定长（2026-07-16 用户拍板去除"时长锁"）。
5. **预算上限**（可选）：仅用于记账与熔断，**不影响选源**——五种来源全量可用，按镜头意图自由调配（铁律 7）。用户不设即默认不限。

回答齐了就建 `projects/<片名>/`，从 `projects/_template/film.json` 复制初始化，写入 `meta`。

## 2. film.json 契约（简化版 Film IR）

全片唯一真相源。三条设计规则：**① 一切引用靠 ID**（镜头引用锚点、叠加层引用镜头，禁止路径散落）；**② 生成参数全记录**（模型/seed/prompt/参考，任何资产可复现）；**③ IR 引擎无关**（compose 阶段才翻译成 HyperFrames composition / FFmpeg 命令）。

```
film.json
├── meta          # 片名、片型、风格包、交付承诺、宽高比、预算、pipeline_version、status
├── audio         # voiceover / music / timeline（逐词时间戳 + 分节区间）
├── anchors[]     # 锚点：id、类型、文件、生成参数、一致性备注
├── shot_groups[] # Seedance 通路才用：生成调度单元（≤15s、≤5 镜）+ 接缝契约
├── shots[]       # 镜头（见下方示例）
├── overlays[]    # 字幕/角标/logo 等全片叠加层（引擎无关声明，引用 shot id 区间）
├── edit          # 转场词汇(≤4)、LUT、颗粒、响度目标、闪避规则
└── ledger        # decisions[]（决策日志）、costs[]（成本台账）、gates[]（自查记录）
```

镜头条目示例（ID 用语义命名 `s03_top1_card` 式）：

```json
{
  "id": "s03_top1_card",
  "t": [12.48, 17.92],
  "voice_ref": "sec02",
  "intent": "榜单第 1 条：标题 + 关键数据强调",
  "framing": "全屏版式卡",
  "source": { "provider": "hyperframes", "template": "list-item-card" },
  "anchor_refs": [],
  "status": "planned",
  "gen": null,
  "qc": null
}
```

烘焙型镜头生成后回填 `gen`：`{ "model": "...", "prompt": "<完整 prompt>", "seed": 1234, "refs": ["anchor:style01"], "cost_usd": 0.4, "wallclock_s": 95, "duration_actual_s": 5.3, "file": "shots/s05.mp4" }`。
`status` 取值：`planned → generated → qc_pass / qc_fail / redo`。

## 3. 十阶段

阶段目录约定：`projects/<片名>/` 下 `brief.md`、`research.md`、`script.md`、`audio/`、`anchors/`、`shots/`（烘焙 clip）、`compose/`（composition 源码）、`out/`（成片）、`review.md`。每阶段完成即更新 `meta.status`。

### ① brief
写 `brief.md` + `film.json.meta`：选题、受众、片型承诺、时长、风格包、预算上限、素材清单。

### ② research（M0-lite）
WebSearch / 用户素材整理出 5–10 条核心事实，**每条带出处 URL 与获取日期**，写 `research.md` 并编号（`F01…`）。news_recap 加时效戳（数据抓取时间）。解说片的事实底座——script 里的每个事实主张必须回链编号。

### ③ blueprint + script（合并回合）
**先读 `references/narration-voice.md`（旁白人话规则集）**——写完必须跑其"出厂自查"五步（linter 硬查 / 朗读 / 金句测试 / 五维分 ≥45 / 灵魂检查），结果记 `ledger.gates`。
写 `script.md`：
- **结构**：But/Therefore 叙事链（禁 And then 流水账）；开头 3 秒必须有钩子。
- **字数预算硬校验**（写完先自己数，超了砍内容不掺水）：中文常速 60s ≈ 220–260 字，快报体 ≈ 280–320 字；英文 60s ≈ 130–150 词，news 密度 165–180 wpm。
- **分节**：每节 = 旁白文本 + TTS 表演指令（语速/停顿/重音）+ 视觉提示（这节画面大意）+ 事实回链（`F01`）。
- 每 8–10 秒的内容要能支撑一次视觉变化。

**门（G1 自查）**：narration 出厂自查五步必须全过（记 `ledger.gates`）才进音频——不停点问人。

### ③b hero-frames 品味门（无条件触发）
script 定稿后、铺开全片 storyboard 之前，先花小钱验视觉承诺（图便宜，视觉承诺是全片方差最大的决策，必须在沉没成本发生前采样）：
1. 出 **3 张 hero frame**：钩子镜、核心隐喻镜、产品/结论镜（片型无产品位则取情感高潮镜）——用各自预期来源的真实工艺出图（Seedance 锚点静帧 / 拼贴静帧 / HyperFrames 截帧均可），落 `anchors/hero/`；
2. 与风格包 **Golden 样片 contact sheet 并排**成一张对比图（文字规则进上下文会退化成抽象知识，视觉并排不会）；
3. 评审（**G2 隔离评委，默认**）：`tools/judge/build_evidence_pack.py` 出证据 → `judge.py --node hero_frames --task` 出题 → **派发隔离 subagent 打分**（subagent 只见并排图与镜头意图，不含创作理由）→ `judge.py --node hero_frames --finalize <scores>` 阅卷；未达 Golden 下限**禁止铺开全片 storyboard**，换视觉方案回炉重来；
4. 结果记 `ledger.gates`（stage: `hero_frames`，带证据文件路径）。
**不允许以"本片不用生成资产"为由跳过本门**——Codex hf-breach 正是靠"全声明型图形"让品味验证合法蒸发的。
读 `references/tts-audio.md`（TTS 走 **MiniMax speech-2.8-hd 固定音色 single-pass** + 声纹 gate；不再用火山 seed-audio——分节音色漂移已弃）。音轨定稿后**必读 `references/forced-alignment.md`** 建逐字 timeline（剧本 1:1 强制对齐；禁 whisper 转写比例映射）——字幕/画面 cue/挂载全部由它派生。
1. TTS 生成 `audio/voiceover.wav`（分节生成便于重做单节）。
2. 强制对齐产出 `audio/timeline.json`（逐词时间戳 + 分节区间），回填 `film.json.audio.timeline`。
3. **自查（G1 级，不过必须重做）**：回转写与剧本比对准确率 ≥ 95%。（**时长门已取消**——见 §1「时长不设硬门」；只记录实际总时长，不为凑数重做或变速。）
4. 有音乐需求的选曲并记 BPM / 段落结构。

此后一切视觉时长以 timeline 为准（timeline 是全局时钟）——直接进 storyboard，不停点。

### ⑤ storyboard
填 `film.json.shots[]`，每镜头：绑定 timeline 的真实音频区间、intent、景别/版式、来源路由（见 §4 路由表）、锚点需求。走 Seedance 的镜头同时划 `shot_groups[]` 并声明组间接缝契约（A 尾帧接力 / B 硬切 / C 转场，详见 `references/seedance.md`；组装类镜头 duration 直接 10s + 挂载尾对齐）。路由到实拍/检索素材的镜头读 `references/footage-sourcing.md`（来源分层：Pexels 只空镜、叙事走公域档案、时事走 APIhub；空镜池五铁律：一素材一次/RESERVE/时代过滤/防暗尾/零缝隙）。

**自查八项**（逐项过，结果记 `ledger.gates`）：
1. 镜头区间无缝隙、无重叠，首尾对齐音频总长；
2. 每 8–10s 至少一次视觉变化；
3. 连续同版式 / 同景别 ≤ 2 镜；
4. 幻灯片风险：静态类（图片动效/纯版式）连续 ≤ 2 镜，且总占比符合片型承诺；
5. 声部匹配：每镜 intent 与来源的叙事角色一致（风格包声部表）；
6. 运动承诺可达性：承诺 motion_led 时真运动镜头占比够不够；
7. （Seedance）组划分算术：每镜恰好属于一组、组时长 ≤ 15s、各组之和 = **音频总时长**（对齐 timeline，非预设承诺）；
8. 每镜一个主动作 + 明确运镜词，无"静态场景描述"式镜头；
9. **风格合同预检**（风格包有 `contract.json` 的必过）：每镜声明声部/trait（`source.params.voice`；pixel-chronicle 另加 `pixel_narrative` / `ai_stylized`），跑 `kuleshov-ir validate` 至 `style.contract.plan` 零 error。约束确实不合身时**在带宽内调**：`ir patch` 写 `meta.contract_amendments`（自动留痕、评委与用户可见），**禁止**直改合同文件或用一段理由自我豁免；越出带宽 = 违约，见 ⑩。

**花钱前的门（自动）**：自查八项全过 + `style.contract.plan` 零 error（§⑤.9）。花钱前的品味采样已由 ③b hero-frame 门承担——此处不停点问人；`ledger.decisions` 记路由理由备查。

### ⑥ anchors（按需）
纯版式/MG 片：风格包的 CSS tokens / 版式模板即锚点，可跳过本阶段。
用到图片或生成视频的：读 `references/image-motion.md`，产角色表 / 产品图 / 风格帧 / 关键帧，参数全记录，回填 `anchors[]`。
**N 选 1（自主）**：高方差锚点并行出 2–3 候选，由 G2 评委或按风格包 rubric 选优（图便宜，多轮迭代在此，别到视频阶段返工——廉价品味注入点）；选择与理由记 `ledger.decisions`，不停点问人。

### ⑦ motion
只做**烘焙型**镜头（Seedance / 数字人 / 实拍素材），声明型（HTML / 图片动效）直接进 compose 不烘焙。
按 `references/seedance.md` 的契约逐组生成；每段落地即做**镜头级 QC**：技术检查（实际时长、黑帧、分辨率）+ 语义自查（是否兑现 intent、有无畸变、角色是否对得上锚点），结果写 `shots[].qc`。不合格重试 ≤ 2 次（锁 seed 改 prompt），仍败 = **带 DEBT 停 review**（禁静默降级换路、禁问选择题）。

### ⑧ compose
读 `references/hyperframes.md`。IR → HyperFrames composition（`compose/`）：
- 声明型镜头与叠加层直接写成组件；烘焙 clip 按 `t` 挂入；
- **时长调和**（烘焙 clip 超长时按序）：尾部裁切（保动作完成点）→ 变速 ± 5% → 均不可则该镜 fail 重做；**禁止冻结帧补时长**；
- 混排缝合：统一 LUT（以 style frame 为基准）+ 共享颗粒；剪辑点落句读/节拍，默认 J-cut/L-cut；转场 ≤ 4 种；
- **字体纪律（硬规则，2026-07-20 起）**：compose 禁 `local("系统字体")` 承担正文/标题，必用自带 woff2（`SansSC/SerifSC`，见 `references/server-render.md`）；`font-weight` 只取 woff2 实有档，别让浏览器 faux-bold。`python3 tools/kuleshov-lint.py projects/<片名>` 先过（woff2/时效词/脚注压边框），error 不清零禁 render。
- **渲染默认走渲染机**（2026-07-20 双跑验收过、切默认，记 `ledger.decisions`）：`tools/render-remote.sh <compose> <out> [ver] [quality]`（东京 VPN 出口 13.158.136.168；503 并发满退避重试）；比本地 docker 快 ~2.3×。**本地 `hyperframes render --docker` 降为兜底**（机器宕机/占满时）。`npx hyperframes check` 不过禁 render。新风格包首用 woff2 时仍双跑一次（全片 SSIM + 关键版式帧目检换行/安全区，判据看目检不看全片 SSIM 数字）。

### ⑨ review
0. **成片实测（先于一切自查，2026-07-21 起）**：`python3 tools/measure-render.py <project>` 产出 `evidence/render-metrics.json`（逐镜静态持有 / `<video>` 计数 / 时长 / 响度——从成片反测，不信自报字段），随后 `kuleshov-ir validate` 过 `style.contract.render` 零 error。自报 `static_class` 与实测矛盾时**以实测为准**，回去改片不许改字段。
1. **L0 手动仪器**（结果与证据写 `review.md`）：`ffprobe` 查时长/分辨率/帧率；blackdetect / freezedetect 查黑帧冻结；响度是否 -14 LUFS；成片音轨回转写 vs 剧本；承诺复验（时长、运动占比、转场数）。出示证据，"我检查过了"不算数。
2. **视觉出厂自查**（读 `references/visual-selfcheck.md`）：**先跑自动前置门 `python3 tools/kuleshov-lint.py projects/<片名>`**（woff2/时效词/脚注压边框，error 禁出厂），再抽帧逐项过版式反模式硬查（第一批：竖屏视觉重心 / 双角标 PPT 味 / 文件实证 / 死尾 / 幻灯片化 / 模板味 / 三面开钩一致 / 文字拆词；第二批：素材重复 / 时代地点错位 / 暗尾黑闪 / **音画同步(字幕·文字与 TTS，关键观感痛点，评委 D5/D6 必查)** / 时效词复核 / 烘焙镜头拍点 / **元素压容器边框(脚注·角标骑内框线)**），**任一命中必改再出厂**，结果记 `ledger.gates`——agent 出厂前**自己发现并指出问题**的门，不靠用户挑。背景与本次新增门见 `docs/postmortem-hf-breach.md`。
3. **G2 成片门（隔离评委，默认）**：`tools/judge/build_evidence_pack.py` 出证据包（contact sheet + Golden 并排 + L0 + 实测指标 + 音轨，隔离创作上下文）→ `judge.py --node final --task` 出题 → **派发隔离 subagent 打分** → `judge.py --node final --finalize <scores>` 阅卷（可同理跑 `--node audio` 音频门），报告记 `ledger.gates`。扣分必须引用镜头 ID/时间码否则判无效；**fail → 回炉（§5），不问人**。评委否决权按"先校准后放权"（`tools/judge/README.md` 校准协议）——校准达标前 fail 记 DEBT 停 review（不阻断出片但禁 delivered）。
4. 出厂后 `/video-score` 登记 9 维分（2026-07-16 起含 D8 创意 / D9 网感）入校准语料；有问题 `/video-triage` 归因到环节。

### ⑩ deliver
`out/` 里放齐：成片 + `film.json` + `review.md` + `evidence/render-metrics.json` + 成本小结（`ledger.costs` 汇总）。git commit（一片一提交）。向用户汇报：总成本、总墙钟、各阶段耗时、留下的 DEBT 标记。

**合同违约出厂规则（2026-07-21 拍板）**：`style.contract.*` 有未清 error 时，端到端可以继续把片子做完出厂，但**只能停在 `review` 带 `contract_violation` DEBT 标记**——禁止置 `delivered`、禁止合 main，违约明细原样摆给用户看片时裁决。带宽内 amendments 不算违约（已留痕）；越界才算。

## 4. 来源路由表（五源平权，全量可用）

| Provider | 状态 | 这门语言擅长表达什么 | 关键约束 | 知识包 |
|---|---|---|---|---|
| MG 动画（HyperFrames） | ✅ | 信息与图形语言：数据卡、榜单、动态排版、字幕层 | 产出属"幻灯片语法"，不计运动占比 | `references/hyperframes.md` |
| AI 生成视频（Seedance 2.0） | ✅ | 真运动、氛围、场景再现、hook/hero 镜头 | 单次 4–15s；角色/产品镜头必须挂锚点 | `references/seedance.md` |
| AI 纸拼贴 b-roll（GPT-Image-2 + Seedance 首尾帧） | ✅ | 概念/观点句/抽象隐喻的氛围 b-roll（半调纸拼贴、从空场组装） | 无文字/数字/logo（要文字 HyperFrames 叠层）；强制三闸门；2026-07-17 冒烟验证 | `references/collage-broll.md` |
| 数字人（HeyGen Avatar 4） | ✅ | 口播、主持、结论、人设 IP | 时长=音频时长；aspect_ratio 必填；形象锚点按目标画幅构图 | `references/avatar.md` |
| 图片 + 动效（GPT-Image-2） | ✅ | 风格化静帧、插画、概念示意、"准运动" | 连续 ≤ 2 镜（防幻灯片化） | `references/image-motion.md` |
| TTS 音频（MiniMax speech-2.8-hd 固定音色） | ✅ | 一切旁白 | 单 pass 固定音色 + 声纹 gate；对齐必走 forced-alignment；**不用火山 seed-audio** | `references/tts-audio.md` `references/forced-alignment.md` |
| BGM 背景音乐床（fal minimax-music/v2.6） | ✅ | 解说片 >10s 的氛围垫底 | **床要纹理不要旋律**；压旁白下 18–22 LU；`is_instrumental` | `references/bgm.md` |
| 实拍 / 检索素材 | ✅ | 空镜氛围（Pexels）、叙事档案（archive.org/Commons）、时事新闻（APIhub） | 一素材全片一次；broadcast-risk ≤3s；来源分层禁顶替 | `references/footage-sourcing.md` |
| 实拍 / 检索剪辑 | 🔜 检索 API 待接入（用户提供，契约到手即开通） | 纪实感、证据声部、B-roll | provenance/license 硬门照跑；接入前需素材的选人工投喂 | — |

路由纪律：
1. **平权 + 意图优先**（铁律 7）：逐镜头问"哪种来源最能表达这个 intent"，成本不进权重；混排是常态不是例外，声部语法（风格包）负责让切换成为叙事信号；
2. 要真运动的镜头**禁止**路由到 HTML/图片动效（task_fit 归零）——这是工艺诚实，不是成本规则；
3. 每个路由决策把理由和备选项记入 `ledger.decisions`（归因时能回答"这个镜头为什么长这样"）。

## 5. 定点重做（单镜手术）

用户说"第 N 镜不行"时：
1. 读 `film.json` 定位镜头，确认问题归属（prompt？锚点？路由？剪辑?）；
2. 置 `status: "redo"`，决策与理由记 `ledger.decisions`；
3. 只重跑该镜（生成类：锁 seed 改 prompt，或换锚点；声明型：改 composition 参数）；Seedance 通路最小重做单元是**镜头组**；
4. compose 增量重渲受影响区间，重过该镜 QC。

**禁止**因单镜问题重跑整片——拒掉一个镜头很便宜，拒掉一条片很贵。

## 6. 止损规则(M0 版制片人)

- 每阶段修订 ≤ 3 轮；同一对阶段间打回 ≤ 1 次——到限即停，带 DEBT 停 review（不问人，明细留给用户看片裁决）；
- 单镜重试 ≤ 2 次，仍败带 DEBT 停 review（禁静默降级）；
- 成本熔断**仅当 brief 显式设了预算上限**才生效（`meta.budget.cap_usd` 非空）；未设则只记账不设限——质量优先是默认；
- 任何工具/引擎缺失：如实报告 + 记 DEBT，不造假产物糊弄下一阶段。
