# HyperFrames Agent 使用说明书

> 面向 AI Agent 的 HyperFrames 理解、创作、检查、渲染与交付手册  
> 资料基线：2026-07-28；HyperFrames `0.7.77`（npm 发布于 2026-07-28T02:18Z）；主仓库提交 `3c857d768b2eeb6ee97d4cad5d27119b8efa23eb`（`chore: release v0.7.77`）；launch 仓库提交 `f487ef4bddd0736d9103822bb575a4680078f039`（自上一版未变，仍是 16 个项目）。  
> 上一版基线为 2026-07-23 / `0.7.68`。两版之间的合同级变化集中列在 **0.3 节**，其中两条是**反向变更**（旧手册写反了的规则），请优先读。

## 导航

章号与正文小节号一致。

- **§0 使用方法与来源优先级** —— 含 **0.3「`0.7.68 → 0.7.77` 变更摘要」，两条反向变更在此**
- §1 核心心智模型
- §2 环境、安装和版本纪律
- §3 Agent 工作流路由
- §4 项目状态与生产制品
- §5 Composition 技术合同（5.7 媒体、**5.9 调色与 media treatment**）
- §6 动画、确定性与多运行时
- §7 Registry 与 Catalog 能力地图
- §8 Studio、CLI 与标准开发循环（**8.2 check 判定语义与 motion sidecar**）
- §9 七阶段生产管线
- §10 本地、Docker、Cloud、Lambda 与 Cloud Run 渲染
- §11 CLI 命令速查
- §12 包与编程接口
- §13 16 个真实 launch 项目地图 + 13.2 Few-shot 效果配方库
- §14 常见故障与排查顺序
- §15 Agent 执行清单
- §16 推荐提示词模板
- §17 主要资料入口
- §18 时效性说明

## 0. 这份手册怎样使用

本手册不是网页的逐段翻译，而是给 Agent 执行任务时使用的操作合同。它综合了：

- HyperFrames 官网文档、Catalog、Packages、SDK 与部署文档；
- 当前 HyperFrames skills 中比普通网页更严格的 composition 合同；
- `heygen-com/hyperframes-launches` 中 16 个真实发布视频项目、835 个文件及其 storyboard、design、handoff 和源码；
- 当前 `0.7.77` 的 changelog、weekly updates 与实际实现（npm 包实测 diff、CLI `--help`、`media-treatment --capabilities`、`catalog --json`）。

### 0.1 来源优先级

遇到冲突时，Agent 必须按以下顺序裁决：

1. 当前项目里已安装、与项目 CLI 版本匹配的 `/hyperframes`、`/hyperframes-core`、`/hyperframes-cli` 等技能合同；
2. 当前版本的 `npx hyperframes lint` / `check` / `doctor` 实际结果；
3. 官网当前 Concepts、Guides、Reference 与 Packages 文档；
4. `hyperframes-launches` 的历史项目源码与 handoff；
5. 通用 Web/GSAP 经验。

原因：launch 项目是宝贵的生产模式库，但部分项目由旧 CLI 版本制作，可能保留已淘汰写法；官网个别旧页面也仍有诸如“用空 tween 延长时长”的过时描述。新项目应以当前技能合同为准。

`0.7.77` 实测到一个具体例子：官网 `guides/color-grading` 页面仍只描述 `adjust / details / effects / lut`，而运行时与 CLI 能力目录已经支持 `wheels / curves / hueCurves / secondaries`。这类冲突按上面的顺序裁决——`npx hyperframes media-treatment --capabilities --json` 的输出胜过网页。

### 0.2 Agent 的总原则

- HyperFrames 是“HTML 作为视频源文件”，不是把网页录屏。
- HTML 声明内容、时间和轨道；CSS 决定静态布局与外观；seek-safe 动画运行时决定任意时间点的视觉状态；HyperFrames 负责媒体播放、clip 生命周期、逐帧 seek、截图和编码。
- 先把静态终态做正确，再加动画。
- 先 `lint` 快速迭代，最终必须 `check`，有子 composition 必须抽取中点 `snapshot` 并肉眼检查。
- `check` 通过不等于可以直接渲染。最终 Studio preview 必须由用户明确批准后才能 render。
- 历史 launch 项目可学习叙事、节奏、音画关系和架构，不应无脑复制其旧语法。

### 0.3 `0.7.68 → 0.7.77` 变更摘要

#### 两条反向变更（旧手册写反了）

**A. 媒体不再要求“必须是 composition 根的直接子节点”。**

`<video>` / `<audio>` 现在可以放在**任意嵌套深度**，包括 `compositions/*.html` 的 `<template>` 内部或一个 wrapper `<div>` 里。运行时用一次扁平的 `document.querySelectorAll("video, audio")` 发现媒体，用 `element.closest("[data-composition-id]")` 解析它归属哪个 composition，再按所有祖先 composition 累计的绝对起点重算它的 `data-start`。所以**场景专属的片段可以带着场景内局部时间住在自己的子 composition 里**，seek 和解码都正确。

配套证据：`0.7.68` 的 lint 规则 `media_in_subcomposition` 在 `0.7.77` 中**已被删除**；`hyperframes-cli` 技能里那段 “`grep -nE '<(video|audio)\b' compositions/*.html` 期望零命中” 的手工检查也已删除。

仍然成立的媒体约束（不要一起放宽）：不要把媒体塞进**带时间的 wrapper**（时间写在媒体元素本身，或让 wrapper 不计时）；不要 tween 媒体的布局尺寸；video 仍需 `muted playsinline` 且声音走独立 `<audio>`。

**B. `repeat: -1` 从硬错误降级为“有条件允许”。**

`gsap_infinite_repeat` 规则现在读根元素的 `data-duration`：

- 根显式声明了有限 `data-duration` → severity 降为 **warning**，提示语是“composition 声明了有限的 Ns 窗口，HyperFrames 会把确定性 seek 与导出裁到这个显式时长”；
- 根没有有限 `data-duration` → 仍是 **error**，理由是 timeline 可能报告无界时长、让渲染排程失败。

但注意来源优先级：`hyperframes-core` 的 `determinism-rules.md` **仍然**把 `repeat: -1` 列在“禁止”里，并要求算有限次数 `Math.max(0, Math.floor(duration / cycleDuration) - 1)`（必须 `floor`，`ceil` 会触发 `gsap_repeat_ceil_overshoot`）。因此当前正确的做法是：**默认仍写有限次数**；只有在确实需要无限循环装饰、且根 `data-duration` 显式有限时，才接受这条 warning，并在交付说明里写清楚。

#### 新增能力

| 版本 | 内容 |
|---|---|
| 0.7.69 | layout 审计新增旋转轴心漂移检测（`rotation_pivot_drift`）；SDK 编辑文本时保留可编辑 `<br>`；字体/probe/worker 内存处理加固 |
| 0.7.70 | 多 worker 实验性快速捕获会自检帧，发现损坏自动回退截图捕获 |
| 0.7.71 | **有限 composition 允许 `repeat: -1`**（需显式根 `data-duration`）；定义媒体处理（media treatment）能力；预览可服务外部 symlink 资产；字幕模板改为运行时数据驱动 |
| 0.7.72 | **Plan v2**：带版本、内容寻址、完整性校验的分布式渲染契约；Studio 新增 keyframe ease 编辑器与 media treatment 检查器；**CLI 新增 agent-first 媒体处理工具**；新增 layout 检查 `off_pivot_rotation`；确定性 keyframe ease 运行时 |
| 0.7.73 | **专业调色落地**：Studio 调色控件、CLI agent-native 调色；Plan v2 publisher 直接把产物流式写入 S3 / GCS；帧覆盖率统计对齐 FFmpeg CFR 取整 |
| 0.7.74 | Plan v2 处理抽取缓存哨兵与部分色彩元数据；GCP 捕获遵循有效 `BeginFrame` 边界；冷启动保留 GSAP live volume 状态 |
| 0.7.75 | 分布式捕获先探测 `BeginFrame` 支持，不支持时安全回退截图；定向重试只恢复 `BeginFrame` 专属失败 |
| 0.7.76 | Plan v2 分片物化会为稀疏分片重建视频目录骨架；改进细长元素的旋转轴心漂移检测与断连连接线诊断 |
| 0.7.77 | Studio 时间线新增可展开属性轨道、轨道头、精确 keyframe 重定时、嵌套 composition 支持；layout 检查新增可选 `proseCoverageFloor` 规则；Windows 下 CLI 下载清理修复 |

#### 命令面变化

- 新增顶层命令 **`media-treatment`**（见 5.9）。这是 `0.7.68 → 0.7.77` 唯一新增的顶层命令，命令总数 47 → 48。
- 新增 lint / check 规则：`off_pivot_rotation`、`rotation_pivot_drift`、`repeated_id_descendant_selector`、`missing_gsap_plugin`。
- 删除规则：`media_in_subcomposition`（见变更 A）。
- `grade-compare` 的 `grades.json` 结构改了：调色字段现在必须包在 `adjust` 里。

```json
// 旧（0.7.68 文档）
[{ "label": "warm", "grading": { "temperature": 0.2, "contrast": 0.1 } }]
// 新（0.7.77）
[{ "label": "warm", "grading": { "adjust": { "temperature": 0.2, "contrast": 0.1 } } }]
```

- `data-color-grading` 从「adjust / details / effects / lut」扩成完整调色台：新增 `wheels`（三路色轮）、`curves`（主通道 + RGB 分通道）、`hueCurves`（hue-vs-hue / sat / luma）、`secondaries`（最多 4 组 HSL 二级校色）。**并且其中 9 个值暴露为 CSS 变量，可以被注册过的 GSAP timeline 直接 tween 且保持 seek-safe**——这条改变了「reveal / 聚焦 / 去码」这类效果的正确做法。全部细节见 5.9。
- Catalog 实测 138 项（113 block + 25 component），新增 `media-treatment-overlay` 标签的 4 个块与 WebGPU Liquid Glass 家族；字幕 component 改为运行时数据驱动。
- `/hyperframes` 路由新增一条：**关于实拍素材观感的模糊反馈也路由到 `/media-use`**，哪怕用户从没说“调色”或“特效”——“太暗”“太平”“无聊”“帮我把这个 reveal 做酷一点”“把脸遮住”都算。编辑前先加载它的 media-treatment 政策，**不要**用自己临时写的 LUT、CSS filter、遮罩层或 opacity tween 去替代现成的规范化处理原语。

#### 保持不变（已复核）

Node 22+ 基线、`@tailwindcss/browser@4.2.4` 固定版本、脚手架模板的 `gsap@3.14.2`、`validate` / `inspect` / `layout` 仍是 `check` 的弃用别名、launch 仓库仍是 16 个项目（同一提交）。第 13 章的项目地图与 13.2 的配方库整体仍然有效，只有涉及“媒体必须直属 root”的两处按变更 A 修正。

---

## 1. HyperFrames 的核心心智模型

HyperFrames 把一个视频建模为一棵 HTML composition：

```text
index.html（顶层 composition / 总编排）
├── 可视 DOM clip（标题、卡片、图表、场景）
├── video / audio / img 媒体 clip
├── compositions/*.html 子 composition
└── 一个暂停、可 seek 的根时间线
```

渲染流程是：

```text
frame → time = frame / fps
      → 所有 adapter seek 到该时间
      → Chrome 生成确定的像素
      → 捕获帧
      → FFmpeg 编码并混音
```

它不是实时播放录制。渲染器可能前进、后退、随机访问或并行请求帧，因此每一帧都必须只由“输入 + 当前时间”决定。

### 1.1 HyperFrames 适合什么

- AI Agent 生成和修改视频：Agent 本来就擅长 HTML/CSS/JS；
- 产品发布、功能演示、品牌短片、解释视频、动态图形；
- 带字幕或图形包装的 talking-head；
- 数据驱动、变量驱动、批量个性化视频；
- 可在网页、Studio、CLI、Docker、HeyGen Cloud、AWS Lambda、Google Cloud Run 之间复用的确定性视频；
- 需要 Git diff、代码审查、自动化验证和 CI 的视频项目。

### 1.2 它与传统编辑器和 Remotion 的关键差异

- 源文件是普通 HTML，不要求 React/JSX，也没有专有二进制工程格式。
- 时间主要由 `data-*` 属性和 seekable timeline 表达。
- DOM、SVG、Canvas、WebGL、Lottie、Three.js、CSS、WAAPI 可共存。
- Studio 的时间线编辑最终回写 HTML 属性与样式，不产生隐藏工程状态。
- Remotion 源码迁移使用 `/remotion-to-hyperframes`，不要把普通新建任务误路由成迁移任务。

---

## 2. 环境、安装和版本纪律

### 2.1 基础依赖

- Node.js 22 或更高；
- npm 或 bun；
- 本地渲染需要 FFmpeg 与 FFprobe；
- Docker 可选，用于跨机器更一致的 Chrome、字体和 FFmpeg 环境；
- launch 仓库的二进制素材需要 Git LFS。

环境检查：

```bash
node --version
ffmpeg -version
npx hyperframes doctor
npx hyperframes doctor --json | jq -e '.ok' >/dev/null
```

注意：`doctor --json` 命令本身通常退出 0，CI 应检查 JSON 中的 `.ok`。

### 2.2 安装 Agent skills

推荐安装当前核心集合：

```bash
npx hyperframes skills update
```

其他方式：

```bash
# 交互挑选，直接取 main
npx skills add heygen-com/hyperframes --full-depth

# 安装全部工作流
npx skills add heygen-com/hyperframes --all --full-depth

# 安装一个技能
npx skills add heygen-com/hyperframes --skill hyperframes-animation --full-depth
```

更新与检查：

```bash
npx hyperframes skills check
npx hyperframes skills update
npx hyperframes skills update product-launch-video
```

### 2.3 项目 CLI 版本

脚手架项目通常在 `package.json` 中固定 HyperFrames 版本，以保证渲染可复现。恢复一个旧项目，在首次会影响渲染的操作前执行：

```bash
npx hyperframes@latest upgrade --project . --check
```

如果落后，再执行：

```bash
npx hyperframes@latest upgrade --project .
npx hyperframes check
```

升级后必须验证。若 `check` 失败，应把 pin 恢复到旧版本，说明继续使用的版本和原因。升级成功也应在交付摘要中写明旧、新版本；“检查通过”不代表新旧像素逐帧完全相同。

### 2.4 新建项目

```bash
npx hyperframes init my-video --non-interactive --example blank
cd my-video
```

常用例子：

| 示例 | 视觉倾向 | 适用 |
|---|---|---|
| `blank` | 纯脚手架 | 从零创作 |
| `warm-grain` | 温暖、颗粒、编辑感 | 生活方式、品牌 |
| `play-mode` | 弹性、高能 | 社媒、发布 |
| `swiss-grid` | 瑞士网格、结构化 | 企业、数据、技术 |
| `kinetic-type` | 动态大字 | Promo、片头 |
| `decision-tree` | 图解、流程 | 教程、解释 |
| `product-promo` | 多场景产品展示 | 产品演示 |
| `nyt-graph` | 新闻编辑式数据图 | 报告、数据故事 |
| `vignelli` | 竖屏、大胆排版 | 9:16 公告 |

可附带媒体：

```bash
npx hyperframes init my-video --example warm-grain --video ./intro.mp4
npx hyperframes init my-video --example blank --tailwind
```

Tailwind 脚手架使用固定的 `@tailwindcss/browser@4.2.4`、CSS-first 的 v4 语法和 `window.__tailwindReady`。不要换回不固定版本的 `cdn.tailwindcss.com`；离线或生产环境应预编译 CSS。

---

## 3. Agent 首先要做的路由

