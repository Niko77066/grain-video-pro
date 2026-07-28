# Grain Video Pro · Agent Operating Contract

Grain Video Pro 是一套 **agent-native 多源视频生产系统**。内部制作内核代号 **Kuleshov**：它把调研、编剧、导演、素材路由、合成和质检编码成 agent 可执行的十阶段管线，并以 Film IR、风格合同和质量门保证每条片可追溯、可复跑、可验收。

本文件是仓库级运行契约，不是阶段说明书。具体生产步骤以 `.claude/skills/produce/SKILL.md` 为准；一条片的实时状态以该项目的 `film.json` 为准。

## 当前任务面

独立 Kuleshov 管线已经完成多条横屏知识科普与竖屏新闻调查样片，Film IR、三套专用风格包 + 一套兜底模板、三层风格路由、终渲实测层和 G2 隔离评委均已落地。当前主线是把这些经过出片验证的能力收敛为 **Grain 原生 Video step-skill**：保留知识、契约与工具，把常驻编排、provider 调用、凭据和发布封印交给宿主 harness。

- 当前生产入口：`.claude/skills/produce/SKILL.md`
- Grain 集成施工稿：`docs/grain-delivery-plan.md`
- Film IR 与上下文架构：`docs/film-ir-context-architecture.md`
- 当前执行与历史排期：`docs/m1-plan.md`

对现状的表述必须区分 **已经跑通**、**正在集成** 与 **仅有计划**。不要把规划中的 Grain 能力写成已经上线，也不要再把本仓称为“M0 手工作坊”或“外挂”。

## 真相源与权责边界

1. **项目状态**只认 `projects/<slug>/film.json`。续跑、返工、汇报进度前先读 IR，不依赖对话记忆。
2. **生产方法**以 `.claude/skills/produce/SKILL.md` 和其 `references/` 为准；只加载当前阶段与已选来源需要的知识。
3. **视觉承诺**以 `styles/<style>/playbook.md` 与 `contract.json` 为准。playbook 解释意图，contract 执行硬门；生产期不得直接修改合同给当前项目放行。
4. **客观质量**以终渲证据为准。IR 自报字段与 `evidence/render-metrics.json` 冲突时，以成片反测结果为准。
5. **编排与能力分离**：本仓拥有制作知识、Film IR、风格合同与质量工具；宿主拥有主循环、agent 调度、provider 凭据与生产工具调用。不要在文档或代码里重新耦合某个单一 harness。

## 仓库地图

