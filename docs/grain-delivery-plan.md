# Kuleshov → grain 交付施工稿（外挂化）

> 状态：**待作者过稿**（2026-07-24 起草）。
> 依据：本仓现状评估 + `~/KuleshovAgent` 效果资产测绘 + `~/deeplang/grain` 消费方契约逆向 + 渲染器同源核实（四轮调查，证据均引到具体文件）。
> 决策前提（用户 2026-07-24 拍板）：不再自造 agent 链路；把本仓打磨成 **harness 无关的能力包（外挂）** 交付给团队 harness（线上自研 + 测试环境 Codex 做 runtime，消费方 = `/Users/admin/deeplang/grain`）；**molly 作底 + 从 KuleshovAgent 搬效果**；范围 **A+B 一次到位**。

---

## 0. 结论摘要（TL;DR）

- **外挂的最终形态不是"一个可移植仓库 + README"，而是 grain 里的一个 In-house Video「生产方法」step-skill**：`producing-kuleshov-video/`（`SKILL.md` 编号 10 阶段 prose + `scripts/` 放 `kuleshov-ir`/produce 纯变换 CLI + `references/`），在 Video carrier 路由表加一行。驱动它的是 grain 的**单 agent tool-loop**（lite 链路），不是我们的 EP loop——这印证了"编排层丢给 harness"。
- **渲染证明卡点已消解。** 我们线上服务器渲染器 = grain 渲染核包了层 HTTP；把最终 compose 走 grain 的 `runVideoRevisionCycle` 拿 `publishProofSealed` 不需要 grain 改任何渲染代码，只是从"HTTP 壳"换到"工具/队列壳"，同引擎同产物。
- **绝大多数花钱动作 grain 已有对应原生工具**（出图/Seedance 视频/数字人/音乐/长音 TTS/Pexels/下载/渲染都 EXISTS），真正的缺口只有 4 处（字幕 CTC 对齐、archive.org 公域素材、youtube 搜索、Volc 短音），每处有明确处置。
- **重塑工作几乎全在我们这侧**，有现成模板可抄（`compiling-podcast-episode` 的纯变换 Python、`producing-hyperframes-video` 的 pipeline-as-one-skill）。需要 grain 团队点头的只剩"字幕 CTC 原生工具要不要加"这类**加法**，不是"改它的门"。
- 采用 **A1（first-party In-house skill，走 grain PR）**：因为要在 Video 路由表加行、要补原生工具、要 same-source 字幕——A2（用户 skill）做不到这些。

---

## 1. 背景与决策

三棵树：
| 树 | 是什么 | 角色 |
|---|---|---|
| `~/kuleshov`(+`molly` worktree) | GitHub `Niko77066/kuleshov`，当前文件仓（M0 手工作坊） | **要交付的外挂本体** |
| `~/KuleshovAgent` | GitHub `Niko77066/KuleshovAgent`，62 commits 的完整 agent 系统 | **效果设计来源；agent 编排层丢弃** |
| `~/deeplang/grain` | 团队自研 harness（TS/Bun turbo monorepo） | **外挂的消费方** |

这次转向与自家蓝图（v3.4 §02/§10「编排层越薄红利越大、护城河在知识+治理」）自洽：把本该薄的 L1 编排层让给 grain，把厚重的 L2 知识 / L3 契约 / L4 工具做成外挂。

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

- 我们 `tools/render-remote.sh` → `http://34.212.107.38:7300/render/hyperframes`（`FFMPEG_RENDER_HTTP_TOKEN`，body `{hyperframesVersion, projectTar.url, quality}`，默认 0.7.3）。
- grain `packages/ffmpeg-runner/src/runner/http-render.ts` = 同一 `/render/hyperframes`、同端口、同 token；其注释："与 BullMQ hyperframes-render job **共用同一渲染核**（`hyperframes.ts renderPreparedProject`）……只负责传输鉴权外壳，不改渲染逻辑"。我们 `docs/render-http-api.md` 也直接点了这个文件。
- `runVideoRevisionCycle` → `executeRenderVideoComposition` → `runRemoteHyperframesRender`（队列路径）→ 同一 `renderPreparedProject`。**HTTP 壳和封印工具是同一渲染核的两层薄壳。**
- **唯一动作**：最终 compose 从"调 HTTP 壳"改成"调 `runVideoRevisionCycle` 工具"拿封印。同引擎、同产物、零 grain 侧渲染改动。
- 旧的 SSIM 0.981 帧一致隐忧是 composition 用了 `local()` 系统字体，已被 woff2 新规根治，与封印无关（封印不比对 local-vs-server，只要求 grain 工具产出该 MP4）。