任何“创建、编辑、动画、预览、检查或渲染视频”的请求，先读 `/hyperframes`。已有项目的单一操作不重新做意图访谈；新建任务才确认 brief 并路由。

### 3.1 工作流选择表

按第一条匹配项选择：

| 输入或目标 | 工作流 |
|---|---|
| 明确迁移 Remotion 源码 | `/remotion-to-hyperframes` |
| 演示文稿、pitch deck、可导航交互 deck | `/slideshow` |
| 现有 talking-head 只加普通字幕 | `/embedded-captions` |
| 现有 talking-head / 采访 / 播客加设计化信息层 | `/talking-head-recut` |
| 音乐节拍驱动、无旁白 | `/music-to-video` |
| 通常 10 秒内、无旁白、motion 本身是信息 | `/motion-graphics` |
| GitHub PR / 代码变更解释 | `/pr-to-video` |
| 从网站或产品 URL 做发布、展示、site tour | `/product-launch-video` |
| 从文本、文章、笔记解释概念，且不用网站画面 | `/faceless-explainer` |
| 其他自定义视频 | `/general-video` |

容易混淆的情况：

- “短”不自动等于 motion graphics；静态标题卡、旁白片段或更长 montage 进 general video。
- 有音乐不等于 music-to-video；只有节拍网格真正驱动剪辑时才使用该工作流。
- 只加字幕与设计化 overlays 是两个不同工作流。
- “想要 storyboard”只改变评审流程，不自动改变内容工作流。
- 专用叙事工作流通常适合约 30–90 秒，最长约 3 分钟；明显更长的片子用 general video。

### 3.1.1 域技能路由：实拍素材观感归 `/media-use`（0.7.77 新增）

工作流拥有整条交付，域技能只被按需加载。`0.7.77` 在 `/hyperframes` 里加了一条明确路由：**只要用户在评价实拍素材的观感或表现方式，就先加载 `/media-use` 及其 media-treatment 政策**，哪怕他从没说过“调色”或“特效”这两个词。

触发词包括但不限于：太暗、太平、无聊、复古、想有隐私、“把这个 reveal 做酷一点”、“让画面贴合选题”。

硬性要求：**不要**用自己临时写的通用 LUT、CSS `filter`、叠加层或 opacity tween 去替代现成的规范化处理原语（见 5.9）。纯文字、纯排版、纯运动的改动仍留在各自的域技能里。

制作过程中如果片子里有重要的实拍素材，最终质检时要包含一次有依据的 media-polish 扫描——**扫完之后判断“不改”也是合法结论**。

### 3.2 新建任务需要锁定的 brief

Agent 至少要知道：

- 受众；
- 唯一核心信息；
- 输出类型；
- 时长；
- 画幅（16:9 / 9:16 / 1:1）；
- 风格与能量；
- 是否旁白、字幕、音乐、SFX；
- 必须使用或禁止使用的品牌、文案、素材；
- 审批方式：协作式逐阶段确认，还是授权范围内自动推进。

一旦生成 `BRIEF.md`，后续工作流以它为唯一意图来源，不反复重新路由。

---

## 4. 项目状态和制品

### 4.1 推荐目录

```text
my-video/
├── BRIEF.md
├── DESIGN.md
├── SCRIPT.md
├── STORYBOARD.md
├── capture/
│   ├── screenshots/
│   ├── assets/
│   ├── extracted/
│   └── AGENTS.md
├── assets/
├── compositions/
│   └── frames/
├── snapshots/
├── renders/
├── index.html
├── hyperframes.json
├── meta.json
└── package.json
```

### 4.2 每个文档的职责

- `BRIEF.md`：确认后的目标、受众、画幅、时长、风格、素材、约束和运行方式；
- `DESIGN.md` / `frame.md`：事实性的视觉系统，不是分镜；记录主题、色板、字体、组件、间距、允许与禁止；
- `SCRIPT.md`：锁定的旁白或逐 beat 屏幕文案；
- `STORYBOARD.md`：每一帧/场景的叙事角色、画面、资产、技术、过渡、音效与状态；
- `transcript.json`：词级时间戳，叙事视频节奏的真实来源；
- `HANDOFF.md`：保留已验证状态、未完成事项、关键偏好和不可回退的技术决定；
- `index.html`：总编排，不应变成所有场景的垃圾场；
- `compositions/*.html`：独立场景；
- `hyperframes.json`：registry、路径、媒体代理等配置。

### 4.3 Storyboard 状态

- `outline`：只有计划；
- `built`：HTML 与布局已确认，通常是 wireframe；
- `animated`：完整设计、素材和 motion 已落地。

复杂叙事片应先确认 plan，再确认 wireframe 布局，最后制作完整设计与动画。用户确认过的 wireframe 是布局合同：后续“build”是给它上设计和 motion，不应重新发明构图。

---

## 5. Composition 技术合同

### 5.1 最小可渲染结构

```html
<!doctype html>
<html lang="zh-CN">
  <head>
    <meta charset="UTF-8" />
    <meta name="viewport" content="width=1920, height=1080" />
    <script src="https://cdn.jsdelivr.net/npm/gsap@3.14.2/dist/gsap.min.js"></script>
    <style>
      html, body { margin: 0; width: 100%; height: 100%; }
      #root {
        position: relative;
        width: 1920px;
        height: 1080px;
        overflow: hidden;
        color: white;
      }
      #background { position: absolute; inset: 0; background: #0b0f14; }
      #title-card { position: absolute; inset: 0; display: grid; place-items: center; }
      #title { margin: 0; font-size: 96px; }
    </style>
  </head>
  <body>
    <div id="root"
         data-composition-id="main"
         data-start="0"
         data-width="1920"
         data-height="1080"
         data-duration="5">
      <div id="background"></div>
      <section id="title-card" class="clip"
               data-start="0" data-duration="5" data-track-index="1">
        <h1 id="title">Hello HyperFrames</h1>
      </section>
    </div>

    <script>
      window.__timelines = window.__timelines || {};
      const tl = gsap.timeline({ paused: true });
      tl.fromTo(
        "#title",
        { y: 48, opacity: 0 },
        { y: 0, opacity: 1, duration: 0.6, ease: "power3.out" },
        0.2
      );
      window.__timelines["main"] = tl;
    </script>
  </body>
</html>
```

关键点：

- 顶层 `index.html` 的 composition 根直接在 `<body>` 中，不能用 `<template>` 包住；
- 根必须是解析后的固定尺寸盒子，祖先高度也要成立；
- 推荐显式写根 `data-duration`，它是总渲染长度；
- 每个 composition 恰好注册一个同步创建、暂停的 timeline；
- timeline key 必须精确等于根的 `data-composition-id`；
- 全屏背景放在 full-bleed 子节点，不放在 composition 根本身，避免 producer 合成时出现“preview 正常、render 黑帧”的隐蔽问题。

### 5.2 根属性

| 属性 | 规则 |
|---|---|
| `data-composition-id` | 必需；与 `window.__timelines[id]` 一致 |
| `data-width` / `data-height` | 必需；常用 1920×1080、1080×1920、1080×1080 |
| `data-duration` | 强烈建议显式写；总 render 秒数，源 HTML 编译期固定 |
| `data-fps` | 可选提示；CLI `--fps` 可覆盖 |
| `data-composition-variables` | 变量声明 JSON 数组 |

根 duration 可在有有限 GSAP/CSS/WAAPI/Lottie 时省略并推断，但以下情况必须显式写：Three.js、无限/无法推断的 CSS/WAAPI、无 timeline 和无其他动画信号。新项目为了可读性和稳定性，默认显式写。

根 `data-duration` 与普通 clip 的 `data-duration` 不一样：根时长在编译期锁定，脚本或 `--variables` 后改无效；普通 clip 的时长可在初始化脚本后由 live DOM 重新读取。

### 5.3 Clip 属性与直接子节点规则

| 属性 | 规则 |
|---|---|
| `id` | 每个 clip 必须稳定且全 assembled page 唯一 |
| `data-start` | 绝对秒数，或同 composition 内相对引用 |
| `data-duration` | `div`、`img`、子 composition host 必需；video/audio 可用素材固有时长 |
| `data-track-index` | 必需；同一轨道不能时间重叠 |
| `class="clip"` | 可视 DOM clip 必需；video 不加，audio 没有可见性也不加 |
| `data-hidden` | Studio 眼睛图标使用；预览与渲染都隐藏，非破坏性 |

**可视 DOM clip** 必须是其 composition 根的直接子节点。若要视觉 wrapper，把 wrapper 放在 clip 内。

**媒体元素是例外（0.7.71+ 起）**：`<video>` / `<audio>` 可以在任意嵌套深度，运行时会扁平发现它们、解析归属 composition 并重算绝对起点。真正的红线是**不要把媒体放进带时间的 wrapper**——时间要么写在媒体元素自己身上，要么让 wrapper 完全不计时。旧手册“媒体必须是 host root 的直接子节点”的写法已作废，见 0.3-A。

可见窗口在边界上包含结束时刻：`start ≤ t ≤ start + duration`，因此最后一帧会保持最终状态。

### 5.4 Track 与 z-index

`data-track-index` 是“时间车道”，不是图层前后关系：

- 同轨道 clip 不得重叠；
- 视觉前后用 CSS `z-index`；
- 常见习惯：0 放底层视频，1+ 放视觉场景和 overlays，10+ 放音频；
- crossfade 的两个场景必须放不同轨道；
- Studio 的视觉行顺序会同时持久化 `data-track-index` 和内联 `z-index`，手写时仍应理解二者语义不同。

相对时间：

```html
<video id="intro" data-start="0" data-duration="10" data-track-index="0" ...></video>
<video id="main" data-start="intro" data-duration="20" data-track-index="0" ...></video>
<video id="overlay" data-start="intro - 0.5" data-duration="2" data-track-index="1" ...></video>
```

引用只能在同 composition 内；被引用 clip 必须有可知时长；不可成环；链不要超过 3–4 层。

### 5.5 子 composition

Host 写法：

```html
<div id="el-chart"
     data-composition-id="data-chart"
     data-composition-src="compositions/data-chart.html"
     data-start="2"
     data-duration="8"
     data-track-index="2"
     data-width="1920"
     data-height="1080"></div>
```

子文件写法：

```html
<!doctype html>
<html>
  <body>
    <template>
      <style>
        #root { position: absolute; inset: 0; }
        .title { font-size: 100px; }
      </style>

      <div id="root" data-composition-id="data-chart"
           data-width="1920" data-height="1080" data-duration="8">
        <h2 id="data-chart-title" class="title">Q4 Revenue</h2>
      </div>

      <script>
        window.__timelines = window.__timelines || {};
        const tl = gsap.timeline({ paused: true });
        tl.fromTo("#data-chart-title", { opacity: 0 }, { opacity: 1, duration: .5 }, 0);
        window.__timelines["data-chart"] = tl;
      </script>
    </template>
  </body>
</html>
```

三条不可违反的跨文件规则：

1. 运行时只 clone `<template>` 内的内容；`<style>`、`<script>`、markup 必须全部在 `<template>` 内；
2. host `data-composition-id`、子根 `data-composition-id`、timeline registry key 三者必须完全相同；
3. 子 composition 根用 `#root` 样式，不要依赖根自身 class 选择器。编译器会给普通选择器加 composition scope，根 class 可能被改写成无法命中的 descendant selector。

Host 的 `data-duration` 是可见窗口：子 timeline 短则保持最后帧，host 窗口短则到点隐藏。不要手工把子 timeline `master.add(child)` 到根 timeline，框架会独立 seek；手工嵌套会双重 seek。

子 composition 内的 element id 要加 composition 前缀，避免多个文件 inline 后产生重复 ID。重复的 image/video ID 可能导致 producer 通过 `getElementById` 注入错对象而变成空白。

入口动画优先使用 `fromTo()`，明确两端状态，减少 seek-back 与 `from()` 初始值捕获造成的差异。

### 5.6 单文件还是模块化

用单文件：

- 只有一个连续场景；
- 一个 Canvas/WebGL/SVG 状态贯穿全片；
- 总规模约 200–400 行；
- 没有重用需要。

用子 composition：

- 三个或更多清晰场景切换；
- 单场景大于约 100 行或 motion 复杂；
- 有可复用片头、片尾、图表、转场；
- 一条音频贯穿多个视觉段；
- 希望逐场景并行制作和单独检查。

模块化项目中，`index.html` 应很薄：声明 scene slots、总时间、根媒体和少量 seam motion。场景内部动画放在各自文件；不要一边有 `compositions/`，一边继续把新场景塞回 index。

共享连续状态的多个 beat 可合并为一个子 composition，在内部用 phase div 与同一 timeline 管理，而不是强行切成多个 slot。

### 5.7 媒体合同

**媒体放置（0.7.71+ 的当前合同）：** `<video>` / `<audio>` 可以放在任意嵌套深度，包括子 composition 的 `<template>` 内部或普通 wrapper `<div>` 里。运行时用一次扁平 `querySelectorAll("video, audio")` 发现媒体，用 `closest("[data-composition-id]")` 确定宿主 composition，再按祖先 composition 累计的绝对起点重算 `data-start`。因此**场景专属素材可以带着场景内局部时间住在自己的场景文件里**，不必再全部上提到 `index.html`。

把媒体放在 `index.html` 根下仍然是合法且常见的做法——贯穿全片的 A-roll、BGM、VO 本来就属于根层。区别只是：现在这是**编排选择**，不再是硬性技术约束。

仍然是硬约束的是：**不要把媒体元素放进带时间的 wrapper**（不要给包着 `<video>` 的 `<div>` 加 `data-start` / `data-duration` / `class="clip"`）。时间写在媒体元素本身，或者让 wrapper 不计时。

```html
<video id="a-roll"
       src="assets/demo.mp4"
       data-start="0" data-duration="12" data-track-index="0"
       data-volume="0" muted playsinline></video>

<audio id="a-roll-audio"
       src="assets/demo.mp4"
       data-start="0" data-duration="12" data-track-index="10"
       data-volume="1"></audio>
```

媒体规则：

- video 必须 `muted playsinline`；即使声音来自同一文件，也用独立 `<audio>` 承担声音；
- 不要调用 `.play()`、`.pause()` 或写 `currentTime`；框架拥有播放与 seek；
- 不在 `<video>` 上 tween `width`、`height`、`top`、`left`；用不计时的 wrapper，并尽量只 tween transform / opacity；
- timeline 只能驱动**和它同属一个 composition** 的媒体：谁的 `closest("[data-composition-id]")` 指向该 composition，就归谁的 timeline 管，时间用该 composition 的局部秒数。放在 `index.html` 根下的媒体归根 timeline，时间用全局秒数；
- 静态响度用 `data-volume`，淡入、duck、淡出可在时间线 tween `volume`；
- `data-media-start` 是源媒体入点；`data-playback-start` 是媒体 wrapper 或子 composition 的源时间偏移；`data-playback-rate` 取 0.1–5；
- 外部跨域媒体需 canvas 抽样时添加 `crossorigin="anonymous"`；
- HEVC/H.265、ProRes 等由 FFmpeg 预解码后渲染；实时 preview 若浏览器不支持，会自动生成缓存代理，除非 `--no-proxy` 或 `media.autoProxy: false`；
- 当前版本支持短视频在较长 slot 中 loop，并正确处理 coverage gate；当前渲染器也能保持视频尾帧。历史 handoff 中“必须用 `tpad` 烘焙 freeze”属于旧版本经验，只有在目标版本验证失败时再使用。

### 5.8 变量

声明是数组，值是对象，不要混淆：