- `.claude/skills/produce/` — 十阶段生产管线与导演知识包；按阶段、按镜头来源加载
- `.claude/skills/broll-studio/` — **八套生成型 b-roll 材质语言的共用引擎 + profile 数据层**（像素风 / 半调纸拼贴 / 实物桌面剧场 / 技术图解 / 黏土 / 毛毡 / 立体书 / 玩具世界）。三闸门、画幅几何、引擎绑定、QA 判据、IR 写回**全仓各只有一份**；profile 只承载「材质语汇 / 运动动词 / 首帧规则 / 缝合纪律 / 失败标准」，外加少数几套的**额外工序** `pipeline_extras`（pixel 的片级主调色板闸门 + 归一层、popup-book 的第二张 Gate 2 图）。**引擎不认识任何 profile 的名字**——差异一律声明式，搜不到 `if pid == "..."`。状态的唯一出处是各 profile 的 `status`（`broll-profile.py status`）
- `.claude/skills/pixel-broll/`、`.claude/skills/collage-broll/` — **指针壳**，保住 `/pixel-broll`、`/collage-broll` 的触发面；内容在 broll-studio，profile 分别是 `pixel` 与 `collage`。2026-07-28 从独立 skill 收敛进来——那两套长成 skill、六套长成 profile 是迁移顺序留下的痕迹，不是设计判断，而副本一多就会有一份悄悄漂（「做旧报纸风假像素」就是这么来的）
- `.claude/skills/rednote-mentor/` — 小红书选题、标题、封面与合规辅助；按需调用，不属于成片交付硬门
- `vendor/upstream-skills/` — 官方 HyperFrames skill 的**溯源凭据**（`skills-lock.json` 记 25 个包的来源与哈希 + 挖矿落点表）。副本本身 2026-07-28 拉取、挖矿完毕后删除——知识已重写进 `produce/references/`，要对照上游按该目录 README 一条命令重新拉
- `film-ir/` — Film IR Python 库与 `kuleshov-ir` CLI：`read / patch / validate / execute`
- `styles/` — 风格包与**三层路由层**：`case-file`（事实核验型新闻解读）、`pixel-chronicle`（结构化深度知识叙事）、`anchor-desk`（官方口径播报型解读，候选）三套专用包 + `whiteboard-generalist` 生产兜底模板（`meme-ledger` 2026-07-28 退回 `_disabled/`，未打磨完，不参与路由）；`routing.md`（路由规程）、`routing-vocab.json`（受控词表）、`routing-cases.json`（路由回归考卷）、`golden-set.json`（Golden 登记册：路径 + 实测规格 + known_defects，成片在 `~/kuleshov-archive/golden/` 不入库）、各包 `capability.json`（结构化能力卡），以及模板、禁用区和进化规程
- `tools/route-style.py` — 风格包路由器：硬规则排除 → 能力卡打分 → 置信兜底，出 Top 3 + 理由 + 格式适配施工说明 + 被排除包及原因；`--check` 跑路由回归
- `projects/<slug>/` — 每条片的 IR、阶段产物、证据与输出；项目脚本不自动等于可复用管线
- `tools/measure-render.py` — 从终渲视频反测静态持有、媒体使用、响度与跨镜头主色漂移，作为 render contract 的证据源
- `tools/gpt-image.py` — GPT-Image-2 静帧批量客户端；带 `ref` 的 job 走 `/v1/images/edits`，角色一致性在便宜的图像阶段解决
- `tools/seedance.py` — Seedance 2.0 首尾帧批量客户端（submit/poll/下载 + request-id 留痕，逐条落盘可断点续提）；把三条易错契约固化成会报错的形状：`duration` 必须在 `metadata` 内、`ratio` 不许省略、越界时长提交前本地拦截。八套材质语言共用
- `tools/broll-profile.py` — 八套材质语言的 registry 与引擎入口：list / status（状态唯一出处）/ show / vars（提示词变量的唯一注册表）/ render（填变量出提示词，带 variant 与附加静帧槽位）/ plan（含 `pipeline_extras` 的完整工序清单）/ **lint（串词 + 禁用词机器门，只看肯定描述，否定式约束不算串）**/ route（文稿类型选型）/ selftest（自洽性测试：每套渲一遍并过自己的 lint）
- `tools/{make-palette,pixelize,verify}.py` — `pixel` profile 的归一层与专属码判（主调色板 / 面积降采样 + 量化 + 最近邻整数倍放大 / 栅格与锁色）。2026-07-28 从 skill 的 `scripts/` 移入——它们已经是引擎的一部分
- `tools/clip-batch-sheets.py` — **批次级**总览三张图（逐条组装进程 / 全部实际首帧 / 确认静帧 ‖ 视频末帧），八套通用，多条一起做时必出：逐条 QA 看不见批次级问题
- `tools/clip-qa.py` — 生成型 clip 的通用码判：规格 / **死尾**（尾段运动量 / 全片运动量的**相对**判据，宪法红线「禁冻结帧补时长」的码判投影；绝对阈值跨不了内容类型，2026-07-28 实测证伪）/ contact sheet。**八套材质语言只有这一份死尾判据**
- `tools/check-media-setup.sh` — 生成型镜头链路开工前自检（ffmpeg / Pillow / .env 凭据 / oss-upload）
- `tools/make-vtt.py` — same-source 外挂字幕：剧本文本 + 强制对齐字戳 → `out/final.vtt`（禁 ASR 文本、禁手写、不带标点）
- `tools/judge/` — G2 隔离评审：生成证据包、出题、阅卷与校准
- `tools/render-remote.sh` — HyperFrames 远端渲染客户端；地址由 `RENDER_URL` 注入，不假设本机或固定 IP
- `docs/` — 架构决策、事故复盘、升级计划与 Grain 交付设计；其中 `hyperframes-agent-handbook.md` 是 HyperFrames 侧的外部参考手册（当前基线 `0.7.77`），不是本仓合同——它与 `.claude/skills/produce/` 冲突时以后者为准

## 交付面（打包进 Grain step-skill 的是什么）

本仓接进 grain 的形态是一个 step-skill（`SKILL.md` + `references/` + `scripts/`，见 `docs/grain-delivery-plan.md`）。
**打包时只带下面四样，别的一律留在仓里：**