---

## 4. 重塑映射：每个组件在 grain 下变成什么

| molly 现状 | grain 下的落点 |
|---|---|
| `/produce` SKILL.md（单个大 skill，10 阶段，⏸ 人在环停点，EP spawn subagent） | `producing-kuleshov-video/SKILL.md`：编号 10 阶段 prose + 拒绝跳步的门；无人在环停点（端到端）、无 subagent（lite 单 agent 驱动） |
| `film-ir` 库 + CLI（read/patch/validate/execute） | 原样保留，烤进镜像/`pip --user`；`kuleshov-ir <verb> --json` 就是 §2.4 的 CLI 契约。**这是最强、最现成的资产** |
| `film.json`（全片唯一真相源） | 仍是我们内部 SoT（由 `kuleshov-ir` 管），但要**投影出** grain 的 `storyboard.json`（供 `renderScriptCaptions`）+ 写进 run 级 dir；跨片锚点提升写 `channel-canon.json` |
| film.json 直写拦截（CC hook） | **删**。grain 无 film.json 概念，其状态用 grain 自己的守；我们侧「`kuleshov-ir patch` 是唯一合法写入口」降级为契约 + CI 校验，不靠 hook |
| 花钱动作调自己的 API（Seedance/MiniMax/Volc/Pexels/render，用 `.env` key） | 全改成 `grain call <tool>` / `invoke_ext`（见 §5 覆盖表）；删 `.env` 依赖 |
| 服务器渲染 `render-remote.sh` | 最终 compose 改走 `runVideoRevisionCycle` 拿封印（§3） |
| `styles/*/contract.json`（plan+render 门，真片校准过数值） | 合并 KA 的更成熟结构（§6 清单 A），**保留 molly 校准数值**；门逻辑落成 contract.json 声明 + 独立 check 脚本（不靠 grain hook） |
| `tools/{measure-render,kuleshov-lint,preflight}.py` | 保留为 check 脚本（去硬编码路径、补 deps 声明）；被 SKILL.md 在对应阶段调 |
| `tools/judge/`（Kimi，网关阻塞） | 换 KA 的评委（gpt-5.6-sol + gemini，9 维）；或直接调 grain 的 `describeVideo`（`runVideoRevisionCycle` 已内建 spot-check） |
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
> → 发布：`metadata.carrier='Video'`、`contentPath`（content.md + ≥1 可点出处）、`metadata.videoUrl=finalVideoPath`（必须在 trusted channel runs dir 下）、`coverUrl`、`proofPath`+`publishProofSealed=true`、`metadata.subtitles=[{lang,url,format:'vtt',default:true,label}]`、实测 `durationSec/videoWidth/videoHeight`。

我们 compose 当前**不产出**但门要求的（= §6-B / §7 的活）：① grain 形态 `content.md`；② `renderScriptCaptions` 从 `storyboard.json` 生的 same-source VTT；③ 落在 trusted runs dir；④ grain `storyboard.json`。

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

