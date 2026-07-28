# Kuleshov → grain 交付施工稿（Grain 原生 Video step-skill）

> 状态：**施工中**（2026-07-24 起草；2026-07-28 按用户拍板更新：① 保留面 / 接缝面定稿，见 §0.5，表述冲突时以该节为准；② 字幕口径反转——发布件 VTT 走 grain `renderScriptCaptions` 同源链路，自产 VTT 降为仓内独立跑与本地 QA，见 §5/§7；③ 术语对齐 CLAUDE.md——交付形态统一叫 **Grain 原生 Video step-skill**，不再称「外挂」「M0 手工作坊」；带日期的历史决策记录保留原文）。
> 依据：本仓现状评估 + `~/KuleshovAgent` 效果资产测绘 + `~/deeplang/grain` 消费方契约逆向 + 渲染器同源核实（四轮调查，证据均引到具体文件）。
> 决策前提（用户 2026-07-24 拍板）：不再自造 agent 链路；把本仓打磨成 **harness 无关的能力包（外挂）** 交付给团队 harness（线上自研 + 测试环境 Codex 做 runtime，消费方 = `/Users/admin/deeplang/grain`）；**molly 作底 + 从 KuleshovAgent 搬效果**；范围 **A+B 一次到位**。

---

## 0. 结论摘要（TL;DR）

- **交付的最终形态不是"一个可移植仓库 + README"，而是 grain 里的一个 In-house Video「生产方法」step-skill**：`producing-kuleshov-video/`（`SKILL.md` 编号 10 阶段 prose + `scripts/` 放 `kuleshov-ir`/produce 纯变换 CLI + `references/`），在 Video carrier 路由表加一行。驱动它的是 grain 的**单 agent tool-loop**（lite 链路），不是我们的 EP loop——这印证了"编排层丢给 harness"。
- **渲染证明卡点已消解。** 我们线上服务器渲染器 = grain 渲染核包了层 HTTP；把最终 compose 走 grain 的 `runVideoRevisionCycle` 拿 `publishProofSealed` 不需要 grain 改任何渲染代码，只是从"HTTP 壳"换到"工具/队列壳"，同引擎同产物。
- **绝大多数花钱动作 grain 已有对应原生工具**（出图/Seedance 视频/数字人/音乐/长音 TTS/Pexels/下载/渲染都 EXISTS），真正的缺口只有 4 处（字幕 CTC 对齐、archive.org 公域素材、youtube 搜索、Volc 短音），每处有明确处置。
- **重塑工作几乎全在我们这侧**，有现成模板可抄（`compiling-podcast-episode` 的纯变换 Python、`producing-hyperframes-video` 的 pipeline-as-one-skill）。~~需要 grain 团队点头的只剩"字幕 CTC 原生工具要不要加"~~ ~~（2026-07-28 已谈定：字幕默认走我们自产的 VTT，此项作废）~~ **（2026-07-28 随保留面/接缝面拍板再反转：发布件字幕统一走 grain `renderScriptCaptions` 同源链路，缺口 1 恢复为质量风险项，见 §5/§7）**——需要 grain 点头的都是**加法**，不是"改它的门"。
- 采用 **A1（first-party In-house skill，走 grain PR）**：因为要在 Video 路由表加行、要补原生工具、要 same-source 字幕——A2（用户 skill）做不到这些。

---

## 0.5 保留面与接缝面（2026-07-28 用户拍板，总纲）

这是整份施工稿的裁决基准：下面每一条都能在 §4 重塑映射、§5 封印配方、§6 清单里找到落点；本节与正文其余部分表述冲突时，**以本节为准**。

### 保留 Kuleshov 的部分（知识、契约与确定性工具，随 step-skill 打包）

