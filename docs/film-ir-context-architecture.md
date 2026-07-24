# Film IR 文件系统 · 导演—子导演上下文架构 · Film IR API（M1 工程化设计）

> 回应 2026-07-15 架构评审反馈第 2 点。依据：设计蓝图 v3.4（§2/§4/§8/§10）、M0 三条片的实测形态（`projects/800v-thermal-runaway` 等）、Anthropic 多 agent 工程原则。
> 状态：**设计稿**——凡与 M0 实测冲突处，以实测回填修订。

---

## 1. Film IR 文件系统：一片一目录，一份真相源

### 1.1 编译器类比（为什么叫 IR）

创意与剧本是源代码，成片 mp4 是机器码。brief→blueprint→script→storyboard 各阶段是**前端**（把模糊创意逐步编译进 IR）；门禁、QC、评委、定点重做是**优化器**（全部作用在 IR 上，不作用在像素上——像素贵且不可编辑，IR 便宜且可手术）；compose 与各 provider adapter 是**后端**（把 IR 翻译成 HyperFrames composition、Seedance API 调用、FFmpeg 滤镜图）。**一个 IR，多个后端——换引擎不动上游。**

阶段 artifact（script.md、research.md）是"提交"，`film.json` 是"仓库"。

### 1.2 目录布局与读写权属

```
projects/<片名>/
├── film.json      # 全片唯一真相源（结构见 1.3）
├── brief.md       # ① 写入后只读
├── research.md    # ② 事实底座，编号 F01…，script 回链
├── script.md      # ③ 评委门后锁定
├── audio/         # ④ voiceover.wav + timeline.json（全局时钟）
├── anchors/       # ⑥ 锚点图（角色表/风格帧/关键帧），参数记入 film.json.anchors[]
├── shots/         # ⑦ 烘焙 clip（Seedance/数字人产出），文件名 = shot_group id
├── compose/       # ⑧ HyperFrames composition 源码（声明型镜头活在这里）
├── out/           # 成片 + 交付包
└── review.md      # ⑨ 自审证据（ffprobe/回转写/承诺复验）
```

权属规则：**每个文件恰好有一个 owner 阶段**；上游 artifact 一旦过门即锁定，下游只读。改上游 = 正式修订（send-back ≤ 1 次，记 `ledger.decisions`），不存在"顺手改一下剧本"。

### 1.3 film.json 结构与分区

```
film.json
├── meta          # 片名、片型、风格包@版本、交付承诺、宽高比、状态       [owner: brief/EP]
├── audio         # voiceover / music / timeline（逐词时间戳）          [owner: audio]
├── anchors[]     # 锚点：id、类型、文件、生成参数、一致性备注            [owner: anchors]
├── shot_groups[] # Seedance 调度单元（≤15s、≤5 镜）+ 接缝契约          [owner: storyboard]
├── shots[]       # 镜头：t/intent/source/anchor_refs/status/gen/qc     [规划: storyboard；回填: motion]
├── overlays[]    # 全片叠加层（引擎无关声明）                          [owner: storyboard/compose]
├── edit          # 转场词汇(≤4)、LUT、颗粒、响度、闪避                  [owner: 风格包预填 + compose]
└── ledger        # decisions[] / costs[] / gates[]  —— append-only    [owner: 全体，只增不改]
```

三条设计规则（已在执行）：**① 一切引用靠 ID**（镜头引锚点、叠加层引镜头，禁止路径散落）；**② 生成参数全记录**（模型/seed/完整 prompt/参考/成本/墙钟，任何资产可复现）；**③ IR 引擎无关**（compose 才翻译成具体引擎方言）。

分区的工程意义：`shots[]` 天然按镜头分区——motion 并行 fan-out 时每个子导演只写自己那几条，冲突面极小；`ledger` 是唯一多写者共享区，所以它必须 append-only。

---

## 2. 全链路：谁在哪个阶段、拿什么上下文、写哪里

### 2.1 十阶段与三处全局屏障

```
brief → research → blueprint+script → audio → storyboard → anchors → motion → compose → review → deliver
                        ▲屏障1           ▲屏障2      ▲屏障3        ├─ 可并行 fan-out ─┤   ▲收敛屏障
```

**屏障 = 必须单 agent 持全局上下文、禁止拆分的环节**（Anthropic MARS 原则：强全局依赖任务禁止拆分）：

1. **script 定稿**——audio 依赖完整文本；
2. **audio.timeline 定稿**——全局时钟，此后一切视觉时长以它为准；
3. **storyboard 定稿**——节奏与编排是全局属性，拆给多个 agent 会互相打架（每 8–10s 视觉变化、声部交替、剪辑密度曲线都是跨镜头约束）。