### 清单 B — 收成 grain 外挂

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
| 1 | **字幕 CTC 对齐**：grain 用 Whisper-ASR+LCS，正是我们为中文否掉的方法（数字/同音字漂移）；且门只认 `renderScriptCaptions` 产的 VTT，我们自产 wav2vec2 VTT 会被判"手写"拒收 | (a) 给 grain 加 wav2vec2-zh CTC 原生工具，喂 `renderScriptCaptions` 时间锚（A1 PR，顺带提升 grain 全部中文字幕质量，好卖）；(b) 接受 grain 方法 + 对我们中文内容重验；(c) v1 先用 grain 法、CTC 列 fast-follow | **(a)** ——干净的加法，对 grain 团队是普惠升级 |
| 2 | **archive.org/Wikimedia 公域素材**：grain 无此工具（只有 Pexels/Pixabay） | (a) 加原生工具（A1）；(b) v1 砍掉公域层，靠 Pexels/Pixabay+Seedance+`downloadVideoClip`；(c) APIhub 走 MCP | **(b) 做 v1，(a) 按需 fast-follow** |
| 3 | **content.md 发布件**：门硬要求（≥1 可点出处）；我们曾取消"发布包" | 注意：取消的是小红书/抖音**文案+封面包**（另一个东西），grain 的 content.md 是视频描述+出处，是**不同 artifact** → 在 deliver 阶段从 research 出处生成一份最小 content.md | **补最小 content.md**（不与"取消发布包"矛盾） |
| 4 | **storyboard.json / runs-dir / film.json 并存** | film.json 留作内部 SoT；加投影器出 grain storyboard.json + 落 run 级 dir + 锚点写 channel-canon | **加映射适配层，不重写 SoT** |
| — | **A1 vs A2** | A1（first-party PR，能加原生工具/改路由表/same-source 字幕）vs A2（用户 skill，做不到上述） | **A1**（缺口 1、路由行、字幕都要求 A1） |

**唯一真需要 grain 团队拍板的**：缺口 1 的 (a) —— 在 grain 加一个 wav2vec2-zh CTC 字幕原生工具。其余都是我们这侧的活或可 v1 绕过。

---

## 8. 施工顺序（A+B 一次到位，但按依赖分相；整体作为一个 skill 交付）

**相 0 · 走通骨架（proof-of-seam，先做，卡后续投入）**
- `kuleshov-ir` 烤进/装进 grain 容器；建 `producing-kuleshov-video/` 骨架 SKILL.md。
- 拿 1 条已交付的干净片（`openai-78m-logs`）在 grain 测试环境（Codex runtime）端到端跑：花钱动作走 `grain call` → compose 出 `index.html` → `runVideoRevisionCycle` 拿真封印 → 发布过门。
- **验收**：产出带合法 `publishProofSealed=true` 的成片，publish gate 全绿。证明整条缝（skill+CLI+grain 工具+渲染+封印+发布）在真机跑通。

**相 1 · provider 适配 + 状态映射**（B2 主体）
- 全部花钱动作改 grain 工具；film.json→storyboard.json 投影器；runs-dir 落位；content.md 生成；VTT 走 grain 法（interim）+ 缺口 1 立项。
- **验收**：全 10 阶段无 `.env`、无自带 key 跑通；三件套齐、发布门绿。

**相 2 · 效果搬运**（清单 A 全量）
- 合同结构合并（保留校准数值）+ 工艺门 + 9 维评委 + 感知诚实 + layout/audio 门 + knowledge-governance + brief schema + stage 拆分 + 三车道泛化。
- **验收**：Codex 翻车片类型（拼贴退写实/静态持有超限）能被工艺门在花钱前红；评委对现有片库盲评秩相关 ≥ 目标；风格合同违约按带宽 amend / 越界带标记停 review。

**相 3 · 交付硬化**（清单 B3 + B1 收尾）
- 修/隔离 uk-argentina；补 test-shots.json；清腐坏引用与死脚本；消费方 README；`.claude/rules` 规则；Video 路由表行；film.schema.json。
- **验收**：干净 checkout 下 `kuleshov-ir validate` 全绿；消费方按 README 零踩坑接入；golden-set 回归可跑。

**缺口轨（与相 1–2 并行）**：字幕 CTC 原生工具（缺口 1，待 grain 团队拍板）；archive.org 决策（缺口 2）。

---

## 9. 待定/开放
- 缺口 1（字幕 CTC 原生工具）需 grain 团队一次拍板。
- Volc 短音（缺口）：默认并入 MiniMax，除非短音时间锚有硬需求。
- `channel-canon.json` 与我们"跨片锚点库提升"的字段对齐细节，留到相 1 落地时定。