| 保留什么 | 仓内资产落点 |
|---|---|
| 十阶段制片法：audio-first、hero-frame 先验品味门、逐镜头最小返工与止损规则 | `.claude/skills/produce/SKILL.md` + `references/`（打包前按 CLAUDE.md「知识写法纪律」拆掉引擎 API 混写） |
| Film IR / `film.json` 状态机，以及 patch / validate / execute / migrate / new 等确定性脚本 | `film-ir/`（`kuleshov-ir` CLI：纯变换、stdout JSON + 退出码，天然满足 §2.4 的 CLI 契约） |
| 风格路由、风格合同、能力卡、Golden 登记册与样片标尺 | `styles/`（`routing.md` / `routing-vocab.json` / `routing-cases.json` / 各包 `capability.json` + `contract.json` / `golden-set.json`）+ `tools/route-style.py` |
| G1 机器硬门：结构、算术、风格合同、kuleshov-lint、成片反测 | `kuleshov-ir validate` + `tools/kuleshov-lint.py`（①–⑦）+ `tools/measure-render.py` + 各风格包 render contract |
| G2 隔离评审：出题、证据包、阅卷、引用校验与判词规则 | `tools/judge/` 的确定性部分整体保留（「眼睛」换 grain，见下表） |
| 「五源平权、按镜头意图选素材」的导演逻辑 | produce 阶段⑤来源路由 + `broll-studio` 八套材质语言的镜头级选型（`tools/broll-profile.py route` / `lint`） |

### 改成 Grain 平台接缝的部分（能力、凭据与发布，宿主拥有）

| Kuleshov 原状 | 接缝后 |
|---|---|
| 直连 provider / `.env` 的生成调用（`tools/gpt-image.py`、`tools/seedance.py`、TTS / BGM / 素材检索、`render-remote.sh`） | 全部换成 grain 原生工具：图片 `generateImage`、视频 `generateImageToVideo`、数字人 `generateTalkingHead`、TTS `synthesizeSpeech`、音乐 `generateMusic`、转写 `transcribeAudio`、素材检索 `searchPexels*` / `searchPixabay*` / `downloadVideoClip`；凭据、成本记账与异步任务由平台管（脚本内 `grain call`，长任务 `invoke_ext_async` → `await_ext_async`） |
| G2 的「眼睛」= Kimi 网关看图看片 | 眼睛换 grain `describeImage` / `describeVideo`，音频核验用 `transcribeAudio`；Kuleshov 的 judge 仍负责**确定性阅卷**（出题、证据包、引用校验、规则派生判词——不信模型自报） |
| HyperFrames composition 本地渲染 / HTTP 壳自渲 | composition 的**设计纪律**（compose 合同、woff2 就地子集化、组件底板禁令、禁烧字幕）仍来自 Kuleshov skill；真正的校验、抽帧、渲染与**封印**都在 grain 渲染机完成（`runVideoRevisionCycle` → `publishProofSealed`，§3/§5） |
| 字幕自产 VTT（`tools/make-vtt.py`）+ 自行交付 | 字幕与发布走 grain：`film.json` → storyboard 投影 → `renderScriptCaptions` 产 same-source VTT → `publishNewDropContent` 发布；**发布门只认 grain 生成的同源字幕和封印证明**。`make-vtt.py` 降级保留两个角色：仓内独立管线的交付件、对 grain 字幕的本地 QA 对照（CLAUDE.md Invariant #13 需加适用范围注） |
| EP 主循环 / subagent 调度 / hook 布线 / CI runner | 调度、Codex harness、工具权限、终态回执与频道运行恢复**全部属于 grain**（即原清单 C：不做，只以接口文档留痕） |

---

## 1. 背景与决策

三棵树：
| 树 | 是什么 | 角色 |
|---|---|---|
| `~/deeplang/grain-video-pro` | GitHub `Niko77066/grain-video-pro`（原 `~/kuleshov` + `molly` worktree，仓已改名迁移），制作内核 Kuleshov 所在仓 | **step-skill 交付面的来源仓** |
| `~/KuleshovAgent` | GitHub `Niko77066/KuleshovAgent`，62 commits 的完整 agent 系统 | **效果设计来源；agent 编排层丢弃** |
| `~/deeplang/grain` | 团队自研 harness（TS/Bun turbo monorepo） | **step-skill 的消费方** |