```html
<html data-composition-variables='[
  {"id":"title","type":"string","label":"标题","default":"Hello"},
  {"id":"accent","type":"color","label":"强调色","default":"#66d9ef"},
  {"id":"price","type":"number","label":"价格","default":0,"min":0,"unit":"$"},
  {"id":"featured","type":"boolean","label":"重点","default":false},
  {"id":"plan","type":"enum","label":"套餐","default":"pro",
   "options":[{"value":"pro","label":"Pro"},{"value":"enterprise","label":"Enterprise"}]}
]'>
```

优先使用声明式绑定：

```html
<img data-var-src="heroImage" src="assets/fallback.jpg" alt="" />
<h1 data-var-text="title">Fallback</h1>
<style>.headline { color: var(--accent); }</style>
```

需要条件、循环或派生逻辑时，在初始化阶段读取一次：

```js
const { title, accent } = window.__hyperframes.getVariables();
```

Host 逐实例覆盖：

```html
<div data-composition-id="card"
     data-composition-src="compositions/card.html"
     data-variable-values='{"title":"Enterprise","accent":"#22c55e"}'
     ...></div>
```

CLI 覆盖与批量：

```bash
npx hyperframes render --variables '{"title":"Q4 Report"}' --strict-variables -o q4.mp4
npx hyperframes render --variables-file vars.json -o out.mp4
npx hyperframes render --batch rows.json --output 'renders/{name}.mp4' --strict-variables
```

优先级：声明默认值 < host `data-variable-values` < 顶层 CLI `--variables`。顶层 CLI 覆盖不会自动穿透到子 composition；子 composition 的值由各 host 提供。

变量不能改变：composition 宽高、已在源 HTML 中写死的根总时长、CLI fps、格式、编码与质量。媒体 URL、文字、颜色、普通 clip 时长和 color grading 可变量化。带声音的 `data-var-src` 媒体要保留真实 fallback `src`，以便音频提取。

### 5.9 Color grading 与 media treatment（0.7.71–0.7.73 大幅扩展）

视频和图片用 `data-color-grading` 表达调色、风格化 shader 与 LUT。`0.7.73` 把它从“简单 grade”扩成了一套完整调色台：三路色轮、RGB 曲线、hue 曲线和 HSL 二级校色。以下 schema 来自 `0.7.77` 运行时与 `media-treatment --all`（capabilities `version: 2`），**比官网 `guides/color-grading` 页面新**。

作用对象只有 `<img>` 和 `<video>`；工作色彩空间是 `rec709`（SDR）。

#### 完整 payload 结构

应用顺序固定为 `adjust → wheels → curves → hueCurves → secondaries → lut → details → effects`。

```json
{
  "preset": "clean-studio",
  "intensity": 1,

  "adjust": {
    "exposure": 0, "contrast": 0, "highlights": 0, "shadows": 0,
    "whites": 0, "blacks": 0, "temperature": 0, "tint": 0,
    "vibrance": 0, "saturation": 0
  },

  "wheels": {
    "shadows":    { "hue": 0, "amount": 0, "level": 0 },
    "midtones":   { "hue": 0, "amount": 0, "level": 0 },
    "highlights": { "hue": 0, "amount": 0, "level": 0 }
  },

  "curves":    { "master": [[0,0],[1,1]], "red": [], "green": [], "blue": [] },
  "hueCurves": { "hueVsHue": [], "hueVsSaturation": [], "hueVsLuma": [] },

  "secondaries": [{
    "enabled": true,
    "hue":        { "center": 210, "range": 30, "softness": 15 },
    "saturation": { "min": 0.1, "max": 1, "softness": 0.1 },
    "luma":       { "min": 0, "max": 1, "softness": 0.1 },
    "correction": { "hueShift": 0, "saturation": 0, "luma": 0, "temperature": 0, "tint": 0 }
  }],

  "details": {
    "vignette": 0, "vignetteMidpoint": 0.5, "vignetteRoundness": 0, "vignetteFeather": 0.65,
    "grain": 0, "grainSize": 0.25, "grainRoughness": 0.5
  },

  "effects": { "blur": 0, "pixelate": 0, "bloom": 0, "kuwahara": 0 },
  "palette": ["#0b0d0d", "#eee9db"],
  "lut": { "src": "assets/luts/look.cube", "intensity": 0.75 },
  "colorSpace": "rec709"
}
```

#### 取值范围与约束

| 分组 | 键 | 恒等值 | 范围 |
|---|---|---|---|
| 顶层 | `intensity` | 1 | 0–1 |
| `adjust` | `exposure` | 0 | −2 – 2 |
| `adjust` | 其余 9 项 | 0 | −1 – 1 |
| `wheels.<zone>` | `hue` | 0 | 0–360（度，环绕） |
| `wheels.<zone>` | `amount` | 0 | 0–1 |
| `wheels.<zone>` | `level` | 0 | −1 – 1 |
| `curves` | `master / red / green / blue` | — | 输入输出均 0–1；2–16 点；隐含端点，端点计入上限 |
| `hueCurves` | `hueVsHue / hueVsSaturation / hueVsLuma` | — | 至少 3 点，最多 16 点 |
| `secondaries` | 数组 | — | 最多 4 个 qualifier |
| `secondaries.hue` | `center` / `range` / `softness` | — | 度；`range + softness ≤ 180` |
| `secondaries.saturation`/`luma` | `min` / `max` / `softness` | — | 0–1，要求 `min < max`；softness 上限 0.5 |
| `secondaries.correction` | `hueShift` | 0 | −180 – 180 |
| `secondaries.correction` | `saturation` / `luma` / `temperature` / `tint` | 0 | −1 – 1 |
| `details` | `vignette*` / `grain*` | 见上方 JSON | 0–1（`vignetteRoundness` 为 −1 – 1） |
| `lut` | `format` / `maxCubeSize` / `intensity` | — | `3d-cube` / 64 / 0–1 |
| `palette` | 颜色数 | — | 2–6 个 `#rrggbb` |

#### 18 个 preset

`neutral`、`warm-daylight`、`clean-studio`、`skin-soft`、`food-pop`、`night-lift`、`muted-editorial`、`vintage-wash`、`mono-clean`、`mono-fade`、`soft-boost`、`bright-pop`、`deep-contrast`、`creator-camcorder`（默认 intensity 0.72）、`vhs-playback`、`home-movie-8mm`（0.72）、`editorial-halftone`、`two-ink-print`。

#### 18 个 shader effect，分四族

| 族 | effects |
|---|---|
| `essentials` 光学、对焦、隐私 | `blur`、`pixelate`、`bloom`（+`bloomRadius`）、`kuwahara`、`chromaticAberration` |
| `retro-glitch` 磁带、胶片、CRT、数字故障 | `tapeDamage`（+`tapeTracking`/`tapeNoise`/`tapeSpeed`）、`filmArtifacts`、`chromaBleed`、`scanlines`、`crtCurvature`、`digitalGlitch`、`monoScreen` |
| `print` 半调、限色、抖动 | `halftone`（+`halftoneSize`）、`twoInkPrint`（+`twoInkPrintSize`）、`dither`（+`ditherSize`） |
| `art` ASCII、雕刻、排线、绘画 | `ascii`（+`asciiSize`/`asciiInvert`）、`engraving`、`crosshatch` |

15 个内置 palette 供兼容 effect 使用：`noir`、`ink-paper`、`terminal`、`amber-glow`、`handheld-green`、`golden-hour`、`deep-sea`、`arctic-night`、`synthwave`、`vaporwave`、`forest`、`sepia`、`blueprint`、`warm-print`、`electric-ink`。

#### 调色可以动画（seek-safe）

这是 `0.7.7x` 新增的重要能力：部分调色值暴露为 CSS 自定义属性，**注册过的 GSAP timeline 可以直接 tween 它们**，且保持确定性。可动画的 9 项：

| payload 路径 | CSS 变量 | 范围 |
|---|---|---|
| `intensity` | `--hf-color-grading-intensity` | 0–1 |
| `lut.intensity` | `--hf-color-grading-lut-intensity` | 0–1 |
| `adjust.exposure` | `--hf-color-grading-exposure` | −2 – 2 |
| `effects.blur` | `--hf-color-grading-blur` | 0–1 |
| `effects.bloom` | `--hf-color-grading-bloom` | 0–3 |
| `effects.kuwahara` | `--hf-color-grading-kuwahara` | 0–1 |
| `effects.pixelate` | `--hf-color-grading-pixelate` | 0–1 |
| `effects.ascii` | `--hf-color-grading-ascii` | 0–1 |
| `effects.dither` | `--hf-color-grading-dither` | 0–1 |

```js
// 马赛克解码式 reveal：不写自定义 shader，也不用 CSS filter 冒充
tl.fromTo("#hero-clip",
  { "--hf-color-grading-pixelate": 0.9 },
  { "--hf-color-grading-pixelate": 0, duration: 1.2, ease: "power2.out" }, 0.3);
```

需要“揭示 / 聚焦 / 去码 / 淡出处理效果”时优先用这条路径，而不是叠一层 CSS `filter` 或黑色遮罩——后者不属于确定性渲染管线，也会被 media-treatment 政策判为改写。

#### `hyperframes media-treatment` 命令（0.7.72 新增）

Agent 用来发现、分析、应用和清除媒体处理的入口，全部支持 `--json`：

```bash
# 发现能力（先看总览，再钻一族/一项）
npx hyperframes media-treatment --capabilities --json
npx hyperframes media-treatment --capability grading --json
npx hyperframes media-treatment --capability kuwahara --json
npx hyperframes media-treatment --all            # 穷举目录，只给工具用

# 分析实际素材，拿到一个有界的主校正建议
npx hyperframes media-treatment --selector '#hero' --analyze --json

# 应用 / 试跑 / 清除
npx hyperframes media-treatment --selector '#hero' \
  --grading '{"preset":"muted-editorial","adjust":{"shadows":0.18}}' --apply
npx hyperframes media-treatment --selector '#hero' --grading '{...}' --dry-run --json
npx hyperframes media-treatment --selector '#hero' --clear
```

其他参数：`--project`（默认 cwd）、`--file`（默认 `index.html`）、`--selector-index`（选择器不唯一时的 0 基下标）。

#### Media treatment 政策（`/media-use`）

`0.7.77` 起，凡是**关于实拍素材观感的请求**都归 `/media-use`，包括用户完全没提调色词汇的模糊反馈。先按下表选最小的那条车道，再选配方：

| 用户意图 | 车道 |
|---|---|
| 太暗、太平、太暖、暗部太多 | correction |
| 想塑造明暗层次或某个颜色 | wheels / curves / HSL secondary |
| 高级感、电影感、贴合选题 | preset 或自定义 treatment |
| 复古、印刷、ASCII、故障、DV 感 | shader effect 或带 effect 的 preset |
| 遮住整段素材 | 隐私 Blur / Pixelate |
| 遮住一张脸、车牌、地址、某个屏幕区域 | 先做裁切 / 遮罩素材，或用外部工具 |
| 想让素材更吸睛但不改像素 | 构图、运动，或可选 overlay |
| reveal、聚焦、去码、淡出处理 | 有限的 seek-safe 处理关键帧 |
| REC 角标、漏光、闪白、定格装饰 | Registry overlay 块 + 必要的像素处理 |

硬性边界，写进交付说明不要含糊：

- **实时调色和 effect 作用于整个被选中的 `<img>` / `<video>`，不做人脸、车牌、区域的隔离或跟踪。** 用户说“把这张脸遮住”时，必须说明整片模糊的范围，或先产出裁切 / 遮罩素材；**不要暗示做了不存在的追踪**。
- 只处理有意义的实拍素材。文字、SVG、logo、图标、UI 界面和刻意风格化的画面默认跳过。
- 这条路径是 Rec.709/SDR。**不要**把 HDR、HLG、PQ 或 camera LOG 素材静默塞进去。
- correction 能解决的抱怨就不要加风格化 effect；只是时间问题就不要动颜色；素材本身能表达就不要装 overlay。
- 反过来：用户点名要 VHS / glitch / ASCII / halftone / DV / 印刷 / 雕刻这类**强风格**时，就要给足强度，让 after-frame 一眼能认出来。克制只适用于校正和打磨，不适用于用户明确点名的风格化。

字段仍可整体引用变量，例如 `"preset":"$gradingPreset"`、`"exposure":"${gradingExposure}"`。Grade 属于媒体 finishing，不应代替场景本身的色彩设计。

---

## 6. 动画合同

### 6.1 GSAP 默认路径

95% 的常规 motion 使用 GSAP：

```js
window.__timelines = window.__timelines || {};
const tl = gsap.timeline({ paused: true });
tl.fromTo("#card",
  { y: 64, opacity: 0, scale: 0.96 },
  { y: 0, opacity: 1, scale: 1, duration: .7, ease: "power3.out" },
  0.3
);
window.__timelines["scene-id"] = tl;
```

硬规则：

- 同步构建，不能在 `async`、`Promise`、`setTimeout`、事件回调中创建 render-critical timeline；
- 必须 `{ paused: true }`；
- 不要 `tl.play()`；
- key 精确匹配 composition id；
- 不要用空 tween 仅为了凑时长，clip/root 用 `data-duration`；
- 不要在页面加载时 `gsap.set()` 尚未进入 DOM 的后续 `.clip`；在 timeline 的明确时间点用 `tl.set()`；
- entrance 在子 composition 中优先 `fromTo()`；
- 一组 motion 通常组合 2–4 个原子规则即可，不要每个镜头都做成复杂 blueprint。

### 6.2 允许动画的属性

优先：

- `x`, `y`, `scale`, `scaleX`, `scaleY`, `rotation`；
- `opacity`；
- `color`, `backgroundColor`, `borderRadius`；
- 其他确定性的 transform。

禁止或谨慎：

- 不 tween `display` 或原始 `visibility`；
- `autoAlpha` 只用于非 clip 元素或 clip 内 wrapper；
- `tl.set(..., {visibility: ...})` 只可在明确边界、非 clip 元素上做确定性硬切；
- 不直接 tween 布局属性 `width`、`height`、`top`、`left`，尤其媒体；
- 不让多个 timeline 同时写同一元素同一属性；
- 空间运动只用 transform aliases；
- tween 期间不要调用 `getBoundingClientRect()` 动态推导位置。初始化时测量一次或预计算常量。

### 6.3 确定性禁令

不可用来驱动视觉状态：

- `Date.now()`、`performance.now()`；
- 未播种的 `Math.random()`；
- render 时的必需网络 fetch；
- hover、focus、scroll、pointer 状态；
- 依赖前一帧累计结果的粒子或物理状态。

有限循环：

```js
const repeats = Math.max(0, Math.floor(duration / cycleDuration) - 1);
```

必须用 `floor`，不能用 `ceil`；后者会越过 composition 时长并触发 `gsap_repeat_ceil_overshoot`。`Math.max(0, …)` 也不能省——负的 repeat 等于无限。

**关于 `repeat: -1`（0.7.71 起有条件放宽）：**

- 根有显式且有限的 `data-duration` → lint 只报 **warning**，HyperFrames 会把确定性 seek 与导出裁到那个显式时长；
- 根没有有限 `data-duration` → 仍然是 **error**，timeline 可能报告无界时长而使渲染排程失败。

`hyperframes-core` 的确定性规范至今仍把 `repeat: -1` 列在禁止项里。因此默认写法不变：**算有限次数**。只有在无限循环装饰确实合理、且根 `data-duration` 显式有限时才用它，并把这条 warning 写进交付说明——不要让它无声地留在 check 输出里。

### 6.4 布局和文字