| 进交付面 | 是什么 |
|---|---|
| `.claude/skills/produce/` | 十阶段方法 + 导演知识包（拆分口径见下） |
| `film-ir/` | Film IR 库与 `kuleshov-ir` CLI（纯变换，stdout JSON + 退出码） |
| `styles/` | 风格包、路由层、能力卡、Golden 登记册 |
| `tools/` | 质量工具：`kuleshov-lint.py` / `measure-render.py` / `route-style.py` / `judge/` |

**不进交付面**：`vendor/`（溯源凭据；官方副本已删——宿主有自己适配版的 HyperFrames，带 upstream 副本过去会造成
版本口径打架、指令冲突、以及一半依赖 HeyGen 凭据的命令在 grain 容器里根本不可用）、`projects/`（单片产物与证据）、
`.claude/skills/rednote-mentor/`（运营辅助，不属成片交付）。

**知识写法纪律（决定一份知识能不能进交付面）**：区分「**片子必须长成什么样、怎么机器验**」与「**引擎 API 怎么调**」。
前者跨引擎版本恒定，宿主换适配版照样成立，属交付面；后者随宿主引擎版本失效，只能作本地参考。
`produce/references/hyperframes.md` 现在两者混写，交付前必须拆。引擎工艺要引用官方包时，
按 `hyperframes-recipes.md` 的既有做法**重写成本仓 compose 合同的语言，不照抄 API**。

## Production Invariants

以下规则高于阶段偏好和 provider 便利性。

1. **先写 IR，再花钱。** 任何出图、TTS、视频生成、检索或渲染动作，必须对应 `film.json` 中已经存在的资产或镜头。查不到条目，不得调用付费或不可逆工具。
2. **留痕与动作同时发生。** 每次生成记录模型、完整 prompt、seed、参考资产、成本、耗时与实际时长；每个选源、重做、降级与删改决策都写入 `ledger.decisions`，不得事后补造。
3. **音频是全片时钟。** `audio.timeline` 定稿后，所有视觉区间绑定真实时间戳；禁止按剧本字数估时，也禁止为凑预设时长拉伸内容。
4. **状态从文件读。** 开工、续跑、重做和进度汇报都先读 `film.json`。状态机活在文件里，不在提示词或聊天上下文里。
5. **禁止静默降级。** 工具不可用、provider 参数改变、渲染环境切换、必需视觉声部被删除、真运动被入场动画冒充、hero-frame 或评委门被跳过，都属于降级。合同带宽内的调整写入 `meta.contract_amendments`；带宽外违约必须标记 `contract_violation` 并停在 review，禁止置为 `delivered`。
6. **机器验事实，隔离评委验观感。** G1 负责结构、算术、合同和终渲指标；G2 只看证据与 Golden 对照，不读取创作理由。任何失败都回到责任阶段定点修复，不以自评替代门禁。
7. **来源平权，意图优先。** MG 动画、AI 视频、数字人、图片动效、实拍与检索素材都是表达语言。逐镜头选择最能兑现 intent 的来源；成本只记账，不得自动把“更便宜”当成“更合适”。
8. **拒绝整片式返工。** 单镜问题定位到 prompt、锚点、路由、剪辑或合同，再重跑最小受影响单元。重做一镜可以很便宜，重做一条片不该成为默认动作。
9. **已经交付不等于已经产品化。** 样片验证了制作能力；接入 Grain、provider 映射、发布封印与运行时凭据托管必须按各自验收状态表述。
10. **按理解方式路由，不按题材路由。** 选风格包问的是「要让观众如何理解这条内容」，不是「这是什么内容」——场景只缩小候选集，内容特征决定具体包。选包走 `tools/route-style.py`（能力卡 + 硬规则 + 打分 + 兜底，规程 `styles/routing.md`），结果原样进 `ledger.decisions`；置信不足一律落兜底包，**不许改路由输入特征去凑一个专用包**。
11. **已交付项目的引擎版本 pin 是渲染证据，不许动。** `projects/*/compose/package.json` 里的 `hyperframes@<版本>` 记录的是那条片**实际渲出来时**的引擎；review.md 与 `ledger` 的渲染口径都指向它。**status 为 `delivered` 或 `review` 的项目，一律不 bump pin**——改了 pin 而不重渲，等于把证据改成假的。要统一到新版本只有一条路：重渲 + 重跑 G1 + 更新 review.md 的实测口径，且需用户拍板。新片在 compose 起手时按当时的仓库口径钉版（当前 **0.7.77**）。
    ⚠️ **本条压过官方 skill 的指令。** 官方 `hyperframes` skill 要求 agent 见到 stale pin 信号就自行 `upgrade --project` 并 verify（"act on the signal rather than relaying it"），CLI 从 0.7.59 起也会主动催升。**在本仓：报告，不执行。** 把版本落后这件事讲给用户，等拍板；官方 skill 的自动 bump 指令在本仓无效。