这次转向与自家蓝图（v3.4 §02/§10「编排层越薄红利越大、护城河在知识+治理」）自洽：把本该薄的 L1 编排层让给 grain，把厚重的 L2 知识 / L3 契约 / L4 工具收进 step-skill 交付面。

---

## 2. 交付形态：grain 契约钉死的硬目标

以下是 grain 逼出的、不可协商的形状（每条引到 grain 文件）：

1. **打包成目录**：`SKILL.md`（触发即载入的核心指令）+ `references/`（长引用）+ `scripts/`（agent 执行、不读入上下文）。格式 = grain 的 `.claude/rules/skill-authoring.md`。
2. **In-house 前缀元数据**：`name`（小写连字符，禁 `anthropic`/`claude`）、`description`（说清做什么 + 何时载入）、`skillType: step`、`carriers: [Video]`。模板：`packages/backend/src/agent/skills/step/producing-hyperframes-video/SKILL.md`。
3. **注册是代码不是配置**：`listSystemSkills` 扫描 `skills/{step,scene}/`；可见性 = 技能侧 `restrictedTo` ∩ agent 侧 `allowedSkills`（要加进 `CREATION_LITE_ALLOWED_SKILLS`）。
4. **CLI 契约 = stdout 打 JSON + 退出码**，被唯一的 model 面工具 `bash` 消费（360s 超时）。纯变换、自己不调平台工具——模板 `compiling-podcast-episode/scripts/`。
5. **平台工具从脚本里用容器内 `grain` CLI 调**：`grain call <tool> --args '<json>'`（读 `~/.grain/tool-gateway.json` 的 url+token，POST `/api/agent-tools/invoke`）。一个脚本可驱动几百次调用不回到模型。
6. **长任务（渲染）走 `invoke_ext_async` → `await_ext_async`**，不用 `bash` 阻塞（超 15min ChatTurn）。
7. **禁 `.env`、禁自带 provider key**：容器只拿 12h 签名 token；每个花钱动作必须映射到 grain 原生工具（grain 注入 key + 计费）。净新增上游走 server MCP 或新原生工具（读宿主 env）。
8. **状态对齐 grain 三层 run 态**（无 film.json 概念）：run 级 `~/channels/{id}/runs/{label}/`（storyboard.json / output/final.mp4 / publish-manifest.json）、跨集 append-only `library/channel-canon.json`、`config/requirement.json`（headSha 乐观锁，只能经 read/write/patchChannelConfig）。
9. **发布硬门「三件套」**（`carrier-contracts/video.md`）：MP4 + `content.md`（≥1 个真实可点、实际用到的出处）+ 外挂 VTT 字幕（same-source：`renderScriptCaptions` 从 storyboard 生成、`transcribeAudio` 只给时间锚；**禁烧进画面、禁手写**）+ 渲染证明 `proofPath`/`publishProofSealed=true`。
10. **Python 有保障但持久化/资源有限**：`python:3.12` + 预装 `numpy/pandas/httpx/pydantic/pillow/moviepy/ffmpeg/...`；只有 `~/` 持久（`/opt/grain-env` 不持久），容器 ~2CPU/2GB → `kuleshov-ir` 烤进镜像（A1）或 `pip install --user`；重活推给 runner。
11. **runtime 无关**：产品视频 agent 是 runtime 无关的 lite loop（grain 自研 + 测试环境 Codex 都跑）→ 纯 `SKILL.md` + CLI + gateway 调工具，不绑任一 runtime 机制。Codex 那层另需在 `.claude/rules/` 加一条 `paths:` 作用域规则（让 Claude/Codex 两套**编码** harness 都能看到 authoring 约束）。

---