- 静态 DOM/CSS 中先存在正确终态；
- 主内容用 grid/flex/padding/max-width，绝对定位主要用于层与装饰；
- transformed 元素要是 block/flex item 且有真实宽高；
- body text 不用 `<br>` 强制换行，短 display title 的刻意逐词换行除外；
- 动态文字使用宽度、wrap 或 `window.__hyperframes.fitTextFontSize()`；高性能排版可使用 `window.__hyperframes.pretext`；
- overshoot、pulse 装饰按峰值尺寸预留空间，不要卡在 `overflow:hidden` 边缘；
- 布局检查的豁免标记按“越窄越好”选：单个刻意出血用 `data-layout-bleed="true"`；入 / 出场行程造成的溢出用 `data-layout-allow-overflow`；刻意的文字叠压（例如演示光标标签压在标题上）用 `data-layout-allow-overlap`；某元素本来就该盖住文字用 `data-layout-allow-occlusion`；纯装饰、根本不该被审计的元素才用 `data-layout-ignore`。`data-layout-allow-overflow` 会抑制整棵子树的多种感知检查，不要当万能开关用。
- 旋转要设对轴心。`0.7.69`–`0.7.76` 新增了 `rotation_pivot_drift`（旋转时元素外接框中心漂移，说明它不是绕自身中心转）和 `off_pivot_rotation`（仪表 / 表盘指针的旋转中心偏离轴心，导致指错或过冲）。修法是调 `transformOrigin` / `svgOrigin`，或先把旋转组平移到轴心再旋转。

### 6.5 其他运行时

| 运行时 | 使用场景 | Seek 方式 |
|---|---|---|
| GSAP | 默认时间线、变换、easing、stagger | `window.__timelines` |
| Lottie / dotLottie | AE 预烘焙动画 | `window.__hfLottie` |
| Three.js | 3D、相机、shader、GLTF | `hf-seek` / adapter 时间 |
| Anime.js | 轻量 tween | `window.__hfAnime` |
| CSS keyframes | 简单装饰、shimmer、有限循环 | delay / play-state / finite duration |
| WAAPI | 浏览器原生 keyframes | `animation.currentTime` |
| TypeGPU / WebGPU | GPU 粒子、液体、compute shader | `hf-seek` |

多个运行时可以共存，但都必须能对任意时间重复 seek。Frame Adapter v0 的基本语义是：`getDurationFrames()` 返回有限非负整数，`seekFrame(frame)` 支持任意顺序且幂等，越界需要 clamp，生命周期为 init → 多次 seek → destroy。

### 6.6 HTML-in-Canvas

HTML-in-Canvas 把 live DOM 作为 WebGL texture，用于 3D 设备屏幕、玻璃、shatter、portal、shader 后期等。Chrome 的 `canvas.drawElement()` 能力在普通浏览器中可能需要实验 flag；HyperFrames CLI render 与 Docker 会自动启用。

原则：

- 先 feature detect；
- 需要 DOM 每帧更新时重新捕获 texture；
- 控制捕获区域和纹理分辨率，避免整页高成本复制；
- 仍遵守确定性，DOM 与 shader 状态都由当前时间推导；
- 优先从 Catalog 安装现成 block，例如 iPhone/MacBook、Liquid Glass、Portal、Shatter、Magnetic、Text Cursor。

### 6.7 Tailwind v4

- 只在 `init --tailwind` 项目使用 scaffolded runtime；
- 用 `@theme`、`@utility`，不用 v3 的 `@tailwind base/components/utilities`；
- v3 配置必须显式 `@config "./tailwind.config.js"`；
- 关键 class token 必须静态出现在 HTML/CSS 中，不在 seek 时拼接 `bg-${color}-500`；
- 固定 viewport 视频不使用 `md:` / `lg:` 响应式分支；
- render-critical motion 不用 `transition-*` 或交互 variants；
- v4 的裸 `border` 使用 currentColor，务必显式颜色；
- 最终除 `check` 外，还要渲染一段证明 frame 0 没有 unstyled flash。

---

## 7. Registry、Catalog 和可复用能力

### 7.1 Block 与 Component

- Block：独立子 composition，有自己的尺寸、时长、timeline；安装到 `compositions/<name>.html`；
- Component：效果片段，没有独立尺寸；安装到 `compositions/components/<name>.html`，需要把 HTML/CSS/JS 合并到 host。

```bash
npx hyperframes catalog --json
npx hyperframes catalog --type block --tag social --json
npx hyperframes add data-chart --no-clipboard --json
npx hyperframes add grain-overlay --dir .
```

一次性先安装所有计划使用的 registry item，再进行并行场景制作，避免多个 worker 同时修改 registry 与配置。

### 7.2 当前 Catalog 能力地图

`0.7.77` 实测 `catalog --json` 共 **138 项：113 个 block + 25 个 component**。覆盖：

- 代码动画：3D Extrude、Shader Dissolve、Particle Assemble、Morph、Snippet Flight、Typing、Diff、Highlight Sweep、Scroll to Line；
- 字幕组件：Clip Wipe、Editorial Emphasis、Emoji Pop、Glitch RGB、Gradient Fill、Highlight、Kinetic Slam、Matrix Decode、Neon、Parallax、Particle Burst、Pill Karaoke、Texture、Weight Shift；
- HTML-in-Canvas / VFX：iOS 26、macOS Tahoe、Liquid Glass、iPhone & MacBook 3D、Liquid Background、Magnetic、Portal、Shatter、Text Cursor；
- 社交 overlays：Instagram、TikTok、YouTube、X、Reddit、Spotify、macOS Notification；
- Lower thirds：BILD、Accent Underline、Bold Block、Clean Bar、Color Block、Dark Card、Kicker Name、Mask Reveal、Side Rule、Soft Pill、Stack Bars、News Ticker；
- Shader transitions：Chromatic Radial Split、Cinematic Zoom、Cross Warp、Domain Warp、Flash Through White、Glitch、Gravitational Lens、Light Leak、Ridged Burn、Ripple、SDF Iris、Swirl、Thermal、Whip Pan；
- CSS transition 套件：3D、Blur、Cover、Destruction、Dissolve、Distortion、Grid、Light、Mechanical、Push、Radial、Scale 等；
- 数据与地图：Data Chart、Spain、US choropleth / bubble / flow / hex、World Map；
- Effects / text：Grain、Vignette、Shimmer、Grid Pixelate、Parallax Zoom/Unzoom、Blend Difference、Morph Text、Texture Mask；
- 完整 showcases：App Showcase、Apple Money Count、3D UI Reveal、VPN spot、NYC→Paris flight、North Korea map 等；
- 代码 snippet 主题：Apple Terminal 系列、VS Code Dark/Light/High Contrast/Monokai/Solarized 等；
- **Media-treatment overlays（`media-treatment-overlay` 标签，配合 5.9 使用）**：`camcorder-hud`、`editorial-flash-overlay`、`organic-light-leak-overlay`、`freeze-frame-dressing`。需要 REC 角标、闪白、漏光、定格装饰时装这些块，不要手搓；
- **WebGPU Liquid Glass 家族**：`ios26-liquid-glass`、`liquid-glass-notification`、`liquid-glass-context-menu`、`liquid-glass-media-controls`、`liquid-glass-widgets`；
- **15 个字幕 component**（`caption-*`）：Pill Karaoke、Neon Accent、Weight Shift、Emoji Pop、Editorial Emphasis、Parallax Layers、Glitch RGB、Matrix Decode、Particle Burst、Texture、Clip Wipe、Kinetic Slam、Gradient Fill、Neon Glow、Highlight。`0.7.71` 起字幕模板改为**运行时数据驱动**（由 transcript 供数），不再需要手写逐词 markup。

Catalog 是快速变化的在线表面，Agent 不应依赖这份静态名单做最终选择；先 `catalog --json`，再显式 `add <name>`。按标签筛选比按记忆猜名字可靠：

```bash
npx hyperframes catalog --type block --tag media-treatment-overlay --json
npx hyperframes catalog --type component --tag captions --json
```

### 7.3 hyperframes.json

```json
{
  "registry": "https://raw.githubusercontent.com/heygen-com/hyperframes/main/registry",
  "paths": {
    "blocks": "compositions",
    "components": "compositions/components",
    "assets": "assets"
  }
}
```

第一次 `add` 时，如果项目已有 `index.html` 但没有配置，CLI 可生成默认文件。

---

## 8. 标准开发循环

### 8.1 建议顺序

```bash
# 1. 快速静态反馈
npx hyperframes lint

# 2. 最终浏览器门禁；内部会再次 lint
npx hyperframes check --snapshots

# 3. 子 composition 或关键镜头的可视抽样；对某个 finding 放大看
npx hyperframes snapshot --frames 10
npx hyperframes snapshot --zoom '#cta'

# 4. 最终 Studio 审片
npx hyperframes preview

# 5. 用户批准后才渲染
npx hyperframes render --quality high --output renders/final.mp4

# 6. 验证交付物
test -s renders/final.mp4
ffprobe -v error -show_format renders/final.mp4
```

### 8.2 lint、check、snapshot 各自负责什么

- `lint`：HTML 结构、必需属性、track overlap、GSAP 危险模式、重复 ID、旧属性、变量等；
- `check`：一个浏览器会话中的 runtime error、请求失败、layout、motion sidecar 断言、对比度和感知问题；
- `snapshot`：真正看见某个时间点，尤其发现子 composition 没挂载、样式丢失、媒体黑/空、SVG 巨大、文字堆左上等跨文件问题；
- `preview`：给用户在 Studio 时间线审片和细调；
- `render`：生成最终文件，不是验证替代品。

最终门禁不需要先单独再跑一次 lint：`check` 会包含 lint，而且 lint 报 error 时它**根本不启动浏览器**。制作中结构改动后单跑 lint 仍有价值。

#### check 的常用参数

```bash
npx hyperframes check --json             # {ok, lint, runtime, layout, motion, contrast, snapshots}
npx hyperframes check --snapshots        # 标注了 finding 框的总览帧 + 每个 error 的裁切图
npx hyperframes check --samples 15       # 更密的时间线扫描（默认 9）
npx hyperframes check --at 1.5,4,7.25    # 指定 hero frame 时间点
npx hyperframes check --at-transitions   # 额外采样每个 tween 的起止边界，抓转场瞬时重叠
npx hyperframes check --tolerance 4      # 报溢出前允许的像素数（默认 2）
npx hyperframes check --strict           # warning 也影响退出码
npx hyperframes check --layout 'proseCoverageFloor=0.05'   # 0.7.77 新增，默认 0.15
```

编排器用的可选门禁（默认关闭）：

```bash
npx hyperframes check --caption-zone 'x0=0;y0=.82;x1=1;y1=1;severity=error;seek=.25,1'
npx hyperframes check --frame-check      # 媒体越出画幅检测，阈值 max(120px, 短边 6%)
```

#### check 的判定语义（容易踩的三件事）

1. **严重度看“是否持久”。** 只在单个采样点出现的问题（入 / 出场瞬态）降级为 info，不影响退出码；跨采样持续存在才 gating。持续的 `content_overlap` 是 error；持续且部分可见的 `canvas_overflow` 突破画幅 5% 时升为 warning。
2. **坐标系类 finding 单独一类**：`escaped_container`、`panel_out_of_canvas`、`connector_detached`——它们指“几何算在一个坐标系、画在另一个坐标系”，例如元素跑到 offset parent 之外、面板卡在画幅边缘、连接线脱离了所有节点。
3. **`sweep_static` 会直接判失败。** 3 秒以上的 composition 如果所有采样点之间毫无几何变化，check 拒绝通过——冻结的时间线让任何绿灯都不可信。指纹包含逐元素 opacity，所以纯 opacity 的 reveal 也算运动，**但只在它仍在进行中的采样点算**。经典陷阱：reveal 很早结束、后面长时间保持静帧，于是每个采样都落在稳定态而失败。正确修法是把 reveal 铺开，或保留一个持续运动的元素（打字镜头用闪烁光标是惯例）；**不要**为了糊弄检查加一段缓慢位移。

对比度失败现在是 **gating error**（不再是 warning），阈值为正文 4.5:1、大字 3:1（24px+，或 19px+ 粗体）。每个 finding 自带采样到的前景 / 背景色、实测与所需比值，以及同色系方向上的 `suggestedColor`——多数对比度问题不用看截图就能改。

#### `*.motion.json`：让 check 验证运动意图

这是“不用把 MP4 渲出来盯着看”的最接近替代品，能抓到布局采样抓不到的 render-vs-preview 问题：seek 跳过了入场、stagger 顺序错乱、元素中途飘出画面、镜头冻结。

把 sidecar 放在 composition 旁边（同目录多个 composition 时按 html 基名匹配），`check` 自动发现，无需加参数；没有 sidecar 时行为不变。

```json
{
  "duration": 6,
  "assertions": [
    { "kind": "appearsBy", "selector": "#headline", "bySec": 0.5 },
    { "kind": "before", "a": "#headline", "b": "#cta" },
    { "kind": "staysInFrame", "selector": ".card" },
    { "kind": "keepsMoving", "withinSelector": ".scene" }
  ]
}
```

| 断言 | 失败条件（错误码） |
|---|---|
| `appearsBy(selector, bySec)` | `bySec` 之前没可见（opacity ≥ 0.5）——`motion_appears_late` |
| `before(a, b)` | `a` 没有严格早于 `b` 首次出现——`motion_out_of_order` |
| `staysInFrame(selector)` | 可见之后其外接框离开画幅——`motion_off_frame` |
| `keepsMoving(withinSelector?)` | 完全静止的窗口超过 `maxStaticSec`（默认 2 秒）——`motion_frozen` |

`duration`、`withinSelector`、`maxStaticSec` 可选。断言失败默认是 **error**。选择器匹配不到任何元素会报 `motion_selector_missing` 而不是静默通过——拼错的选择器会大声失败。

#### snapshot 与放大取证

`check --snapshots` 已经为每个带 bbox 的 error 写了 `finding-NN-<code>.png` 裁切图。独立使用时：

```bash
npx hyperframes snapshot                          # 5 个关键帧
npx hyperframes snapshot --frames 10              # 均匀 N 帧
npx hyperframes snapshot --zoom '#cta'            # 按选择器裁切，3 倍密度
npx hyperframes snapshot --zoom '100,50,400,300' --zoom-scale 2   # 按像素区域
```

`--zoom` 通过提高 `deviceScaleFactor` 出真实高密度裁切，**不用 CSS zoom 也不改 viewport**，所以布局和渲染确定性不受影响。选择器匹配不到会大声报错；目标在该帧没有可见盒子（塌陷或动到画外）会跳过并注明，而不是写出一条细缝。

### 8.3 Studio

Studio 提供：

- live preview 与 hot reload；
- clips 时间线与播放控制；
- move 更新 `data-start`；
- 换轨更新 `data-track-index`；
- 行顺序更新内联 `z-index`；
- 右 trim 更新 `data-duration`；
- 媒体左 trim 同时更新 `data-start` 与 `data-media-start` / `data-playback-start`；
- GSAP keyframe diamonds、ease、属性编辑；
- x/y tween 的 arc motion 与 MotionPath；
- gesture recording；
- 选中元素的上下文复制与 Agent 查询。

`0.7.72–0.7.77` 新增：

- **keyframe ease 编辑器**，带预设库，配套确定性 ease 运行时（0.7.72）；
- **media treatment 检查器** 与**专业调色控件**：三路色轮、主通道与 RGB 分通道曲线、hue-vs-hue / hue-vs-saturation / hue-vs-luma 曲线、HSL 二级校色（0.7.72–0.7.73），写出的就是 5.9 的 payload；
- **时间线升级**（0.7.77）：可展开的属性轨道、轨道头、精确 keyframe 重定时、嵌套 composition 支持；
- 扁平 inspector 面板成为默认（旧版可用环境变量切回）。

