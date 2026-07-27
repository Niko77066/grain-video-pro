# Grain Video Pro

**把 AI 编程 agent 变成一支真正的视频制作团队。**

给它一个选题或 brief，它会完成调研、脚本、配音、分镜、素材生成与检索、剪辑合成、成片质检，最后交付一条可发布的视频。整个过程由结构化 Film IR 驱动：每个镜头有意图，每次生成可追溯，每次降级必须显式，每条成片都要过机器硬门与独立评委。

**Brief in. Reviewed film out.**

Grain Video Pro 不是“输入一句 prompt，拼几张图配个音”的短视频生成器。它把一支成熟制作团队的工作方法——制片、研究、编剧、导演、剪辑、质检——编码成 agent 可执行、可复跑、可审计的生产系统。

> **当前状态**：Kuleshov 制作内核已经独立跑通并交付多条样片；当前正在收敛为 Grain 原生的 Video step-skill。现有仓库可由 Codex、Claude Code 或团队自研 harness 驱动，Grain 集成边界见 [`docs/grain-delivery-plan.md`](docs/grain-delivery-plan.md)。

## 一条完整生产线，而不是一串 API

```text
brief → research → script → hero frames → audio → storyboard
      → assets & motion → compose → review → deliver
```

每个阶段都有明确产物、进入条件和失败后的定点回炉路径。agent 不靠对话记忆猜“做到哪了”，也不能用一段自我解释绕过质量问题。

### 这套系统真正解决什么

- **把创意变成可执行的镜头计划**：先做 research 与 script，再用真实音频时间轴驱动分镜，避免“按字数估时”和音画错位。
- **让多种素材成为同一种导演语言**：MG 动画、AI 视频、数字人、图片动效、实拍与检索素材按镜头意图平权路由，而不是全片套一种低成本模板。
- **让品味可以复用，也可以进化**：风格包同时包含叙事 playbook、机器可读合同和 Golden 样片基准；新经验回写系统，不只留在某次对话里。
- **在花钱前拦错，在交付前验片**：storyboard 预检、hero-frame 品味门、镜头级 QC、终渲反测和隔离评委组成两层质量体系。
- **让每条片可追溯、可复跑**：prompt、模型、seed、参考资产、成本、耗时、路由与降级决策全部进入 ledger。
- **不绑定某一家 agent 或 provider**：知识、契约和 CLI 构成稳定内核；宿主负责主循环与工具调用，provider 可以替换，生产纪律不变。

## 核心设计

### Film IR：一条片的唯一真相源

每个项目以 `projects/<slug>/film.json` 描述全片：元数据、音频时间轴、锚点、镜头、叠加层、剪辑规则、成本和质量门结果都在同一份 IR 中。所有合法修改通过 `kuleshov-ir` 完成，并带乐观锁与自动留痕。

```bash
kuleshov-ir read projects/<slug> shots
kuleshov-ir patch projects/<slug> --op '{"op":"set","path":"shots[s03].status","value":"redo"}'
kuleshov-ir validate projects/<slug>
kuleshov-ir execute projects/<slug> shots.s03 --dry-run
```

### Style Contract：把“像这种感觉”编译成约束

风格包不是配色预设，而是完整的导演协议：什么题材适配、哪些视觉声部必须出现、真运动占比、静态镜头上限、转场词汇与不可违条款。当前提供：

| 风格包 | 擅长内容 | 画幅 |
|---|---|---|
| `pixel-chronicle` | 知识科普、历史叙事、像素纸拼贴 | 16:9 |
| `case-file` | 新闻调查、隐私与安全议题、案卷拼贴 | 9:16 |
| `whiteboard-generalist` | 超出专用风格覆盖时的通用叙事 | 自适应 |

合同在 storyboard 阶段做计划预检，在 review 阶段用终渲实测数据复验。agent 可以在预先授权的带宽内调整，但不能改合同给自己放行。

### G1 + G2：代码验事实，评委验观感

- **G1 硬门**验证 IR 一致性、时间轴、风格合同、字体、黑帧、冻结、响度与终渲指标。
- **G2 隔离评委**只看证据包和 Golden 对照，不读取创作者的解释；扣分必须落到具体镜头或时间码。

失败不会触发整片重来，而是回到责任阶段做单镜或单环节手术。达到止损上限仍不过的片会带 `DEBT` 或 `contract_violation` 停在 review，不能伪装成 delivered。

## 开始使用

### 1. 准备运行环境

```bash
python3.12 -m venv film-ir/.venv
film-ir/.venv/bin/pip install -e film-ir
film-ir/.venv/bin/pip install -r tools/requirements.txt
film-ir/.venv/bin/pip install pytest
```

还需要 `ffmpeg` / `ffprobe`、Node.js / `npx` 和 Git。生成、检索、TTS 与渲染凭据参考 [`.env.example`](.env.example)；由宿主 harness 运行时，凭据应由宿主工具注入。

### 2. 让 agent 开拍

在 Codex 或 Claude Code 中打开本仓库，直接描述任务：

```text
用 pixel-chronicle 做一条 3 分钟的知识科普视频：
为什么英国和阿根廷隔着一片海，却总像宿敌？
```

agent 会读取 [`.claude/skills/produce/SKILL.md`](.claude/skills/produce/SKILL.md)，创建 `projects/<slug>/`，并按十阶段管线推进。已有项目则从 `film.json` 的真实状态续跑。

### 3. 验证内核

```bash
film-ir/.venv/bin/python -m pytest film-ir/tests
bash tools/preflight.sh projects/<slug>
```

## 仓库地图

| 路径 | 作用 |
|---|---|
| `.claude/skills/produce/` | 十阶段生产 SOP 与按来源加载的导演知识包 |
| `film-ir/` | Film IR 模型、CLI、执行适配器与 G1 门套件 |
| `styles/` | 风格 playbook、机器合同、Golden 基准与进化规程 |
| `tools/judge/` | G2 证据包、隔离评审与校准工具 |
| `tools/measure-render.py` | 从终渲视频反测静态持有、媒体使用、响度、跨镜头主色漂移等指标 |
| `projects/` | 已交付样片、生产中的项目与项目模板 |
| `docs/` | 架构、复盘、升级计划与 Grain 集成方案 |

## 宿主如何接入

Grain Video Pro 的边界刻意保持清晰：

1. 宿主读取生产 skill，负责主循环、并发与任务调度；
2. `kuleshov-ir` 负责状态、合法写入、验证与执行计划；
3. 宿主的 provider 工具执行出图、视频、TTS、检索与渲染；
4. 终渲进入 G1 实测与 G2 隔离评审，全部通过后才能交付。

这意味着 Codex、Claude Code 或 Grain 可以共享同一套制作知识与质量契约，而不需要共享同一套编排实现。详细接口与迁移路线见 [`docs/grain-delivery-plan.md`](docs/grain-delivery-plan.md) 和 [`docs/film-ir-context-architecture.md`](docs/film-ir-context-architecture.md)。

## 当前边界

- `meme-ledger` 尚未完成，位于 `styles/_disabled/`，不会参与自动选型。
- `projects/*` 是样片与校准资产，不是可复用管线本身；个别早期项目保留了只用于复盘的脚本。
- Grain 原生工具映射、发布三件套与 provider 凭据托管仍在集成阶段；当前仓库不把“规划完成”写成“产品已上线”。

---

**Kuleshov** 是这套系统的制作内核代号，名字来自“意义产生于镜头并置”的库里肖夫效应。Grain Video Pro 要做的不是生成更多镜头，而是让 agent 知道为什么拍、该用什么拍，以及什么时候这条片还不能交付。