## 3. 关键事实：渲染器同源（卡点消解的证据）

- 我们 `tools/render-remote.sh` → `http://34.212.107.38:7300/render/hyperframes`（`FFMPEG_RENDER_HTTP_TOKEN`，body `{hyperframesVersion, projectTar.url, quality}`，默认 0.7.77）。
- grain `packages/ffmpeg-runner/src/runner/http-render.ts` = 同一 `/render/hyperframes`、同端口、同 token；其注释："与 BullMQ hyperframes-render job **共用同一渲染核**（`hyperframes.ts renderPreparedProject`）……只负责传输鉴权外壳，不改渲染逻辑"。我们 `docs/render-http-api.md` 也直接点了这个文件。
- `runVideoRevisionCycle` → `executeRenderVideoComposition` → `runRemoteHyperframesRender`（队列路径）→ 同一 `renderPreparedProject`。**HTTP 壳和封印工具是同一渲染核的两层薄壳。**
- **唯一动作**：最终 compose 从"调 HTTP 壳"改成"调 `runVideoRevisionCycle` 工具"拿封印。同引擎、同产物、零 grain 侧渲染改动。
- 旧的 SSIM 0.981 帧一致隐忧是 composition 用了 `local()` 系统字体，已被 woff2 新规根治，与封印无关（封印不比对 local-vs-server，只要求 grain 工具产出该 MP4）。

---

## 4. 重塑映射：每个组件在 grain 下变成什么

| 本仓现状 | grain 下的落点 |
|---|---|
| `/produce` SKILL.md（单个大 skill，10 阶段，⏸ 人在环停点，EP spawn subagent） | `producing-kuleshov-video/SKILL.md`：编号 10 阶段 prose + 拒绝跳步的门；无人在环停点（端到端）、无 subagent（lite 单 agent 驱动） |
| `film-ir` 库 + CLI（read/patch/validate/execute） | 原样保留，烤进镜像/`pip --user`；`kuleshov-ir <verb> --json` 就是 §2.4 的 CLI 契约。**这是最强、最现成的资产** |
| `film.json`（全片唯一真相源） | 仍是我们内部 SoT（由 `kuleshov-ir` 管），但要**投影出** grain 的 `storyboard.json`（供 `renderScriptCaptions`）+ 写进 run 级 dir；跨片锚点提升写 `channel-canon.json` |
| film.json 直写拦截（CC hook） | **删**。grain 无 film.json 概念，其状态用 grain 自己的守；我们侧「`kuleshov-ir patch` 是唯一合法写入口」降级为契约 + CI 校验，不靠 hook |
| 花钱动作调自己的 API（GPT-Image/Seedance/MiniMax/Volc/Pexels/render，用 `.env` key；含 `broll-studio` 引擎绑定的 `tools/gpt-image.py` + `tools/seedance.py`） | 全改成 `grain call <tool>` / `invoke_ext`（见 §4 覆盖表）；删 `.env` 依赖 |
| 服务器渲染 `render-remote.sh` | 最终 compose 改走 `runVideoRevisionCycle` 拿封印（§3） |
| `styles/*/contract.json`（plan+render 门，真片校准过数值） | 合并 KA 的更成熟结构（§6 清单 A），**保留 molly 校准数值**；门逻辑落成 contract.json 声明 + 独立 check 脚本（不靠 grain hook） |
| `tools/{measure-render,kuleshov-lint,preflight}.py` | 保留为 check 脚本（去硬编码路径、补 deps 声明）；被 SKILL.md 在对应阶段调 |
| `tools/judge/`（Kimi 做眼睛，网关阻塞） | **眼睛换 grain `describeImage` / `describeVideo`，音频核验 `transcribeAudio`（2026-07-28 拍板，§0.5）**；出题、证据包、引用校验与规则派生判词等确定性阅卷保留在我们侧；KA 的 9 维 rubric + 感知诚实条款作为 rubric 来源合并（§6 A-Tier1）。`runVideoRevisionCycle` 内建的 `describeVideo` spot-check 与 G2 不互相替代 |
| `projects/*`（示例，含 uk 的 35 error 与死脚本） | 保留 1 条干净片（openai-78m-logs）作可跑示例；uk 修或隔离；死脚本清出 |