普通 DOM motion clip 没有真正的“左 trim”，因为它缺少内部 animation source offset；只能整体移动或剪短尾部。媒体与子 composition 有 playback offset 才能做真实 start trim。

Agent 不确定用户说的“这个元素”时，查询 Studio：

```bash
npx hyperframes preview --context --json --context-fields selection
```

优先使用 `selection.target.hfId`，否则使用 selector 与 source file。返回 `no-selection` 时让用户先点击元素。

### 8.4 Storyboard board 与最终 preview 不同

- Storyboard board：计划阶段，可在 composition 检查前打开，URL 含 `?view=storyboard#project/...`；
- Final composition preview：`check` 通过后，URL 为 `#project/...`；
- 用户批准 storyboard 不等于批准最终视频；render 前仍需 final preview 批准。

---

## 9. 七阶段生产管线

| 阶段 | 产物 | 核心任务 |
|---|---|---|
| Capture | `capture/` | 截图、字体、颜色、资产、文字、动画、CTA |
| Design | `DESIGN.md` | 品牌事实、组件、间距、Do/Don't |
| Strategy | brief 决策 | 受众、唯一信息、类型、节奏、叙事弧 |
| Storyboard + Script | `STORYBOARD.md`, `SCRIPT.md` | 概念优先分镜、旁白/屏幕文案、素材审计 |
| VO + Timing | `narration.*`, `transcript.json` | TTS、词级时间、真实 beat 边界 |
| Build | `compositions/*.html` | 按场景实现静态布局、设计、motion |
| Validate | checks + snapshots | 静态、浏览器、视觉、最终审片 |

依赖关系比编号更重要：

- 已知 prompt 的 TTS、BGM、图片/视频生成可以后台并行；
- registry blocks 在并行工作前一次性安装；
- narration 的真实词级时间覆盖 storyboard 中的估算时长；
- frames 完成后 assembly，再加 transitions、captions；
- 最终 verify 通过才进入 final look；
- 最终 look 得到批准才 render / publish。

### 9.1 网站到视频

```bash
npx hyperframes capture https://example.com -o capture
```

Capture 可提取：scroll screenshots、像素与 computed style 色板、CSS 字体与 woff2、图片/SVG/Lottie/视频预览、可见文本、WAAPI/scroll/WebGL 动画、页面 sections 和 CTA。

可选 Gemini/OpenRouter vision 为资产补充视觉描述，但 key 不是基础流程必需。捕获结果只提供品牌事实，创意叙事仍在 storyboard 中决定。

### 9.2 Figma

两条通道：

- REST/CLI：asset、tokens、editable component；适合 CI，所有文件最终冻结到本地；
- Figma MCP：Motion、shader、storyboard 与任何计划的变量读取。

顺序：先 tokens，再 components，以便颜色绑定到品牌变量。Figma storyboard 不是逐页 slideshow：共享元素应被理解为同一对象的时间状态，并重建为连续 DOM motion；产品 UI 的多个状态可进一步重建为真实交互序列。

### 9.3 音频

```bash
npx hyperframes tts SCRIPT.md --voice af_nova --output narration.wav
npx hyperframes transcribe narration.wav
```

原则：

- `SCRIPT.md` 是语义文案，`narration.txt` 可保存发音替换后的实际口播；
- 词级 `transcript.json` 是镜头时长和字幕的真实时间源；
- A-roll lip sync 最稳妥的方式是画面片段与声音来自同一源文件，且源入点一致；
- 音频剪接边界用短 afade 可防 click/pop；
- SFX 绑定视觉因果，BGM 提供结构，不要把每个字都做成噪声；
- 音频生成与场景制作可以并行，但最终 render 前必须等待全部生成完成。

### 9.4 背景移除与 text-behind-subject

```bash
npx hyperframes remove-background input.mp4 -o subject.webm
npx hyperframes remove-background input.mp4 -o subject.webm --background-output plate.webm
```

典型层级：原背景视频 → behind text → 透明主体 → front captions。WebM 适合浏览器/HF composition，ProRes 4444 MOV 适合 NLE 往返，PNG 适合单图。

---

## 10. 渲染与输出

### 10.1 本地与 Docker

| 场景 | 选择 |
|---|---|
| 日常迭代 | 本地 `render --quality draft` |
| 最终本地交付 | `--quality high` |
| CI / 跨机器像素稳定 | `--docker --strict` |
| 无本地 Chrome/FFmpeg 基础设施 | HeyGen Cloud |
| 必须自管 AWS | Lambda |
| 必须自管 GCP | Cloud Run |

Docker 固定 Chrome、字体和 FFmpeg，解决跨平台差异；它不保证旧 CLI 与新 CLI 的算法输出完全相同。

### 10.2 格式

| 格式 | 用途 | Alpha |
|---|---|---|
| MP4 / H.264 | 通用交付 | 否 |
| MOV / ProRes 4444 | Premiere、Resolve、AE、Final Cut 透明叠加 | 是 |
| WebM / VP9 | 浏览器透明视频 | 是，但主流 NLE 常忽略 |
| PNG sequence | 无损合成、定制编码 | 是 |
| GIF | GitHub、README、短循环，无音频 | 1-bit |

```bash
npx hyperframes render --format mov --output overlay.mov
npx hyperframes render --format webm --output overlay.webm
npx hyperframes render --format png-sequence --output frames/
npx hyperframes render --format gif --fps 15 --gif-loop 0 --output demo.gif
```

透明 composition 不要给 `html`、`body`、root 设置不透明背景。

### 10.3 质量、分辨率和性能

- `draft`：CRF 28 / ultrafast，迭代；
- `standard`：CRF 18 / medium，常规 1080p；
- `high`：CRF 15 / slow，最终交付；
- `--crf` 与 `--video-bitrate` 互斥；WebM 另有 `--vp9-cpu-used`（−8–8，越大越快、质量 / 体积代价越大）；
- `--fps` 接受整数（24/25/30/50/60/120/240）也接受 ffmpeg 风格分数：`30000/1001`（29.97）、`24000/1001`（23.976）、`60000/1001`（59.94）。不传时取根 `data-fps`，再退到 30；
- UI 录屏或颜色敏感源视频用 `--video-frame-format png`；带 alpha 的源始终按 PNG 抽帧；
- `--resolution` 预设：`landscape`(1920×1080)、`portrait`(1080×1920)、`landscape-4k`(3840×2160)、`portrait-4k`(2160×3840)、`square`(1080×1080)、`square-4k`(2160×2160)，别名 `1080p` / `4k` / `uhd` / `1080p-square` / `4k-square`。本质是整数倍 deviceScaleFactor 超采样；画幅必须与 composition 相同，不支持降采样，当前不与 HDR 同用。`init` 也接受同一组预设；
- `--gpu` 是 FFmpeg 硬件编码；`--browser-gpu` 是另一个开关，默认 auto（首次启动探测，无 GPU 时回落 SwiftShader），`--no-browser-gpu` 强制软件渲染；
- worker 每个约一个 Chrome 进程（约 256 MB），内存紧张先降到 1。`--low-memory-mode` 会锁 1 worker、改用截图捕获、跳过自动 worker 标定；默认按总内存自动判定（≤ 8 GB 开启），也可用 `PRODUCER_LOW_MEMORY_MODE`；
- `--page-side-compositing`（**默认开**）把 shader 转场放到 Chrome 内的 WebGL canvas 上跑，SDR 转场渲染约快 6 倍；HDR / alpha / 视频内容会自动禁用，`--no-page-side-compositing` 强制走 Node 侧分层合成；
- `--experimental-fast-capture` 用 Chrome 的 `drawElementImage` 直接读 DOM paint 记录，约快 2 倍；在 macOS + 硬件 GPU 上默认开启，不兼容的 composition 与**自检失败的帧会自动回退**到截图捕获（0.7.70 加的自检，0.7.75 补了 `BeginFrame` 预检与定向重试）；
- `--frames-cache-dir` 迁移内容寻址的抽帧缓存目录（默认在系统临时目录），传 `off` / `none` / `false` / `0` 可完全关闭；系统盘小的机器（尤其 Windows 长渲染）需要它；
- 重型 composition 超时用 `--browser-timeout`（秒，控制 `page.goto`，默认 60 秒）、`--protocol-timeout`（CDP，默认 5 分钟）、`--player-ready-timeout`（播放器就绪，默认 45 秒）；
- `--best-effort` 默认开启：带结构化的“捕获就绪”警告也出片。要在媒体缺失 / 未就绪时直接失败，用 `--no-best-effort`。`--strict` 在 lint error 时失败，`--strict-all` 连 warning 也失败；
- 批量：`--batch rows.json` 每行出一个文件，`--batch-concurrency`（默认 1，因为单次渲染本身已并行）、`--batch-fail-fast`、`--json`（批量时只输出一份最终 JSON）；
- 原图最多约 composition 尺寸的 2 倍；减少大面积 blur、backdrop-filter、阴影和巨大纹理。

### 10.4 HDR

- `--hdr` 强制 HDR，`--sdr` 强制 SDR，默认根据源的 BT.2020 + PQ/HLG metadata 自动决定；
- HDR 输出只支持 MP4，使用 H.265 10-bit BT.2020；
- SDR DOM overlay 会转换进 HDR 色域；
- 用 ffprobe 检查 `color_primaries=bt2020`、`color_transfer=smpte2084` 或 HLG；
- 4K supersampling 当前不与 HDR 组合。

### 10.5 Hosted Cloud

```bash
npx hyperframes auth login
npx hyperframes cloud render
npx hyperframes cloud list
npx hyperframes cloud get <render_id>
npx hyperframes cloud delete <render_id>
```

上传接近 200 MB 时先：

```bash
npx hyperframes cloud render --dry-run --json
```

用 `.hyperframesignore` 排除可再生成的 renders、snapshots 等；不要仅因素材大就忽略真正被 composition 引用的资源。可用 asset id 重复渲染不同变量，避免重复上传；fire-and-forget 支持 webhook，重试要复用已有 render/asset 信息，避免重复计费或重复作业。

### 10.6 AWS Lambda / GCP Cloud Run

- Lambda：`deploy` → 可选 `sites create` 内容寻址上传 → `render` / `render-batch` → `progress` → 不再使用时 `destroy`；
- Cloud Run：部署 render image 与 workflow，再 `sites create`、`render` / `render-batch`、`progress`；
- Lambda 适合必须掌握 AWS 账户、IAM、S3、Step Functions 的团队；
- Cloud Run 适合 GCP ownership，并以 Cloud Workflows 管理分布式任务；
- 模板变量适合批量个性化，分布式调用的 execution input 有大小限制，大资产使用 URL，不用 base64 塞进变量。

**Plan v2（0.7.72–0.7.76）。** 分布式渲染的任务契约换成了带版本号的 Plan v2：产物内容寻址、带完整性校验，publisher 直接把结果流式写入 S3 / GCS（0.7.73），稀疏分片会重建视频目录骨架（0.7.76），抽取缓存哨兵与部分色彩元数据也已正确处理（0.7.74）。捕获侧现在会先探测 `BeginFrame` 支持、不支持时安全回退截图捕获，GCP 捕获遵循有效的 `BeginFrame` 边界。这些都是引擎内部行为，不需要改 composition；但如果你还在用旧版本 CLI 驱动新部署，先跑 `upgrade --check` 而不是猜。

---

## 11. CLI 速查

### 创建与资产

```text
init, add, catalog, capture, compositions, figma,
transcribe, tts, remove-background, skills
```

### 诊断与检查

```text
lint, check, snapshot, media-treatment, compare, grade-compare,
beats, keyframes, doctor, browser, info, benchmark
```

`media-treatment` 是 `0.7.72` 新增的顶层命令：发现 / 分析 / 应用 / 清除确定性媒体处理，详见 5.9。

`validate`、`inspect`、`layout` 是**弃用别名**：仍能运行，会在 stderr 打弃用提示，`--json` 里标 `_meta.deprecated: true`。对应关系是 `validate`（runtime + 对比度）→ `check`（对比度已升级为带修复建议的 gating error）；`inspect` / `layout`（布局扫描 + motion sidecar）→ `check`（参数同名：`--samples`、`--at`、`--at-transitions`、`--tolerance`、`--strict`）。脚手架项目的 `npm run check` 已经指向 `check`。

### 预览、播放、渲染、分发

```text
preview, play, present, render, publish,
cloud, lambda, cloudrun, auth
```

### 维护

```text
upgrade, docs, telemetry, feedback
```

Agent/CI 默认优先 `--json`。`preview`、`play`、server-mode render 不一定提供普通 JSON，但 preview 的 selection/context 查询例外。一个验证循环可复用同一个 `HYPERFRAMES_RUN_ID`。

---

## 12. 包与编程接口

| 包 | 职责 | 何时直接用 |
|---|---|---|
| `@hyperframes/core` | types、HTML、runtime、compiler | 底层 composition 工具 |
| `@hyperframes/parsers` | HTML/GSAP AST、hf-id、spring、slideshow parser | 只要解析与重写，不要完整 core |
| `@hyperframes/lint` | 独立 linter | 集成自定义 CI |
| `@hyperframes/sdk` | headless query/mutate/patch/undo/persist | Agent 或自定义编辑器结构化修改 |
| `@hyperframes/engine` | Chrome BeginFrame seek capture | 自建帧捕获流水线 |
| `@hyperframes/producer` | capture + encode + audio mix + server | Node 后端程序化渲染 |
| `@hyperframes/player` | `<hyperframes-player>` web component | 网页嵌入 composition |
| `@hyperframes/studio` | React 编辑器、timeline、preview | 自定义 Studio UI |
| `@hyperframes/studio-server` | Hono preview/edit backend | 把 Studio 后端嵌入自己的服务 |
| `@hyperframes/shader-transitions` | WebGL scene transitions | 自定义 shader 过渡 |
| `@hyperframes/aws-lambda` | Lambda / Step Functions | 自管 AWS 分布式渲染 |
| `@hyperframes/gcp-cloud-run` | Cloud Run / Workflows | 自管 GCP 分布式渲染 |

### 12.1 SDK 的 Agent 心智模型

- 所有编辑目标都是稳定 `data-hf-id`；
- typed method 是 `dispatch()` 的语法糖；
- 每个变更产生 RFC 6902 forward/inverse patches；
- standalone mode 由 SDK 管 history/autosave；embedded override mode 只存模板差量；
- persistence 与 preview 通过 adapter 解耦；
- 子 composition 元素用 scoped id，例如 `hf-HOST/hf-LEAF`。

```ts
import { openComposition } from "@hyperframes/sdk";

const comp = await openComposition(html);
const [id] = comp.find({ text: "Old headline" });
if (id) {
  comp.batch(() => {
    comp.setText(id, "New headline");
    comp.setStyle(id, { color: "#FFD60A", fontSize: "96px" });
    comp.setTiming(id, { start: 1, duration: 3 });
  });
}
const updated = comp.serialize();
comp.dispose();
```

SDK 是编辑层，不负责渲染；渲染用 CLI 或 producer。

---

## 13. `hyperframes-launches` 生产项目地图

该仓库当前含 16 个 standalone 项目。它们展示真实发布流程，不是最小规范样例。