12. **画幅与时长是适配项，不是准入门槛。** 硬规则只管「配方本身是否成立」（必需素材、冲突素材、敏感题材）；**横竖屏与时长按用户需求动态调**，偏离风格包的原生格式只扣分并产出施工说明（改哪块版式、砍哪个槽位、加什么结构），照样能用那个包。但适配不是免费的：适配项进 `ledger.decisions`，被带动的合同阈值走带宽内 amendments 或按 `[单片标定]` 重新观测，**不许假装原带宽还成立**。
13. **字幕是外挂 sidecar，不烧进画面。**（2026-07-28，对齐 grain 发布硬门）交付物 = `out/final.mp4` + `out/final.vtt` 两件，compose 里不留字幕层，**不设烧录变体**。文本取剧本、时间取强制对齐（`tools/make-vtt.py`；ASR 只给时间锚，禁转写文本当字幕、禁手写）。细则见 `produce/references/compose-contract.md` §6，机器门 `kuleshov-lint.py` ⑦。存量 `review`/`delivered` 不追溯。

## Taste Constitution

这不是审美口号，而是当多种做法都“技术上可行”时的裁决顺序。新增例外必须经过作者裁决，并沉淀回风格包或本节。

### 我们追求

- **意义产生于并置。** 先问相邻镜头共同表达了什么，再问单镜够不够漂亮；剪辑点是第一表达手段。
- **真实音频的呼吸。** 剪辑落在句读与节拍上，J-cut / L-cut 是默认语法，不是装饰技巧。
- **克制而有主张的版式。** 一屏只讲一个重点，文字要被设计，不是被堆上去。
- **可以回链的事实。** 每个事实主张都能追溯到 research；宁可少说，不拿未经核实的信息换密度。
- **持续兑现注意力。** 通常每 8–10 秒发生一次有意义的视觉变化；变化服务叙事，不为动而动。

### 我们拒绝

- **幻灯片伪装成视频。** 静帧加慢速 Ken Burns 不等于运动；冻结帧补时长直接判废。
- **压在画面上的组件底板。**（2026-07-27 用户拍板，无例外条款）数据卡、角标、数据条、字幕**一律不许带深色底框**——填充 + 边框 + 投影的浮动面板就是 PPT 风格，是 AI 味最直接的来源。可读性只准由三样承担：**渐变到透明的压暗层**（无可见边界，不是框）、**多层 text-shadow 等效描边**、**字重与留白拉开的层级**。唯一豁免是**角标级信息**（左上台标那种量级）；豁免要在 CSS 里显式写 `/* lint-allow-panel: 理由 */`，不许默默加。机器门：`tools/kuleshov-lint.py` ④。
- **带标点的字幕。**（2026-07-27 用户拍板）专业视频的字幕从不加标点符号。句末标点删除，句中停顿用全角空格。**切分仍然用标点**（它是断句依据），但输出层必须剥干净——外挂 VTT 同样适用。机器门：`tools/kuleshov-lint.py` ⑤⑦。
- **用转场遮掩剪辑。** 来源切换不必自动加特效；全片转场词汇保持克制且有语义。
- **可以随意换题的模板味。** 如果替换产品名或选题后整条片仍然成立，说明导演工作还没做够。
- **未经缝合的 AI 塑料感。** 多源素材必须通过 LUT、颗粒、构图和节奏建立同一世界。
- **无意图的运镜。** 每个运动都要能回答“它让观众看见或感受到什么”。

### 牺牲顺序

- 宁可短，不可水；内容装不下就砍，不用空话填时长。
- 宁可降低一档信息密度，也要保住节奏与呼吸。
- 宁可重做一个镜头，也不放过角色变脸、文字碎裂与关键动作失败。
- 宁可 TTS 平实克制，也不要过火的表演腔。