### provider 覆盖表（§5 的浓缩）
EXISTS = grain 已有原生工具直接用；GAP/PARTIAL = 需处置。

| 我们的花钱动作 | grain 原生工具 | 状态 |
|---|---|---|
| GPT-Image 出图 | `generateImage` | EXISTS（同模型同 base_url） |
| Seedance 视频生成 | `generateImageToVideo` | EXISTS（同 `doubao-seedance-2-0-260128`，我们契约本就抄自 grain） |
| 数字人 HeyGen Avatar4 | `generateTalkingHead` | EXISTS |
| 音乐/BGM | `generateMusic`（minimax music 2.6） | EXISTS |
| 长音 TTS（MiniMax speech） | `synthesizeSpeech` | EXISTS |
| 短音 TTS（Volc seed-audio） | `synthesizeSpeech`（仅 MiniMax） | PARTIAL（功能被 MiniMax 覆盖，引擎不同） |
| **字幕强制对齐（wav2vec2-zh CTC）** | `transcribeAudio`+`renderScriptCaptions`（Whisper ASR + LCS） | **PARTIAL（关键缺口，见 §7）** |
| Pexels/Pixabay 空镜 | `searchPexels*`/`searchPixabay*` | EXISTS |
| **archive.org/Wikimedia 公域** | 无 | **GAP（见 §7）** |
| APIhub youtube 检索 | `downloadVideoClip`（能下已知 URL，不能搜） | PARTIAL |
| OSS 上传 | `uploadFile`（fal CDN） | EXISTS（CDN 不同） |
| 服务器渲染 | `renderVideoComposition`/`runVideoRevisionCycle` | EXISTS（同引擎，§3） |

---

## 5. 封印配方（最终 compose→deliver）

> compose 产出 `projectDir/index.html`（HyperFrames composition + 自带 woff2，就是 `render-remote.sh` 现在打 tar 的东西）
> → 在 grain channel 工作区调 `runVideoRevisionCycle({ projectDir, quality:'standard' })`（**省略 `composition`、quality≠draft，否则不封印**）
> → 同引擎渲染 + validate（lint/inspect/contrast/transition/mediaSlot 五查）+ `describeVideo` spot-check，干净则返回 `finalVideoPath`+`coverPath`+`proofPath`+`publishProofSealed=true`（证明 = 对 video/poster 哈希的 HMAC-SHA256，`GRAIN_SECRET_KEY` 签，**我们侧无法伪造**）
> → 发布（`publishNewDropContent`）：`metadata.carrier='Video'`、`contentPath`（content.md + ≥1 可点出处）、`metadata.videoUrl=finalVideoPath`（必须在 trusted channel runs dir 下）、`coverUrl`、`proofPath`+`publishProofSealed=true`、`metadata.subtitles=[{lang,url,format:'vtt',default:true,label}]`、实测 `durationSec/videoWidth/videoHeight`。

我们 compose 当前**不产出**但门要求的（= §6-B / §7 的活）：① grain 形态 `content.md`；② `renderScriptCaptions` 从 `storyboard.json` 生的 same-source VTT；③ 落在 trusted runs dir；④ grain `storyboard.json`。