屏障之间按**逐镜头 DAG** 流水线化：镜头 1 锚点过门立即发起镜头 1 的 motion，不等镜头 8；compose 是唯一收敛屏障（也必须单 agent——它是全片时间轴的唯一持有者）。

### 2.2 席位与上下文配给表（M1 目标形态）

导演不是一个进程：**意志在知识层**（品味宪法+风格包），**眼睛在评委**（G2，M0 由用户代行），**手在 EP**。EP 是执行制片人，阶段工种是部门负责人。M0 一切席位都由主循环兼任；M1 只把三类席位 subagent 化——**评委（需要上下文隔离）、motion（需要并行广度）、anchors（可并行）**。15× token 只花在广度环节，其余席位留在主循环。

| 席位 | 运行形态 | 注入（spawn 时写死在初始上下文） | 按需读（自己拉） | 写权限 | 回传 EP |
|---|---|---|---|---|---|
| **EP 主循环** | 主 agent | produce SOP、品味宪法、风格包档案+声部表 | film.json 全量（唯一全局视野） | meta.status、ledger.decisions | ——（面向用户汇报） |
| research | M1 仍在主循环 | 任务卡：选题+事实需求 | WebSearch/素材 | research.md | 事实清单 |
| script/storyboard | **主循环内联（屏障）** | 风格包：宣言+节奏+声部表+翻译表引用行 | audio/timeline.json | script.md、shots[]、shot_groups[] | —— |
| anchors 子导演 | subagent，可并行 | 任务卡 + `image-motion.md` + 风格包视觉系统 | 自己的 anchors[] 条目 | anchors/、anchors[] | 锚点清单+一致性备注 |
| motion 子导演 | **subagent × 每镜头组** | 任务卡四要素：本组镜头规格（IR 切片逐字复制）+ 锚点文件路径 + `seedance.md` + 风格包 Seedance 方言行 + 边界（不许改剧本/分镜/路由）+ 资源档位（重试 ≤2） | `ir read shots[own_group]` | shots[own].gen/qc、shots/ 下本组文件 | ≤2000 token：状态+QC 摘要+异常 |
| compose | **主循环内联（收敛屏障）** | `hyperframes.md` + 风格包视觉系统/版式模板 + edit 契约 | film.json 全量 | compose/、edit、out/ | —— |
| G2 评委 | **subagent，物理隔离** | rubric + 风格包 rubric 附录 + 2–3 条带人工分的锚片 | 证据包（artifact + 采样帧 + L0 报告），**看不到创作过程** | ledger.gates | 分数+必须引用镜头 ID/时间码 |

四条纪律（全部来自蓝图 §10 / Anthropic 原则，M1 照此执行）：

1. **传 ID 不传本体**：席位间传 shot_id 和文件路径，不把内容贴进对话——防"传话游戏"失真，也是上下文经济的根基。
2. **任务卡四要素**：目标 / 输出格式（artifact Schema）/ 工具白名单 / 边界与资源档位。motion 子导演的任务卡里没有剧本全文——它不需要，也不许改。
3. **锁定后拿干净上下文进场**：blueprint/storyboard 是 plan artifact，过门即锁；下游子导演开新上下文只带 spec，避免"边执行边改主意"。
4. **评委与创作者不同 agent、不共享上下文**：评委只看产物与契约，评分必须引用具体位置，引用缺失判无效——防"自己审自己"的系统性放水（LLM 自评准确率实测仅 ~46%）。

### 2.3 M0 → M1 的迁移量

M0 已经在按这张表的"内联版"运行（produce SOP 就是 EP 的注入知识；风格包先行；状态从 film.json 读）。M1 增量只有三件：① motion/anchors 的 subagent 化 + 任务卡模板；② G2 评委席位（先上 storyboard/成片两个点）；③ 下节的 IR API。**不新增阶段、不改 film.json 结构**——这是把已验证实践工程化，不是造新系统。

---

## 3. Film IR API：必要性论证与工程化注意点

### 3.1 为什么 M0 不需要、M1 必须有

M0 单写者（一个主循环）+ 人在环，"约定 + 自觉"够用——API 在 M0 是过度工程，所以蓝图把"IR 工具化"排在 M1（pull-based：有触发条件才建）。**M1 的四个触发条件同时到达：**