| 项目 | 最值得学习的内容 |
|---|---|
| `HF-heygen-stripe` | 对齐 After Effects 金标、A-roll/VO 同源 lip sync、连续背景硬切、音频拼接 afade、4K 对比与 handoff |
| `claude-paper-launch` | 长叙事 UI、密集 typing/click SFX、frame.md 级设计系统、聊天内容与声音同步 |
| `cloud-render-launch` | 持久聊天 UI、多 scene 同一界面状态、seek-safe DOM、Lottie、并行 worker 叙事 |
| `figma-launch` | 1:1 产品发布、背景视频与 scene composition 混合、Figma 资产和产品画面 |
| `frame-md-launch-storyboard` | DESIGN / frame vocabulary、10-beat 叙事、从视觉系统到分镜 |
| `hyperframes-launch` | CSS、GSAP、Lottie、shader、Three.js、音乐、SFX、footage 的全能力展示 |
| `inspector-launch` | 大型单文件项目、Inspector 功能叙事、把旧片头移植进新 master |
| `k3-promo` | 16.47 秒单文件 monolithic 高密度 promo |
| `pr-to-video-launch` | PR/代码变更的 opener→problem→features→CTA 结构 |
| `sfx-music-launch` | 无旁白音效/音乐产品叙事、音频 cue map、seam grammar |
| `spacex-launch` | 品牌皮肤替换、复用 Claude Paper composition、声音与 UI 叙事 |
| `texture-launch-video` | 单文件 texture-mask typography、shader 背景、重 VFX |
| `timeline-launch` | 音频驱动 timing、持久聊天、Studio screen recording、matched motion seam |
| `variables-launch` | 变量产品故事、hook variants、9:16 UGC、text-behind-subject |
| `vfx-heygen-combined` | 合并两个独立工程、WebGL/Three.js/portal、同方向速度转场 |
| `website-to-hyperframes` | 网站捕获到成片、agent UI、11 段 capability reel、逐句 VO/SFX 编排 |

### 13.1 从这些项目提炼出的生产规律

1. 根 `index.html` 最适合做音频、媒体、scene slots 与 seam；复杂 motion 留在子 composition。
2. 连续界面不要在每个 scene 重建成不同坐标。若同一 chat/UI 状态跨 cut，合并 composition 或确保前一终帧与下一初帧由同一布局公式生成。
3. 同背景场景简单 crossfade 容易在中点变暗；连续背景可对齐 source time 后硬切，只换前景文字。不同视觉世界才用 crossfade 或 matched-motion transition。
4. 过渡的两边必须一起设计：方向、位移、速度、blur 和 end/start pose 要匹配。不要只修一边。
5. 字幕、lower third、music、SFX 应是独立轨道；音频总体贯穿视觉 cuts。
6. 真实词时间胜过估算。Storyboard 的 beat time 在 VO 生成后要回填。
7. Contact sheet 对长片比逐张查看更经济，也更容易发现节奏、空帧、构图漂移和字体失真。
8. Handoff 要记录“用户喜欢什么、哪些不能回退、已验证命令、已知 warning、下一任务”，而不只是文件列表。
9. 大型单文件能工作，但 port、合并和长期维护成本明显更高。第三个清晰 cut 前优先模块化。
10. 历史项目里关于 duration padding、媒体 class、freeze frame、父子 selector 的具体写法可能过时；迁移时用当前技能合同重写，不照抄。

### 13.2 Launch 案例 Few-shot 效果配方库

本节把 launch 仓库里的成片效果提炼成可复用答案。它不是历史源码的逐字副本，而是按当前合同重写后的 few-shot：Agent 应复制其结构、时间关系和参数组织方式，再替换内容与视觉语言。

#### 13.2.1 使用协议

1. 先从下表选“效果意图”，再复制对应配方；不要因为某个案例视觉相似就复制整个项目。
2. 所有片段默认放在已经合法的 composition 中；完整 wrapper 仍按 5.1 节创建。
3. 把 `fx-*` 前缀换成当前 composition 的唯一前缀；注册 key 必须等于 `data-composition-id`。
4. 所有 timed DOM 预先写入文档，不在 timeline callback 中临时创建或删除。
5. 片段中的数字是参考节奏，不是固定模板。先按 VO/音乐词点换算时间，再调 duration 与 stagger。
6. 案例若使用了旧式 `width/top/left/filter/display/visibility` 动画，本节会改成 `transform/opacity/color/borderRadius` 等当前安全属性。
7. 每次复制后至少运行 `hyperframes lint`、`hyperframes check`，并在关键时刻 snapshot。

下方 JS 片段中的 `root` 指当前 composition 根。为方便单独阅读，部分片段重复写了 `const tl = ...`；真正合并时同一 composition 只保留一支 `tl`，按“查询 root → 创建 tl → 加入所选 tween → 注册”的顺序组织：

```js
const compositionId = 'replace-with-your-composition-id';
const root = document.querySelector(`[data-composition-id="${compositionId}"]`);
const tl = gsap.timeline({ paused:true });

// 把所选配方的 tween 加到这一支 tl 上。

window.__timelines = window.__timelines || {};
window.__timelines[compositionId] = tl;
```

| 想要的效果 | 优先抄用 | 主要灵感来源 |
|---|---|---|
| 大字逐词进出、跟旁白卡点 | F01 | `timeline-launch/act0-intro-bell`、`cloud-render-launch/textbeat` |
| 一行文案里不断换动词 | F02 | `HF-heygen-stripe/rotary`、`variables-launch/scene-01` |
| 终端打字、提示词输入 | F03 | `HF-heygen-stripe/terminal`、`variables-launch/scene-05` |
| 鼠标飞入、点击、界面反馈 | F04 | `cloud-render-launch/opener`、`HF-heygen-stripe/commands` |
| 聊天消息持续堆叠 | F05 | `timeline-launch/act2-merged-chat`、`cloud-render-launch/responds` |
| 多任务并行渲染、进度完成 | F06 | `cloud-render-launch/fleet`、`variables-launch/scene-08` |
| 视频/案例卡片矩阵展开 | F07 | `variables-launch/scene-06`、`cloud-render-launch/payoff` |
| 代码或变量值发生变化 | F08 | `variables-launch/scene-04`、`pr-to-video-launch/feature-code` |
| 全屏界面收成悬浮窗口 | F09 | `cloud-render-launch/opener`、`finished` |
| 流程线、轨迹、连接关系 | F10 | `hyperframes-launch/engine`、`frame-md/scene-05-ui-flow` |
| 纹理填充标题 | F11 | `texture-launch-video` |
| 视频在设备框/产品框中播放 | F12 | `figma-launch`、`timeline-launch/act4-video` |
| 动作同时有 click/pop/whoosh | F13 | `sfx-music-launch`、`pr-to-video-launch` |
| Canvas/WebGL 随时间确定性渲染 | F14 | `hyperframes-launch/flex-shader`、`vfx-heygen-combined` |
| Logo/CTA 结束卡 | F15 | `timeline-launch/act6-logo`、`website-to-hyperframes/act-4-end-card` |
| 硬切、方向接力、zoom-through | F16 | `HF-heygen-stripe`、`vfx-heygen-combined` |

#### F01｜逐词 Kinetic Typography

**效果意图：** 让关键词按语音逐个落位，停留后成组离场。适合 hook、价值主张和章节标题。

**DOM/CSS：**

```html
<div class="fx-kinetic clip" data-start="0" data-duration="3.2" data-track-index="10">
  <span class="fx-word">Build.</span>
  <span class="fx-word fx-accent">Preview.</span>
  <span class="fx-word">Render.</span>
</div>
<style>
  .fx-kinetic { position:absolute; inset:0; display:flex; align-items:center;
    justify-content:center; gap:48px; overflow:hidden; }
  .fx-word { display:inline-block; font-size:132px; font-weight:800; opacity:0;
    will-change:transform,opacity; }
  .fx-accent { color:#35c838; }
</style>
```

**Timeline：**

```js
const words = root.querySelectorAll('.fx-word');
const tl = gsap.timeline({ paused:true });
tl.fromTo(words,
  { x:82, opacity:0 },
  { x:0, opacity:1, duration:.32, stagger:.055, ease:'power4.out' }, 0.12);
tl.to(root.querySelector('.fx-accent'),
  { scale:1.04, duration:.28, yoyo:true, repeat:1, ease:'power2.inOut' }, 1.15);
tl.to(words,
  { y:180, opacity:0, duration:.38, stagger:.05, ease:'power3.in' }, 2.45);
```

**可调参数：** `x: 50–100` 决定冲入力度；`stagger: .04–.09` 决定语速；强调词可用颜色和一次有限 pulse。若每个词有精确词点，不用 stagger，逐条把 tween 放到对应绝对时间。

**不要抄错：** section 本身不要先被 `gsap.set(...opacity:0)` 永久隐藏；timed 外壳由 HyperFrames 管可见性，内部词才由 GSAP 管状态。