> **字幕口径（2026-07-28 同日两次拍板，后者为准）**：
> ② 的仓内侧已落地：`tools/make-vtt.py` 产 same-source VTT（文本取剧本 `audio/narration.txt`、时间取
> 强制对齐字戳），compose 不再烧字幕——规则写进 CLAUDE.md Production Invariant #13 与
> `compose-contract.md` §6，机器门 `kuleshov-lint.py` ⑦。**「禁烧录、外挂 sidecar」这半边不变。**
> ~~"谁产的 VTT" 一度谈定默认走我们自产的 VTT，不必绕 `renderScriptCaptions`~~ —— **随 §0.5 保留面/
> 接缝面拍板反转：接入 grain 后，发布件 VTT 走 grain 的 storyboard 投影 + `renderScriptCaptions`，
> 发布走 `publishNewDropContent`，发布门只认 grain 生成的同源字幕和封印证明。** `make-vtt.py` 降级
> 保留两个角色：仓内独立管线的交付件、对 grain 字幕的本地 QA 对照（中文数字/同音字漂移的探测器）。
> 于是 §7 缺口 1 从「可选质量升级」**恢复为质量风险项**：grain 的 Whisper-ASR+LCS 正是我们为中文
> 否掉的方法，wav2vec2-zh CTC 原生工具升回相 1–2 的并行推进项。存量片（status 已 review/delivered）
> 按旧政策烧录，不追溯。CLAUDE.md Invariant #13 需补一句适用范围注（仓内独立跑 vs grain 接入后）。

---

## 6. 清单 A（搬效果） + 清单 B（收交付）

### 清单 A — 从 KuleshovAgent 搬效果资产（都落成 contract.json 声明 / check 脚本 / SKILL.md prose）

**A-Tier1**
- **合同成熟度**：每数值叶子 `amend:[lo,hi]` 带宽 + `craft` 工艺协议（`assemble_from_empty`/`document_chrome`/`pixel_anchor_assembly`）+ `inviolable` 不可违条款 + `incompatible_topics`（花钱前 style×topic 硬查）。⚠️ **molly 的合同数值是真 Golden 片 measure-render 校准过的 → 合并结构、保留数值。**
- **工艺门"数存在≠数工艺"**：`collage_craft`/`document_craft`/`pixel_craft`/`style_consistency`——花钱前拦风格退化。落成 storyboard 阶段的 check 脚本。
- **评委升级**：9 维 rubric（含 D8 创意/D9 网感）+ 感知诚实条款（夸不存在元素→整份作废）+ 规则派生判词（不信模型自报）+ 按画幅锚 Golden。可直接复用 grain `describeVideo` 做载体。

**A-Tier2**
- 三个新实测门：`layout_check`（headless 渲染查文字溢出/重叠）、audio-QC 真听门、字幕对齐门。
- **知识治理规程** `knowledge-governance.md`：principle-vs-rule 两问、`补偿@/兼容@/策略@` 标注、单一权威落点、改代删除 playbook。—— 知识包不腐烂的元资产。
- 指令优先级 `instruction_precedence`：user > constitution > project_contract > style_contract > stage_skill > provider_adapter。品味宪法从 CLAUDE.md 抽成独立文件。

**A-Tier3（结构升级）**
- 三车道风格泛化（news=拼贴/knowledge=像素/whiteboard 兜底）+ 选风格 skill。
- brief 入口形式化：`brief.schema.json` + interview + `topic_flags` 风险预检 + `research_min_facts` 地板。
- `/produce` 拆 12 个动名词 stage skill（grain step-skill 天然支持）。

### 清单 B — 收成 grain step-skill

**B1 打包与接口**
- 建 `producing-kuleshov-video/`（§2 形态）；`SKILL.md` = 编号 10 阶段 prose；`scripts/` = `kuleshov-ir`/produce 纯变换 CLI。
- Video carrier 路由表加一行 + 加进 `CREATION_LITE_ALLOWED_SKILLS` + `.claude/rules/` 加 `paths:` 规则。
- 顶层消费方 README（知识/工具/示例/基建 四类清点 + "怎么被 grain 接手"）。
- 出 `schema/film.schema.json`（从 pydantic 生成，文档到处引用却不存在）。