1. **多写者并发出现了。** motion fan-out 后，N 个子导演同时回填 `shots[].gen/qc` + 追加 ledger。整文件"读-改-写"必然互相覆盖（lost update）——这不是假设，是并行的定义。
2. **Rule Zero 从自觉变强制。** "先写 IR 再花钱"在 M0 靠提示词（advisory）；M1 要求生成动作查不到 shot_id 就拒绝执行（guarantee）。没有程序化的查询/校验层，这条铁律无处落地。
3. **承诺字段不可静默修改。** 片型承诺、时长承诺、预算是 G1 门控字段，改它必须走正式修订并留痕。提示词拦不住模型顺手改 JSON，写入层拦得住。
4. **上下文经济。** 3 分钟片的 film.json 预计 2000+ 行；motion 子导演只需要自己那 3–5 镜。没有 selector 读取，每个子导演都得吞全文——token 浪费 × 注意力稀释双输。

**M1 明确不做的**（每个都有触发条件，没到不建）：DAG 执行引擎（第一次有人在等片时再建）、MCP server 形态、数据库。文件 + CLI 够用。

### 3.2 API 面：四个正交动词

不做"每种改法一个工具"——工具语义爆炸且新片型要新工具。只有四个动词（实现为 `tools/ir` CLI，agent 经 Bash 调用）：

```bash
ir read  <片名> <selector>          # shots[s07] | shots[status=qc_fail] | meta | audio.timeline
ir patch <片名> --actor <席位> <ops>  # JSON-Patch 子集 + 语义宏（set-status / fill-gen / add-decision）
ir validate <片名> [--stage storyboard]  # Schema 全量 + 阶段特定校验器 == G1 硬门执行体
ir execute <片名> --shots s05,s07 --dry-run  # M1 版：只算受影响集（该重生成的组/该增量重渲的区间）
```

选 CLI 不选 MCP server 的理由：调用天然进 transcript（留痕免费）、hook 可拦、无常驻进程、子导演的 Bash 白名单就能约束权限。

### 3.3 工程化注意点（按踩坑概率排序）

1. **写入口唯一化，用 hook 保证。** PreToolUse hook 拦截 Edit/Write 对 `film.json` 的直接写入——"提示词是 advisory，hook 才是 guarantee"。没有这条，API 只是又一个可以绕过的建议。
2. **校验在写入层，不在调用方。** 每次 `ir patch`：Schema 校验 → 门控字段检查（改 `meta.commitment` 类字段必须带 `--revision` + 决策理由，否则拒绝）→ 写入 → 自动 append 一条 ledger（actor/ts/op 摘要）。校验器与 G1 硬门**共用同一份代码**——storyboard 八项自查里可判定的（区间无缝隙、组时长算术、连续同版式 ≤2）逐步从 SOP 文本编译进 `ir validate --stage`，这正是"知识三形态"里编译形态的落地路径。
3. **并发控制：分区 + 乐观锁 + append-only。** 顶层 `_version` 字段乐观锁 + flock 文件锁足够（都是本机进程）；shots 按镜头天然分区，冲突面小；ledger 只允许 append。写冲突返回可行动错误："version 14 已被 motion:s05g2 更新为 15，请 `ir read` 后重试"。**禁止**上分布式锁/数据库——单机文件系统，别造飞机。
4. **actor 署名进任务卡。** 子导演 spawn 时任务卡带 `--actor motion:s05g2`；每条 patch/ledger 记 actor。归因（`/video-triage`）需要回答"这个字段谁改的、为什么"。
5. **错误信息当新员工文档写。** "镜头 s99 不存在。当前 shots: s01_hook…s16_cta（16 条）；你的任务卡分配的是 s05–s07。"——可行动错误让子导演自愈，省一轮 EP 仲裁。
6. **Schema 从实测反推，不凭空设计。** `schema/film.schema.json` 以现有三个项目的 film.json 为准反推 + 收紧，M0 项目必须能过 `ir validate`（允许 `--legacy` 豁免清单）。Schema 进 git，`pipeline_version` 记（skills+schema+校验器）的 git SHA——版本间质量对比是 diff，不是回忆。
7. **`ir execute` 保持薄。** M1 只做"标记 + 受影响集计算"（dry-run 报告：重做 s05 → 触及 group g2 → compose 区间 [12.4, 27.9] 增量重渲），真正调 Seedance 仍由 motion 子导演按知识包执行。把执行塞进 API = 提前造 DAG 引擎，违反 pull-based。
8. **回传纪律写进任务卡模板。** 子导演回传 ≤2000 token 摘要 + artifact 路径；EP 永不读子导演的完整过程。摘要格式固定（状态/QC/成本/异常/DEBT），方便 EP 机械化汇总。
9. **逃生舱。** 一镜到底 morph、非线性拼贴这类 schema 表达不了的，允许以不透明 blob 镜头入 IR（只带 QC 契约不带结构语义）——IR 表达力天花板不该变成品味天花板，但每次使用记 DEBT 复审。

---

## 4. 风格包：定义、为什么不是 skill、注入机制

### 4.1 定义