原案例：[act0-intro-bell.html](https://github.com/heygen-com/hyperframes-launches/blob/main/timeline-launch/compositions/act0-intro-bell.html)、[textbeat.html](https://github.com/heygen-com/hyperframes-launches/blob/main/cloud-render-launch/compositions/textbeat.html)

#### F02｜3D 动词轮 / Rotary Word Dial

**效果意图：** 固定句式中只替换一个高价值动词，例如 “Agent discovers / provisions / generates / pays”。

```html
<div class="fx-dial-row">
  <span>The agent</span>
  <div class="fx-dial"><div class="fx-axis"><div class="fx-cylinder">
    <span style="--i:0">discovers</span><span style="--i:1">provisions</span>
    <span style="--i:2">generates</span><span style="--i:3">pays</span>
  </div></div></div>
</div>
<style>
  .fx-dial-row { position:absolute; inset:0; display:flex; align-items:center;
    justify-content:center; gap:28px; font-size:112px; font-weight:800; }
  .fx-dial { width:620px; height:220px; perspective:900px; overflow:hidden;
    -webkit-mask-image:linear-gradient(transparent,#000 28%,#000 72%,transparent); }
  .fx-axis { position:absolute; inset:0; transform:translateZ(-260px);
    transform-style:preserve-3d; }
  .fx-cylinder { position:absolute; inset:0; transform-style:preserve-3d; }
  .fx-cylinder span { --step:30deg; position:absolute; inset:50% 0 auto;
    text-align:center; color:#35c838; transform:translateY(-50%)
    rotateX(calc(var(--i) * -1 * var(--step))) translateZ(260px); }
</style>
<script>
  const cylinder = root.querySelector('.fx-cylinder');
  const tl = gsap.timeline({ paused:true });
  tl.fromTo(cylinder, { rotationX:0 }, { rotationX:30, duration:.35, ease:'power3.inOut' }, 1.12)
    .to(cylinder, { rotationX:60, duration:.35, ease:'power3.inOut' }, 1.87)
    .to(cylinder, { rotationX:90, duration:.35, ease:'power3.inOut' }, 2.79);
</script>
```

**可调参数：** `step` 与 `translateZ` 必须配套；每次落点对齐动词的 spoken onset。词宽差异很大时，设计阶段测出最大宽度并写成常量，不在 tween 过程中测布局。

原案例：[rotary.html](https://github.com/heygen-com/hyperframes-launches/blob/main/HF-heygen-stripe/compositions/rotary.html)、[scene-01.html](https://github.com/heygen-com/hyperframes-launches/blob/main/variables-launch/compositions/scene-01.html)

#### F03｜可 Seek 的打字机

**效果意图：** 在 terminal、composer 或 code block 中逐字显示。最稳妥的做法是预建字符节点，再控制 `opacity`；不要依赖真实键盘事件。

```html
<div class="fx-command" aria-label="hyperframes render">
  <span class="fx-char">h</span><span class="fx-char">y</span><span class="fx-char">p</span><!-- 继续预建 -->
  <span class="fx-caret"></span>
</div>
<style>
  .fx-command { font:600 34px/1.4 ui-monospace,monospace; }
  .fx-char { opacity:0; }
  .fx-caret { display:inline-block; width:4px; height:1em; background:currentColor;
    vertical-align:-.12em; }
</style>
<script>
  const chars = root.querySelectorAll('.fx-char');
  const caret = root.querySelector('.fx-caret');
  const tl = gsap.timeline({ paused:true });
  tl.set(chars, { opacity:0 }, 0)
    .to(chars, { opacity:1, duration:.01, stagger:.045, ease:'none' }, .25)
    .to(caret, { opacity:0, duration:.18, repeat:5, yoyo:true, ease:'steps(1)' }, .25)
    .to(caret, { opacity:0, duration:.01 }, 1.8);
</script>
```

Agent 可以在构建期用脚本把字符串拆成 span，但最终 HTML 中应已经存在这些 span。长文本也可 tween 一个数值代理，并在 `onUpdate` 中用 `Math.round(progress)` 重算 `textContent`；回调必须只依赖当前 tween progress，不能依赖累积状态。

原案例：[terminal.html](https://github.com/heygen-com/hyperframes-launches/blob/main/HF-heygen-stripe/compositions/terminal.html)、[scene-05.html](https://github.com/heygen-com/hyperframes-launches/blob/main/variables-launch/compositions/scene-05.html)

#### F04｜光标飞入、点击与界面反馈

**效果意图：** 把“Agent 操作了产品”视觉化。光标先从画外进入，点击时光标和目标同时压缩，再恢复。

```js
const cursor = root.querySelector('.fx-cursor');
const target = root.querySelector('.fx-target');
const tl = gsap.timeline({ paused:true });

tl.fromTo(cursor,
  { x:520, y:360, opacity:0, rotation:-6 },
  { x:0, y:0, opacity:1, rotation:0, duration:.62, ease:'power3.out' }, .30);
tl.to(cursor, { scale:.82, duration:.09, ease:'power2.in', transformOrigin:'20% 15%' }, .96);
tl.to(target, { scale:.96, backgroundColor:'#d97757', duration:.09, ease:'power2.in' }, .96);
tl.to([cursor,target], { scale:1, duration:.16, ease:'power2.out' }, 1.05);
tl.to(cursor, { opacity:0, duration:.22 }, 1.35);
```

**对位规则：** 先在 1920×1080 设计坐标中算好光标终点，把 cursor SVG 的尖端而非外框中心对到按钮；SFX 的 `data-start` 放在压缩开始的同一时刻。

原案例：[opener.html](https://github.com/heygen-com/hyperframes-launches/blob/main/cloud-render-launch/compositions/opener.html)、[commands.html](https://github.com/heygen-com/hyperframes-launches/blob/main/HF-heygen-stripe/compositions/commands.html)

#### F05｜持久聊天栈

**效果意图：** 多轮 prompt/reply 从底部持续堆叠，旧消息上移和淡出；同一产品 UI 不因 scene cut 跳变。

```html
<div class="fx-thread">
  <div class="fx-msg fx-old">Previous request</div>
  <div class="fx-msg fx-user">Make the timing earlier.</div>
  <div class="fx-msg fx-reply">Done.</div>
</div>
<style>
  .fx-thread { position:absolute; left:510px; bottom:180px; width:900px; }
  .fx-msg { margin-top:18px; opacity:0; will-change:transform,opacity; }
  .fx-old { opacity:1; }
</style>
<script>
  const stack = root.querySelector('.fx-thread');
  const old = root.querySelector('.fx-old');
  const user = root.querySelector('.fx-user');
  const reply = root.querySelector('.fx-reply');
  const tl = gsap.timeline({ paused:true });
  tl.fromTo(user, { y:18, opacity:0 }, { y:0, opacity:1, duration:.35, ease:'power3.out' }, .25)
    .to(stack, { y:-92, duration:.48, ease:'power3.out' }, .80)
    .fromTo(reply, { y:12, opacity:0 }, { y:0, opacity:1, duration:.35, ease:'power3.out' }, .88)
    .to(old, { opacity:0, duration:.35 }, .88);
</script>
```

**关键约束：** 所有消息预建；不要在 `tl.add(() => appendChild(...))` 中改变 DOM。跨 scene 继续同一聊天时，优先合并为一支 composition；必须拆分时，前一终帧和后一初帧使用同一组坐标与消息内容。

原案例：[act2-merged-chat.html](https://github.com/heygen-com/hyperframes-launches/blob/main/timeline-launch/compositions/act2-merged-chat.html)、[responds.html](https://github.com/heygen-com/hyperframes-launches/blob/main/cloud-render-launch/compositions/responds.html)

#### F06｜并行任务 / Render Fleet

**效果意图：** 多条任务依次出现，进度线从 0 到满，完成状态随后显示。适合 cloud render、batch generation、agent task list。

```html
<div class="fx-job"><span>Worker 01</span><i></i><b>✓ done</b></div>
<div class="fx-job"><span>Worker 02</span><i></i><b>✓ done</b></div>
<div class="fx-job"><span>Worker 03</span><i></i><b>✓ done</b></div>
<style>
  .fx-job { display:grid; grid-template-columns:180px 1fr 120px; gap:20px;
    align-items:center; opacity:0; }
  .fx-job i { height:14px; border-radius:99px; background:#35c838;
    transform:scaleX(0); transform-origin:left center; }
  .fx-job b { opacity:0; color:#35c838; }
</style>
<script>
  const jobs = [...root.querySelectorAll('.fx-job')];
  const tl = gsap.timeline({ paused:true });
  jobs.forEach((job,i) => {
    const t = .25 + i*.24;
    tl.fromTo(job, { x:-14, opacity:0 }, { x:0, opacity:1, duration:.28 }, t)
      .to(job.querySelector('i'), { scaleX:1, duration:.65+i*.08, ease:'power1.out' }, t+.12)
      .to(job.querySelector('b'), { opacity:1, duration:.2 }, t+.77+i*.08);
  });
</script>
```

这里以 `scaleX` 替代历史案例中的 `width: 0% → 100%`，视觉一致但不触发布局动画。

原案例：[fleet.html](https://github.com/heygen-com/hyperframes-launches/blob/main/cloud-render-launch/compositions/fleet.html)、[scene-08.html](https://github.com/heygen-com/hyperframes-launches/blob/main/variables-launch/compositions/scene-08.html)

#### F07｜卡片矩阵 / Capability Reel

**效果意图：** 一次展现多个案例、hook 或生成结果。中卡先立住，上下/左右卡随后扇出。

```js
const center = root.querySelector('.fx-card-center');
const top = root.querySelectorAll('.fx-card-top');
const bottom = root.querySelectorAll('.fx-card-bottom');
const all = root.querySelectorAll('.fx-card');
const tl = gsap.timeline({ paused:true });

tl.fromTo(center, { scale:.78, opacity:0 },
  { scale:1, opacity:1, duration:.48, ease:'expo.out' }, .05);
tl.fromTo(top, { y:-180, opacity:0 },
  { y:0, opacity:1, duration:.5, stagger:.06, ease:'power3.out' }, .42);
tl.fromTo(bottom, { y:180, opacity:0 },
  { y:0, opacity:1, duration:.5, stagger:.06, ease:'power3.out' }, .50);
tl.to(all, { scale:1.025, duration:.7, stagger:.025, yoyo:true, repeat:1, ease:'sine.inOut' }, 1.45);
```

**媒体注意（0.7.71+ 修订）：** `<video>` 现在可以嵌在卡片结构里，运行时照样发现并 seek。唯一不能做的是把它塞进**带时间的** wrapper——`.fx-card` 不要带 `data-start` / `data-duration` / `class="clip"`。若卡片壳本身必须计时，仍按老写法把 `<video>` 和卡片壳做成兄弟节点，用完全相同的静态坐标和同一组 transform tween。

原案例：[scene-06.html](https://github.com/heygen-com/hyperframes-launches/blob/main/variables-launch/compositions/scene-06.html)、[payoff.html](https://github.com/heygen-com/hyperframes-launches/blob/main/cloud-render-launch/compositions/payoff.html)

#### F08｜代码 Diff / 变量替换

**效果意图：** 让旧值上滑消失，新值从下方进入，并在最后揭示对应视觉结果。

```html
<span class="fx-swap"><code class="fx-old-value">duration: 8</code><code class="fx-new-value">duration: 3</code></span>
<style>
  .fx-swap { position:relative; display:inline-block; width:260px; height:44px; overflow:hidden; }
  .fx-swap code { position:absolute; inset:0; }
  .fx-new-value { color:#35c838; opacity:0; transform:translateY(12px); }
</style>
<script>
  const swaps = root.querySelectorAll('.fx-swap');
  const tl = gsap.timeline({ paused:true });
  swaps.forEach((swap,i) => {
    const t = .55 + i*.16;
    tl.to(swap.querySelector('.fx-old-value'),
      { y:-12, opacity:0, duration:.18, ease:'power2.in' }, t)
      .to(swap.querySelector('.fx-new-value'),
      { y:0, opacity:1, duration:.22, ease:'power2.out' }, t+.09);
  });
</script>
```

变化行可用固定背景色表示 added/removed，但不要逐帧改变 DOM 内容；长 diff 先在 HTML 中准备好两层状态。

原案例：[scene-04.html](https://github.com/heygen-com/hyperframes-launches/blob/main/variables-launch/compositions/scene-04.html)、[feature-code.html](https://github.com/heygen-com/hyperframes-launches/blob/main/pr-to-video-launch/compositions/feature-code.html)

#### F09｜全屏产品界面收成悬浮窗口

**效果意图：** 从沉浸式产品画面退到“产品运行在一台窗口里”的解释性镜头。不要 tween `width/height`，用预设尺寸和 scale。

```html
<div class="fx-window"><div class="fx-titlebar">•••</div><!-- UI 内容 --></div>
<style>
  .fx-window { position:absolute; left:160px; top:90px; width:1600px; height:900px;
    border-radius:26px; overflow:hidden; background:#fff; transform-origin:center; }
  .fx-titlebar { opacity:0; }
</style>
<script>
  const win = root.querySelector('.fx-window');
  const bar = root.querySelector('.fx-titlebar');
  const tl = gsap.timeline({ paused:true });
  // 1600×900 放大 1.2 后覆盖 1920×1080。
  tl.fromTo(win,
    { scale:1.2, borderRadius:0 },
    { scale:1, borderRadius:26, duration:.6, ease:'power3.inOut' }, 0)
    .to(bar, { opacity:1, duration:.3, ease:'power2.out' }, .28);
</script>
```

若要反向从窗口进入全屏，只交换 from/to。全屏前后若有媒体，确保媒体层和窗口壳使用同一 transform，不改变 video DOM 层级。

原案例：[opener.html](https://github.com/heygen-com/hyperframes-launches/blob/main/cloud-render-launch/compositions/opener.html)、[finished.html](https://github.com/heygen-com/hyperframes-launches/blob/main/cloud-render-launch/compositions/finished.html)

#### F10｜SVG 路径绘制与流程节点

**效果意图：** 展示 agent 流程、数据路径或 “source → composition → render”。

```html
<svg class="fx-flow" viewBox="0 0 1200 400">
  <defs><clipPath id="fx-flow-reveal">
    <rect class="fx-reveal" width="1200" height="400" />
  </clipPath></defs>
  <path class="fx-path" clip-path="url(#fx-flow-reveal)"
    d="M80 300 C340 40 760 360 1120 100" />
  <circle class="fx-dot" cx="80" cy="300" r="12" />
  <circle class="fx-dot" cx="600" cy="205" r="12" />
  <circle class="fx-dot" cx="1120" cy="100" r="12" />
</svg>
<style>
  .fx-path { fill:none; stroke:#35c838; stroke-width:8; stroke-linecap:round;
  }
  .fx-reveal { transform:scaleX(0); transform-origin:left center; transform-box:fill-box; }
  .fx-dot { fill:#fff; stroke:#35c838; stroke-width:6; opacity:0; }
</style>
<script>
  const tl = gsap.timeline({ paused:true });
  tl.to(root.querySelector('.fx-reveal'),
    { scaleX:1, duration:1.15, ease:'power2.inOut' }, .2)
    .fromTo(root.querySelectorAll('.fx-dot'),
    { scale:.4, opacity:0 },
    { scale:1, opacity:1, duration:.24, stagger:.45, ease:'back.out(1.5)' }, .2);
</script>
```

历史案例常用 `strokeDashoffset` 画线；当前安全版本改为用 `scaleX` 扩展 SVG clipPath，路径本身不变形，也不越过动画属性白名单。没有 MotionPath 插件时，不要假装圆点精确沿贝塞尔路径运动；要么只画线和点亮节点，要么在设计阶段采样路径并生成确定性 keyframes。

原案例：[engine.html](https://github.com/heygen-com/hyperframes-launches/blob/main/hyperframes-launch/compositions/engine.html)、[scene-05-ui-flow.html](https://github.com/heygen-com/hyperframes-launches/blob/main/frame-md-launch-storyboard/compositions/scene-05-ui-flow.html)

#### F11｜纹理填充文字

**效果意图：** 把金属、纸张、石材等 texture 填进大标题，让 typography 自带材质感。

```html
<h1 class="fx-texture-word">TEXTURE</h1>
<style>
  .fx-texture-word { font-size:210px; font-weight:900; color:transparent;
    background-image:linear-gradient(rgba(255,255,255,.12),rgba(0,0,0,.16)),
      url('assets/masks/diamond-plate.png');
    background-size:100% 100%, 166% 166%; background-position:center,42% 50%;
    background-clip:text; -webkit-background-clip:text; -webkit-text-fill-color:transparent;
    will-change:transform,opacity; }
</style>
<script>
  const word = root.querySelector('.fx-texture-word');
  const tl = gsap.timeline({ paused:true });
  tl.fromTo(word, { scale:.72, y:48, opacity:0 },
    { scale:1, y:0, opacity:1, duration:.58, ease:'expo.out' }, .1)
    .to(word, { scale:1.035, duration:.7, yoyo:true, repeat:1, ease:'sine.inOut' }, .8);
</script>
```

纹理的位置、尺寸和对比度应按每个单词单独设定；把 texture 当填充，不要再叠无意义的霓虹 glow。资产路径必须本地可渲染。

原案例：[texture-launch-video/index.html](https://github.com/heygen-com/hyperframes-launches/blob/main/texture-launch-video/index.html)

#### F12｜设备框 / 产品框中的视频

**效果意图：** 展示 screen recording。下面用「媒体与设备壳做兄弟节点」的写法：它在任何版本都成立，也让屏幕与外框共享同一套坐标和 transform。（0.7.71+ 起，把 `<video>` 嵌进不计时的设备壳内部同样合法。）

```html
<!-- 屏幕与外框互为兄弟节点，共享同一套静态坐标 -->
<video class="fx-screen" src="assets/demo.mp4" muted playsinline
  data-start="0" data-duration="4" data-media-start="1.5" data-track-index="1"></video>
<div class="fx-device-shell clip" data-start="0" data-duration="4" data-track-index="2"></div>
<style>
  .fx-screen,.fx-device-shell { position:absolute; left:420px; top:120px;
    width:1080px; height:810px; border-radius:36px; transform-origin:center; }
  .fx-screen { object-fit:cover; }
  .fx-device-shell { border:18px solid #151515; box-shadow:0 36px 90px rgba(0,0,0,.3); }
</style>
<script>
  const pair = root.querySelectorAll('.fx-screen,.fx-device-shell');
  const tl = gsap.timeline({ paused:true });
  tl.fromTo(pair, { y:90, scale:.88, opacity:0 },
    { y:0, scale:1, opacity:1, duration:.62, ease:'expo.out' }, .12)
    .to(pair, { scale:1.035, duration:1.2, ease:'sine.inOut' }, 1.5);
</script>
```

不要用 JS 调 `video.play()`、`currentTime` 或循环；由 HyperFrames 按 composition time 控制媒体。若要 text-behind-subject，先生成透明/抠像媒体资产，并让背景、文字、前景主体分别占独立 z 层。

原案例：[figma-launch/index.html](https://github.com/heygen-com/hyperframes-launches/blob/main/figma-launch/index.html)、[act4-video.html](https://github.com/heygen-com/hyperframes-launches/blob/main/timeline-launch/compositions/act4-video.html)

#### F13｜SFX 卡点轨道

**效果意图：** 让 whoosh 对齐进入，click 对齐按压，pop 对齐卡片出现，chime 对齐完成态。

```html
<!-- audio 直接放在 composition root 下，时间是局部 composition 时间 -->
<audio src="assets/sfx/whoosh.mp3" data-start="0.10" data-duration="0.55"
  data-volume="0.8" data-track-index="60"></audio>
<audio src="assets/sfx/click.mp3" data-start="0.96" data-duration="0.22"
  data-volume="1" data-track-index="61"></audio>
<audio src="assets/sfx/chime.mp3" data-start="1.82" data-duration="0.70"
  data-volume="0.65" data-track-index="62"></audio>
```

**语法：** whoosh 通常从视觉移动前 1–3 帧开始；click 与压缩第一帧同点；pop 与元素从不可见变可见同点；chime 与 `done` 或成功色出现同点。多个 SFX 使用不同 track；整片 music/VO 放根层长轨，不在 scene JS 中播放。

原案例：[sfx-music-launch/index.html](https://github.com/heygen-com/hyperframes-launches/blob/main/sfx-music-launch/index.html)、[pr-to-video-launch/index.html](https://github.com/heygen-com/hyperframes-launches/blob/main/pr-to-video-launch/index.html)

#### F14｜Canvas / WebGL 的确定性时间适配器

**效果意图：** shader、粒子、3D 或 2D canvas 必须根据 timeline 的当前时间重绘，而不是靠独立 RAF 时钟自由运行。

```js
const state = { t:0 };

function renderAt(t) {
  // 纯函数思路：所有视觉只由 t 和固定常量决定。
  // gl.uniform1f(uTime, t); drawScene();
  // 或 ctx.clearRect(...); drawFrame(ctx, t);
}

renderAt(0);
const tl = gsap.timeline({ paused:true });
tl.to(state, {
  t:4,
  duration:4,
  ease:'none',
  onUpdate:() => renderAt(state.t)
}, 0);
```

**硬规则：** 禁止内部 `requestAnimationFrame`、`Date.now()`、`performance.now()`、未播种随机数、异步网络状态。粒子随机种子和几何常量在初始化时固定；同一个 `t` 必须绘出同一帧。复杂 VFX 优先安装 Catalog block，再按其时间适配器修改。

原案例：[flex-shader.html](https://github.com/heygen-com/hyperframes-launches/blob/main/hyperframes-launch/compositions/flex-shader.html)、[vfx-heygen-combined/index.html](https://github.com/heygen-com/hyperframes-launches/blob/main/vfx-heygen-combined/index.html)

#### F15｜Logo / CTA 结束卡

**效果意图：** 前景退场后 Logo 以一次清晰的 scale settle 出现，随后 CTA 或命令 pill 落位，至少保留 0.8–1.5 秒可读时间。

```js
const oldWorld = root.querySelector('.fx-old-world');
const mark = root.querySelector('.fx-logo');
const cta = root.querySelector('.fx-cta');
const tl = gsap.timeline({ paused:true });

tl.to(oldWorld, { scale:1.16, opacity:0, duration:.34, ease:'power3.in' }, 0)
  .fromTo(mark, { scale:.72, opacity:0 },
    { scale:1, opacity:1, duration:.55, ease:'expo.out' }, .18)
  .fromTo(cta, { y:24, opacity:0 },
    { y:0, opacity:1, duration:.38, ease:'power3.out' }, .60)
  .to(mark, { scale:1.018, duration:.7, yoyo:true, repeat:1, ease:'sine.inOut' }, .85);
```

结束卡不要继续堆新信息。Logo、品牌关系、一个 CTA 足够；若 CTA 是安装命令，使用高对比 monospace pill 并确保停留可截图。停留时长由 composition 的静态 `data-duration` 提供，不添加空 tween 垫时长。

原案例：[act6-logo.html](https://github.com/heygen-com/hyperframes-launches/blob/main/timeline-launch/compositions/act6-logo.html)、[act-4-end-card.html](https://github.com/heygen-com/hyperframes-launches/blob/main/website-to-hyperframes/compositions/act-4-end-card.html)

#### F16｜三种 Scene Seam

**A. 连续背景硬切：** 两个相邻 scene 使用同一个背景视频源，并让各自 `data-media-start` 对齐到同一全局源时间；边界只换前景。不要把两份背景 crossfade，否则中点会变暗。

**B. 方向接力：** 前 scene 的内容向左以 `x:-220, opacity:0` 退出，后 scene 从右侧 `x:220, opacity:0` 进入；时长和 ease 保持相近，观众会把它读作同一次运动。

```js
// 前一 scene 的尾部
tl.to(root.querySelector('.fx-out'),
  { x:-220, opacity:0, duration:.28, ease:'power3.in' }, 2.72);

// 后一 scene 的头部
tl.fromTo(root.querySelector('.fx-in'),
  { x:220, opacity:0 },
  { x:0, opacity:1, duration:.34, ease:'power3.out' }, 0);
```

**C. Zoom-through：** 前景迅速放大并淡出，下一世界从略小或略大 settle 到 1。缩放方向要讲得通：像穿过前景时前层应放大；像镜头退出时前层应缩小。

```js
// 出场
tl.to(outgoing, { scale:1.28, opacity:0, duration:.24, ease:'power3.in' }, 3.1);
// 入场
tl.fromTo(incoming, { scale:.78, opacity:0 },
  { scale:1, opacity:1, duration:.42, ease:'expo.out' }, 0);
```

**验收方式：** 分别 snapshot 边界前 2 帧、边界、边界后 2 帧；检查构图中心、运动方向、速度和背景亮度是否连续。接缝问题要同时修改两边，不只修一个 scene。

原案例：[HF-heygen-stripe/index.html](https://github.com/heygen-com/hyperframes-launches/blob/main/HF-heygen-stripe/index.html)、[vfx-heygen-combined/index.html](https://github.com/heygen-com/hyperframes-launches/blob/main/vfx-heygen-combined/index.html)

#### 13.2.2 Agent 选择配方的决策顺序

面对“做得更有动效”这类模糊要求时，Agent 不应随机叠效果，应按下列顺序决定：

1. **先找叙事动作。** 是“出现”“替换”“完成”“比较”“进入另一个世界”，还是“展示并行规模”？
2. **再选一个主配方。** 出现用 F01/F07；替换用 F02/F08；完成用 F06/F15；交互用 F03/F04/F05；世界切换用 F09/F16。
3. **最多叠一个辅助配方。** 例如 F07 卡片矩阵 + F13 pop SFX；F03 打字 + F04 click；F10 路径 + F06 完成态。
4. **保留视觉呼吸。** 0.3–0.7 秒入场，0.6–1.5 秒阅读，0.25–0.5 秒离场是可靠起点；信息密度高时延长阅读而不是加速所有动画。
5. **用品牌变量替换皮肤，不改 motion grammar。** 先复制结构和时序，再替换字体、颜色、圆角、纹理和资产。
6. **最后才做 VFX。** 普通 DOM/GSAP 已能表达时，不为炫技引入 WebGL；只有材质、粒子、3D 空间本身承担叙事时才用 F14。

#### 13.2.3 Few-shot 组合示例

用户说：“做一个 8 秒的 Agent 产品功能演示，结尾带安装命令。”Agent 可以直接组合：

```text
0.00–1.20  F01：逐词标题 “Ask. Build. Render.”
1.20–3.20  F03：在 composer 中输入任务
3.20–4.00  F04 + F13：cursor 点击，click SFX 同点
4.00–6.10  F06：3 个 worker 并行完成，最后一个 chime
6.10–8.00  F15：Logo + `npx hyperframes create` CTA
接缝       F16-B：标题向左退，composer 从右接力
```

实现后，Agent 必须明确写出：使用了哪些配方、每个配方对应什么叙事动作、关键时间点、替换了哪些品牌变量，以及 lint/check/snapshot 结果。这样 few-shot 是可审计的创作依据，而不是盲目套模板。

---

## 14. 常见故障与排查顺序

### 14.1 元素一直可见

检查可视 timed DOM 是否有 `class="clip"`。video/audio 按当前合同例外。

### 14.2 动画静止

依次检查：

1. timeline 是否同步创建且 paused；
2. `window.__timelines[key]` 是否存在；
3. key、子根 id、host id 是否完全一致；
4. 子文件的 script 是否真的在 `<template>` 内；
5. 是否在 async/callback 中才创建 timeline；
6. 是否在 scene 被挂载前对 `.clip` 做了 page-load `gsap.set()`。

### 14.3 子场景变成左上角小字 / SVG 铺满画布

通常是 `<style>` 在 `<head>`，没有放进 `<template>`；或根用 class 选择器导致 CSS scope 后无法命中。把 style/script/markup 全移入 template，根用 `#root`。

### 14.4 video 黑、白或停帧

- 确保有唯一 `id`（多个文件 inline 后 ID 重复会让 producer 通过 `getElementById` 注入错对象）；
- **没有被 timed wrapper 包裹**——这是当前最常见的真因。嵌套本身没问题，wrapper 带时间才有问题；
- `muted playsinline`；
- 没有直接 tween 尺寸/位置布局属性；
- preview 的 HEVC 问题先检查自动 proxy 与 FFmpeg；
- 驱动它的 timeline 与它的宿主 composition 是否一致（宿主由 `closest("[data-composition-id]")` 决定）；
- 用 `snapshot` 和 draft render 分别判断 DOM mount 与媒体逐帧问题。

注意：`0.7.68` 之前那条“媒体在子 composition 里就一定不会被 seek”的经验**已经过期**，对应的 lint 规则 `media_in_subcomposition` 也已删除。渲染后面板发黑就是真 bug，不是“放错位置”的预期后果——按上面的清单定位，别先去搬 DOM。

### 14.5 render 时长错误

- 新项目显式检查 root `data-duration`；
- 不要在 script 或 variable 中改根时长；
- 检查 scene slot 的 start+duration 是否覆盖全片；
- 检查媒体自然时长和 `data-media-start`；
- 检查无限 repeat；
- 用 `npx hyperframes compositions --json` / `info --json` 查看解析结果。

### 14.6 Preview 卡，但 render 正常

说明单帧 paint 超过 16–33 ms，不必然是时间同步错误。检查：

- 大面积或堆叠 `backdrop-filter`；
- 大 blur/drop-shadow；
- 远超 4K 的图片；
- 大量 shadowed animated elements；
- WebGL texture 尺寸；
- DevTools Performance 中 Composite Layers / Paint / Layout / Script。

### 14.7 Preview 与 render 不同

- 本地字体、Chrome、GPU 路径差异：用 Docker；
- 子 composition mount 问题：用 assembled index snapshot，而不是只预览单 scene；
- 外部 CDN 或网络资产：冻结到本地；
- frame 0 Tailwind flash：保留 readiness promise 或预编译 CSS；
- 依赖 `onUpdate`、累计状态、timer、随机数：改成由当前 time 直接计算。

### 14.8 Check 的 layout warning

先修真实问题，不先加忽略：字体是否加载、父高度是否解析、box 是否越界、text 是否 wrap、装饰 peak 是否预留、场景根是否 full size。只有确认是刻意出血后，才用最小范围 `data-layout-bleed` / `allow-overflow`。

---

## 15. Agent 执行清单

### 15.1 接手旧项目

- [ ] 读项目 `AGENTS.md` / `CLAUDE.md` / `BRIEF.md` / `STORYBOARD.md` / `HANDOFF.md`
- [ ] 识别 monolithic 或 modular
- [ ] 检查 git 状态，保留用户改动
- [ ] 检查 `package.json` pin 与 `hyperframes.json`
- [ ] 跑 upgrade check，不盲升
- [ ] `doctor --json` 判断环境
- [ ] `info --json` / `compositions --json` 建立项目地图
- [ ] 先 snapshot 当前关键帧，留视觉基线
- [ ] 只改请求涉及的场景、时间、变量或资产

### 15.2 新建项目

- [ ] 读 `/hyperframes` 并完成路由
- [ ] 写 `BRIEF.md`
- [ ] 初始化项目并锁定画幅、时长、CLI pin
- [ ] 需要时 capture / Figma import / 素材 staging
- [ ] 写 DESIGN、SCRIPT、STORYBOARD
- [ ] 有旁白先生成 VO 与词时间，再锁 beat durations
- [ ] 一次性安装 registry blocks
- [ ] 静态布局先过，再 motion
- [ ] 模块化场景，index 保持薄
- [ ] `lint` 迭代，最终 `check --snapshots`
- [ ] 关键运动意图写成 `*.motion.json` sidecar，让 `check` 自动验证
- [ ] 子 composition 每个可见中点 snapshot
- [ ] 片中有重要实拍素材时，做一次 media-polish 扫描（`media-treatment --analyze`）；判断“不改”也是合法结论
- [ ] Studio final preview
- [ ] 得到明确批准后 render
- [ ] ffprobe 验证、说明输出路径与版本

### 15.3 Pre-render 红线

- [ ] 所有 id 在 assembled page 唯一
- [ ] 可视 timed DOM 有 `class="clip"`
- [ ] video/audio 没有被 timed wrapper 包住（嵌套本身允许）
- [ ] video `muted playsinline`，声音独立 audio
- [ ] 同轨道无重叠，z-index 明确
- [ ] root duration、各 scene slot 覆盖正确
- [ ] 子 composition 的 template/style/script/id 三件套正确
- [ ] timeline 全部 paused、同步、有限、key 匹配
- [ ] 无 clock、unseeded random、event/scroll state
- [ ] `repeat: -1` 已改成有限次数；若确需保留，根 `data-duration` 显式有限且已在交付说明里写明
- [ ] 旋转元素的 `transformOrigin` / `svgOrigin` 正确，无 `rotation_pivot_drift` / `off_pivot_rotation`
- [ ] 无 render-critical 网络依赖
- [ ] 无 root background 合成风险；使用 full-bleed child
- [ ] `check` 0 findings（含对比度 error 与 motion sidecar 断言），无 `sweep_static`
- [ ] 关键 snapshot 肉眼通过
- [ ] 用户已批准最终 preview

---

## 16. 给 Agent 的推荐提示词模板

```text
使用 /hyperframes 处理这个任务。

目标：
受众：
唯一核心信息：
输入素材/URL/PR/视频/音频：
时长：
画幅：
风格与能量：
旁白/字幕/音乐/SFX：
必须出现：
禁止出现：
参考作品：
交付格式：

请先读取项目状态和现有 handoff；以当前 HyperFrames skills 与 CLI 检查结果为规范，
历史 launch 源码只用于学习生产模式。复杂项目先提交 storyboard 和布局审阅，
构建后运行 check 与关键帧 snapshot，最终 Studio preview 得到批准后再 render。
```

针对直接复用 launch 效果：

```text
使用本手册 13.2 的 Few-shot 配方库完成任务。先说明叙事动作，再选择 1 个主配方，
必要时最多叠加 1 个辅助配方；优先复用 motion grammar，不复制历史项目的整段源码。

本任务选用：F__（主）+ F__（辅，可省略）。
需要替换的品牌变量：字体、颜色、圆角、资产、文案。
需要对齐的时间依据：VO 词点 / music beat / 明确秒数。

请把历史案例规范化为当前 HyperFrames 合同：唯一 ID、媒体不放进 timed wrapper、timed DOM clip、
单支 paused timeline、有限且可 seek、无独立时钟和运行时 DOM 累积。完成后报告使用了哪些
配方、关键时间点、改动文件以及 lint/check/snapshot 结果。
```

针对网站：

```text
用 /hyperframes 把 https://example.com 做成 25 秒 16:9 产品发布片。
核心信息是：……。视觉继承网站品牌，但节奏像 Apple keynote，暗色、高对比、克制。
需要旁白、词级字幕、轻音乐和关键交互 SFX。先 capture，再给我 storyboard board。
```

针对精确修改：

```text
这是已有 HyperFrames 项目。不要重新做 brief 或重建全片。
只修改 compositions/scene-03.html：把标题 entrance 延后 0.4 秒，
改成 power3.out 的 y+opacity fromTo；保持现有文案、布局、轨道、ID 和其他 timing 不变。
修改后 lint、check，并给 03 场景中点 snapshot；不要自动 render。
```

---

## 17. 主要资料入口

- 官网首页与文档：[hyperframes.heygen.com](https://hyperframes.heygen.com/)
- 完整文档索引：[llms.txt](https://hyperframes.heygen.com/llms.txt)
- Quickstart：[Quickstart](https://hyperframes.heygen.com/quickstart)
- Concepts：[Compositions](https://hyperframes.heygen.com/concepts/compositions)、[Data Attributes](https://hyperframes.heygen.com/concepts/data-attributes)、[Variables](https://hyperframes.heygen.com/concepts/variables)、[Determinism](https://hyperframes.heygen.com/concepts/determinism)、[Frame Adapters](https://hyperframes.heygen.com/concepts/frame-adapters)
- Guides：[Pipeline](https://hyperframes.heygen.com/guides/pipeline)、[Prompting](https://hyperframes.heygen.com/guides/prompting)、[Rendering](https://hyperframes.heygen.com/guides/rendering)、[Website to Video](https://hyperframes.heygen.com/guides/website-to-video)、[Color Grading](https://hyperframes.heygen.com/guides/color-grading)（注意：调色页当前落后于运行时，见 0.1）
- 版本动态：[Changelog](https://hyperframes.heygen.com/changelog)、[Weekly Updates](https://hyperframes.heygen.com/weekly-updates)
- CLI：[CLI package](https://hyperframes.heygen.com/packages/cli)
- SDK：[SDK overview](https://hyperframes.heygen.com/sdk/overview)
- Catalog：[Catalog](https://hyperframes.heygen.com/catalog/blocks/data-chart)
- HyperFrames 主仓库：[heygen-com/hyperframes](https://github.com/heygen-com/hyperframes)
- 真实 launch 项目：[heygen-com/hyperframes-launches](https://github.com/heygen-com/hyperframes-launches)

---

## 18. 时效性说明

本手册基于 2026-07-28 的 `0.7.77`。这一版本带来 Studio 时间线的可展开属性轨道、轨道头、精确 keyframe 重定时与嵌套 composition 支持，以及可选的 `proseCoverageFloor` 布局规则。

从 `0.7.68` 到 `0.7.77` 只用了 6 天，发了 9 个版本——**迭代速度就是本手册最大的风险**。两条合同级规则在这 6 天里发生了反转（媒体嵌套、`repeat: -1`），说明“上次是对的”不构成“这次也对”。Agent 每次开始重要制作都应：

```bash
npx hyperframes skills check
npx hyperframes@latest upgrade --project . --check
npx hyperframes docs
```

高价值的核对动作（都很便宜，都比读手册准）：

```bash
npx hyperframes media-treatment --capabilities --json   # 调色 / 处理能力的真相源
npx hyperframes catalog --json                          # Catalog 是在线表面，数量随时变
npx hyperframes check --json                            # 规则集与严重度以实跑为准
```

不要把本手册中的具体版本、Catalog 数量、lint 规则集或历史项目技巧当作永久事实；composition 的当前技能合同、项目 pin 和 CLI 检查结果始终优先。发现手册与实跑冲突时，**信实跑**，然后回来改这份文件。