**B2 解耦**
- 花钱动作全改 `grain call`/`invoke_ext`（§4 覆盖表）；删 `.env` 依赖，出 `.env.example` 仅列本地开发用。
- film.json→`storyboard.json` 投影器 + 写 run 级 dir + 锚点写 `channel-canon.json`。
- 最终 compose 改走 `runVideoRevisionCycle`（§5）。
- 去 `tools/*.py` 硬编码路径、补 deps（numpy）、写前置清单（ffmpeg/hyperframes/docker）。

**B3 一致性欠账（不修消费方第一次 validate 就翻车）**
- `uk-argentina-feud`（35 error、却 delivered/合 main）：修，或明确降级为"历史样本、不过 validator"。
- 补 `test-shots.json`（全仓 SOP 强制、实际一个不存在 → 迭代/回归规程当前跑不起来）。
- 清腐坏：translation-table 全 `[假设]`（验证或标注）、pixel-chronicle 未过考片却交付、`DESIGN.md` 自相矛盾、发布包已取消却留在 `out/`、模板 m1-v2 vs 样片 m0-v1、CLAUDE.md "两包"实际三包、34 个死脚本指向已删 worktree。

### 清单 C — 不做（丢给 grain harness），但设计留痕为接口文档
EP 主循环 / AgentRuntime 双实现 / toolface 派发 + hook 布线 / ledger append-only 强制 / state_machine 驱动 / 预算预留 / flock / shadow_compare / CI runner。→ 以文档留痕（loop 设计、四条结构性保证、grain 交付契约），作为"grain harness 怎么驱动这个包"的接口说明。

---

## 7. 缺口与需决策项

| # | 缺口 | 处置选项 | 建议 |
|---|---|---|---|
| 1 | **字幕 CTC 对齐**（2026-07-28 §0.5 拍板后恢复为**质量风险项**：发布件 VTT 走 grain `renderScriptCaptions`，发布门只认 grain 同源字幕）：grain 用 Whisper-ASR+LCS，正是我们为中文否掉的方法（数字/同音字漂移）；自产 wav2vec2 VTT 只作本地 QA 对照，不作发布件 | (a) 给 grain 加 wav2vec2-zh CTC 原生工具，喂 `renderScriptCaptions` 时间锚（A1 PR，顺带提升 grain 全部中文字幕质量，好卖）；(b) 接受 grain 方法 + 对我们中文内容重验；(c) v1 先用 grain 法、CTC 列 fast-follow | **(a)，与相 1–2 并行**；CTC 未就绪期间按 (c) 过渡，但中文片发布前必须过 `make-vtt.py` 本地对照 QA（漂移超限就停 review，不静默放行） |
| 2 | **archive.org/Wikimedia 公域素材**：grain 无此工具（只有 Pexels/Pixabay） | (a) 加原生工具（A1）；(b) v1 砍掉公域层，靠 Pexels/Pixabay+Seedance+`downloadVideoClip`；(c) APIhub 走 MCP | **(b) 做 v1，(a) 按需 fast-follow** |
| 3 | **content.md 发布件**：门硬要求（≥1 可点出处）；我们曾取消"发布包" | 注意：取消的是小红书/抖音**文案+封面包**（另一个东西），grain 的 content.md 是视频描述+出处，是**不同 artifact** → 在 deliver 阶段从 research 出处生成一份最小 content.md | **补最小 content.md**（不与"取消发布包"矛盾） |
| 4 | **storyboard.json / runs-dir / film.json 并存** | film.json 留作内部 SoT；加投影器出 grain storyboard.json + 落 run 级 dir + 锚点写 channel-canon | **加映射适配层，不重写 SoT** |
| — | **A1 vs A2** | A1（first-party PR，能加原生工具/改路由表/same-source 字幕）vs A2（用户 skill，做不到上述） | **A1**（缺口 1、路由行、字幕都要求 A1） |