风格包 = **版本化的品味数据资产（SKU）**，一个目录（现行实例：`styles/engineering-anatomy/`），七件套：

| 组件 | 形态 | 消费方 |
|---|---|---|
| 档案 + 风格宣言（爱/恨清单） | 文本 | EP、storyboard、G2 评委 |
| 开拍提问模板（elicitation schema） | 结构化问题清单 | EP（开拍时执行） |
| 视觉系统（CSS tokens、LUT、版式模板） | **代码/数据，不是提示词** | compose（直接进 composition 源码） |
| 节奏与剪辑（翻译表行引用 + 覆写） | 文本 + 表 | storyboard、compose |
| 声部表（来源 × 叙事角色） | 表 | storyboard（路由校验依据） |
| 反模式黑名单（一票否决项） | 表 | G2 评委逐条核对、创作侧自查 |
| golden 样片 + 考片记录 | 文件引用 + 分数 | 准入/下架裁决、评委锚片 |

### 4.2 为什么不做成 skill

skill 与风格包的分界：**skill 是行为（怎么干活的流程，跨风格共享），风格包是参数（这次穿哪套手艺）**。`produce` 是引擎，风格包是配置。做成 skill 有四个具体的坏处：

1. **触发机制不对。** skill 靠 description 匹配按需激活（检索形态，依赖模型注意力）；风格包必须**整体、无损、强制**地进入相关席位的上下文——品味不能靠模型"想起来去读"。
2. **一半内容不是提示词。** CSS tokens、LUT 文件、elicitation schema、golden 样片是代码和数据，塞进 skill 正文只能被"读一遍"，进不了 composition 源码和 ffmpeg 参数。
3. **治理模型不对。** 风格包有考片制准入（3–5 条样片盲评赢基线才进库）、有下架复审（L5 数据走低）、有版本（`style_pack@sha` 记进每片 meta）——这是资产库存管理，不是技能管理。
4. **数量模型不对。** LibTV 每导演一个 skill 是"多导演商场"产品形态；我们是**单导演多风格包**——风格包会长到十几个，做成 skill 会稀释整个技能库的注意力（技能库总量预算 ~30 份是硬纪律）。

### 4.3 注入机制：评审问题的准确答案

> 问："EP 导演拿到风格包确认后，spawn subagent 时直接在上下文里写入风格包相应的系统提示词指导 subagent 操作吗？"

**方向对，三处修正：**

1. **按席位裁剪切片，不整包平铺。** storyboard 席位拿宣言+节奏+声部表+翻译表引用行；motion 子导演只拿 Seedance 方言行 + 本组镜头相关的锚点引用；compose 拿视觉系统+版式模板+edit 契约；G2 评委拿 rubric 附录+黑名单。全文平铺 = 上下文稀释（motion 子导演不需要知道封面版式），而且 3 分钟片的 fan-out 会把同一份全文复制十几遍。
2. **能编译的不注入。** 知识三形态的铁律——每条内容先问能不能编译：CSS tokens 直接写进 composition、LUT 直接进渲染参数、elicitation 是开拍时跑的问卷、黑名单里可判定项（"火焰镜头连续 ≥3"）进 `ir validate` 校验器。**只有必须影响模型判断的品味正文才走注入**（推送进初始上下文，不是"请你去读"）；长尾参照（golden 样片）留检索。
3. **切片逐字注入 + 记版本。** EP 不许转述/概括风格包内容（概括必走样）——切片以原文块进任务卡；`meta.style_pack` 记 `engineering-anatomy@<git-sha>`，归因时能回答"这片用的是哪一版品味"。

机制细节：Claude Code 的 subagent 由 agent 定义给 system prompt，任务内容进首条消息——所以"写入上下文"的落点是**任务卡（首条消息）的固定段落**，效果与 system prompt 注入等同，且便于逐片替换。评委席位拿同一份 rubric 附录是**双向使用**的关键：创作侧某次没贯彻，评委按同一标准拦下——风格包因此从"建议"升级为"闭环约束"。

---

## 5. 落地顺序（M1 内）

1. `schema/film.schema.json`（从三个 M0 项目反推）+ `ir read/validate`——半天，立刻消灭"子导演吞全文"；
2. `ir patch`（乐观锁 + ledger 自动 append + 门控字段拒改）+ film.json 直写拦截 hook——半天；
3. motion/anchors 任务卡模板（四要素 + 风格包切片位 + actor）——与首条 3 分钟片的生产同步验证；
4. G2 评委席位（storyboard、成片两个点先行），rubric 引用风格包附录——评委分与用户人工分并行记录，先校准后放权；
5. `ir execute --dry-run` 受影响集计算——等第一次定点重做需求出现再写（pull-based）。