~~**唯一真需要 grain 团队拍板的**：缺口 1 的 (a)~~ ~~2026-07-28 作废：字幕已谈定走我们自产 VTT~~ —— **2026-07-28 §0.5 拍板后再更新：发布件字幕走 grain 同源链路，缺口 1 的 (a) 重新成为需 grain 团队排期的项（性质仍是加法，不是改它的门；未排上期用 (c) 过渡）。**

---

## 8. 施工顺序（A+B 一次到位，但按依赖分相；整体作为一个 skill 交付）

**相 0 · 走通骨架（proof-of-seam，先做，卡后续投入）**
- `kuleshov-ir` 烤进/装进 grain 容器；建 `producing-kuleshov-video/` 骨架 SKILL.md。
- 拿 1 条已交付的干净片（`openai-78m-logs`）在 grain 测试环境（Codex runtime）端到端跑：花钱动作走 `grain call` → compose 出 `index.html` → `runVideoRevisionCycle` 拿真封印 → 发布过门。
- **验收**：产出带合法 `publishProofSealed=true` 的成片，publish gate 全绿。证明整条缝（skill+CLI+grain 工具+渲染+封印+发布）在真机跑通。

**相 1 · provider 适配 + 状态映射**（B2 主体）
- 全部花钱动作改 grain 工具；film.json→storyboard.json 投影器；runs-dir 落位；content.md 生成；VTT 走 grain `renderScriptCaptions`（§0.5 定稿口径）+ `make-vtt.py` 本地对照 QA + 缺口 1（CTC）立项。
- **验收**：全 10 阶段无 `.env`、无自带 key 跑通；三件套齐、发布门绿。

**相 2 · 效果搬运**（清单 A 全量）
- 合同结构合并（保留校准数值）+ 工艺门 + 9 维评委 + 感知诚实 + layout/audio 门 + knowledge-governance + brief schema + stage 拆分 + 三车道泛化。
- **验收**：Codex 翻车片类型（拼贴退写实/静态持有超限）能被工艺门在花钱前红；评委对现有片库盲评秩相关 ≥ 目标；风格合同违约按带宽 amend / 越界带标记停 review。

**相 3 · 交付硬化**（清单 B3 + B1 收尾）
- 修/隔离 uk-argentina；补 test-shots.json；清腐坏引用与死脚本；消费方 README；`.claude/rules` 规则；Video 路由表行；film.schema.json。
- **验收**：干净 checkout 下 `kuleshov-ir validate` 全绿；消费方按 README 零踩坑接入；golden-set 回归可跑。

**缺口轨（与相 1–2 并行）**：字幕 CTC 原生工具（缺口 1，§0.5 口径下为并行推进项，需 grain 团队排期；未就绪按 §7 (c) 过渡）；archive.org 决策（缺口 2）。

---

## 9. 待定/开放
- 缺口 1（字幕 CTC 原生工具）需 grain 团队排期（§0.5 口径下重新变为并行推进项；未排上期按 §7 (c) 过渡）。
- Volc 短音（缺口）：默认并入 MiniMax，除非短音时间锚有硬需求。
- `channel-canon.json` 与我们"跨片锚点库提升"的字段对齐细节，留到相 1 落地时定。
- ~~**`broll-studio` 是否进交付面、以何形态**~~（2026-07-28 用户拍板：**进**，CLAUDE.md 交付面表已同步）：进的是知识与机器门（材质语汇 / 三闸门 / 画幅几何 / QA 判据 / lint / `broll-profile.py` 等纯变换工具）；引擎绑定的直连客户端 `gpt-image.py` + `seedance.py` 不进，接缝后换 `generateImage` / `generateImageToVideo`；`pixel-broll` / `collage-broll` 指针壳属本仓触发面，不进。
- CLAUDE.md Production Invariant #13（字幕 sidecar）需补适用范围注：仓内独立跑交付 `make-vtt.py` 产的 VTT；grain 接入后发布件 VTT 由 `renderScriptCaptions` 产，`make-vtt.py` 转本地对照 QA。
