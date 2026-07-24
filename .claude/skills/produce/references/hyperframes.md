# 引擎知识包 · HyperFrames（HTML 确定性合成）

> 何时读我：storyboard 有镜头路由到 `hyperframes` 时；compose 阶段全程。
> **要做具体动效（更炫酷/更有动效/像发布片）→ 读 `hyperframes-recipes.md`（F01–F16 few-shot）**：
> 本文件立框架合同（能不能、怎么才不崩），配方库给 motion grammar（用什么表达叙事动作）。
>
> 资料基线：HyperFrames Agent Handbook 2026-07-23（HyperFrames 0.7.68）。
> <!--# 策略@hf-handbook-2026-07-23：版本号/Catalog 数量/launch 技巧会老化；本仓 compose
> 硬规则与 tools/lint.py 永远优先于手册，官网 llms.txt 是细节的活口径。 -->

## 定位

HeyGen 开源（Apache 2.0）的 agent-native 合成框架："写 HTML/CSS/GSAP，渲染视频"。**不产生像素，只做确定性合成**。它是 **MG 动画（motion graphics）/信息图形语言**的主引擎，也是全片叠加层（字幕/角标/数据卡）的宿主——按表达选它，不是按成本选它。

**类型纪律**：全部产出属"幻灯片语法"，**不计入运动占比**——片型承诺只能写 `typography_led` / `data_explainer`，冒充 `motion_led` 是承诺违约。

## 安装与文档

```bash
npx skills add heygen-com/hyperframes   # 8 核心 + 10 工作流技能
```

- 文档索引：hyperframes.heygen.com/llms.txt （细节问题先查这里，别猜 API）
- Playground：hyperframes.dev

## 硬规则（violate = lint 不过 = 禁 render）

1. timeline 必须 `{ paused: true }` 创建并注册到 `window.__timelines[compositionId]`；
2. `<video>` 元素必须 `muted`（声音走独立 audio 轨，混音归 compose 契约管）；
3. 禁 `Math.random` / `Date.now` / `requestAnimationFrame` / 渲染期网络请求——一切必须由帧时钟驱动、可复现；
4. 计时元素必须 `class="clip"` + `data-start` / `data-duration` / `data-track-index`；
5. 资产全部本地文件，禁 CDN；
6. **GSAP 供给纪律**：用 `gsap.timeline()` 就必须**自带在盘的真 `assets/gsap.min.js`**
   （首选，版本无关，golden 全走这条），**禁手搓 `window.gsap` shim**——渲染机 seek 驱动
   会调 `timeScale()`/`invalidate()`/`eventCallback()` 等生命周期方法，手搓 shim 漏一个就
   `[Browser:PAGEERROR] …is not a function`→capture rc=1（`e2e-post-less` 教训）。万不得已
   自包含时，**只准整块抄** `references/gsap-fallback-shim.md`（实现了生命周期全表）。

`npx hyperframes lint` 是现成 G1 硬门：**lint → 过了才 render**。

## composition 合同深水区（不懂这些 → preview 正常但 render 黑/错位/时长错）

### 属性合同

- **根**：`data-composition-id`（必需，与 `window.__timelines[id]` 一致）、`data-width`/`data-height`
  （1920×1080 / 1080×1920 / 1080×1080）、`data-duration`（**强烈建议显式写**，编译期锁定总渲染秒数，
  脚本/变量改无效）；全屏背景放 **full-bleed 子节点**，不放根本身（否则 preview 正常、render 黑帧）。
- **clip**：`id` 全 assembled page 唯一；`data-start`（绝对秒或同 composition 内相对引用）；
  `data-duration`（div/img/子 composition host 必需，video/audio 可用素材固有时长）；`data-track-index` 必需；
  可视 DOM 才加 `class="clip"`（video 不加，audio 不加）。可见窗口**含**结束时刻（`start ≤ t ≤ start+duration`，末帧保持终态）。
- **track ≠ z-index**：`data-track-index` 是"时间车道"（同轨不得时间重叠），视觉前后用 CSS `z-index`；
  惯例 0=底层视频、1+=视觉/overlay、10+=音频；crossfade 两场景必须不同轨。
- **相对时间**：`data-start="intro"` / `"intro - 0.5"` 只在同 composition 内引用，被引用 clip 须有可知时长，
  不可成环，链 ≤3–4 层。

### 子 composition 三条不可违反的跨文件规则（"左上角小字/SVG 铺满"全是踩这里）

1. 运行时**只 clone `<template>` 内**的内容——`<style>`/`<script>`/markup 必须全在 `<template>` 内；
2. host `data-composition-id`、子根 `data-composition-id`、`window.__timelines` 注册 key **三者完全相同**；
3. 子根用 `#root` 样式，**别依赖根自身 class 选择器**（编译器给普通选择器加 scope，根 class 会被改写成命不中的 descendant）。

host `data-duration` 是可见窗口（子 timeline 短则保持末帧，host 窗口短则到点隐藏）。**禁手工 `master.add(child)`**
把子 timeline 嵌进根 timeline——框架独立 seek，手工嵌套=双重 seek。子 composition 内 element id 加 composition 前缀防重复。
入场优先 `fromTo()`（明确两端，减少 seek-back 与 `from()` 初值捕获差异）。

### 媒体合同（黑/白/停帧的头号根因）

- `<video>`/`<audio>` 必须是 **host composition 根的直接子节点**，禁进子 composition `<template>`、禁中间 wrapper 包裹；
- `<video>` 必须 `muted playsinline`；声音走独立 `<audio>`（即使同源文件）；
- **禁** `.play()`/`.pause()`/写 `currentTime`——框架拥有播放与 seek；
- **禁**在 `<video>` 上 tween `width/height/top/left`；用不计时 wrapper，只 tween transform/opacity；
- 子 composition timeline **不能**驱动 host 媒体；host 媒体的 scale/opacity 写在根 timeline，时间用全局秒；
- 入点 `data-media-start`；wrapper/子 composition 源偏移 `data-playback-start`；倍速 `data-playback-rate`（0.1–5）；
- 跨域媒体需 canvas 抽样时加 `crossorigin="anonymous"`；HEVC/ProRes 由 FFmpeg 预解码，preview 不支持时自动生成缓存代理；
- 当前版本支持短视频在长 slot loop 且保尾帧；旧 handoff 的"必须 `tpad` 烘焙 freeze"是旧经验，仅目标版本验证失败才用。
- **本仓 seek 附加**：Seedance 素材挂入前必须密集重编码关键帧（`-g 12 -keyint_min 12 -sc_threshold 0`），否则渲染器 seek 冻帧。

### 变量（批量个性化 / 变体）

声明是数组（`<html data-composition-variables='[{"id":"title","type":"string","default":"Hello"},…]'>`，
类型 string/color/number/boolean/enum），值是对象。优先声明式绑定 `data-var-text` / `data-var-src` /
CSS `var(--accent)`；需要条件/派生时初始化阶段 `window.__hyperframes.getVariables()` 读一次。
优先级：声明默认 < host `data-variable-values` < CLI `--variables`（顶层 CLI 不自动穿透子 composition）。
**变量不能改**：画幅宽高、源 HTML 写死的根总时长、fps/格式/编码/质量；能改：媒体 URL、文字、颜色、普通 clip 时长、color grading。
带声音的 `data-var-src` 要保留真实 fallback `src` 以便音频提取。

### color grading（LUT / 调色 / grain / blur / pixelate 都在这）

视频/图片用 `data-color-grading` 表达 shader grade：`preset`+`intensity`、`adjust`（曝光/对比/饱和/vibrance/
色温/tint/高光/阴影）、`details`（vignette/grain/grainSize）、`effects`（blur/pixelate）、`lut`+强度、`colorSpace`。
字段可引用变量（`"preset":"$gradingPreset"`）。**grade 属媒体 finishing，不代替场景本身的色彩设计**。

### 动画属性白名单 + 确定性禁令（违反 = 抖动/漂移/render 与 preview 不一致）

- **优先 tween**：`x`/`y`/`scale`/`scaleX`/`scaleY`/`rotation`、`opacity`、`color`/`backgroundColor`/`borderRadius`；
- **禁/慎**：不 tween `display`/`visibility`（`autoAlpha` 只用于非 clip 元素或 clip 内 wrapper；硬切用 `tl.set()` 在明确边界）；
  不 tween 布局属性 `width/height/top/left`（尤其媒体）；不让多条 timeline 写同一元素同一属性；
  tween 期间禁 `getBoundingClientRect()` 动态推位（初始化测一次或预计算常量）；
- **禁驱动视觉的非确定性源**：`Date.now()`/`performance.now()`、未播种 `Math.random()`、render 期网络 fetch、
  hover/focus/scroll/pointer 状态、`repeat:-1`、依赖前帧累计的粒子/物理；
- **有限循环**：`const repeats = Math.max(0, Math.floor(duration / cycleDuration) - 1)`——必须 `floor` 不能 `ceil`（`ceil` 越过时长）。

### 其他运行时（都必须可对任意时间重复 seek）

| 运行时 | 场景 | Seek |
|---|---|---|
| GSAP（默认） | 时间线/变换/easing/stagger | `window.__timelines` |
| Lottie/dotLottie | AE 预烘焙 | `window.__hfLottie` |
| Three.js | 3D/相机/shader/GLTF | `hf-seek` / adapter 时间 |
| Anime.js | 轻量 tween | `window.__hfAnime` |
| CSS keyframes | 装饰/shimmer/有限循环 | delay / play-state / 有限 duration |
| WAAPI | 原生 keyframes | `animation.currentTime` |
| TypeGPU/WebGPU | GPU 粒子/compute | `hf-seek` |

Frame Adapter v0：`getDurationFrames()` 返回有限非负整数，`seekFrame(frame)` 任意顺序且幂等，越界 clamp，
生命周期 init → 多次 seek → destroy。**本仓 WebGL/Three 实战见下方**，程序化 3D 优先 headless Chrome 逐帧烘焙成 mp4。

### 能力地图（用户要"更炫酷"时知道 HyperFrames 能干什么 → 先 `catalog --json` 再 `add <name>`）

HyperFrames/Catalog 覆盖：**转场**（CSS 套件 3D/Blur/Cover/Dissolve/Push/Radial/Scale… + shader Whip Pan/
Cinematic Zoom/Light Leak/Ripple/Glitch…）、**字幕组件**（Kinetic Slam/Karaoke/Neon/Glitch RGB/Highlight…）、
**HTML-in-Canvas/VFX**（iPhone&MacBook 3D、Liquid Glass、Portal、Shatter、Magnetic）、**社交 overlay**
（IG/TikTok/YouTube/X/Reddit/Spotify）、**lower thirds**、**数据/地图**（Data Chart、choropleth/flow/hex、World Map）、
**effects/text**（Grain/Vignette/Shimmer/Pixelate/Parallax Zoom/Morph Text/Texture Mask）、**字幕转写/编辑**、
**去背景/透明素材**（`remove-background`）、**编解码代理/渲染缓存/并行渲染**。
Catalog 是快变在线表面——**不要背名单**，先 `npx hyperframes catalog --json` 查活口径再显式 `add`。
本仓 compose 前一次性装好计划用的 block，再并行制作；VFX 优先装现成 block 而非从零手搓（见 F14）。

## 渲染纪律

- 渲染一律 `--docker`：同一 composition 逐字节复现——未来 golden-set 回归可做帧级 diff，基线从 M0 第一片就用 Docker 建；
- 逐帧寻位（整数帧时钟），动画时长换算成帧数思考（30fps：0.3s = 9 帧）。

## 感受词 → 参数（与 styles/translation-table.md 联动，拉片后往总表补行）

| 感受词 | GSAP 参数 |
|---|---|
| 干脆 / snappy | `power4.out`，0.2–0.4s |
| 能量感 | 入场 0.2s 级；元素错峰 stagger 0.05–0.08s |
| 沉稳 | `power2.inOut`，0.5–0.8s，位移小 |
| 数字强调 | count-up ≤ 0.6s，`tabular-nums` 防抖动 |

## 典型用途（声部：信息主轨）

榜单卡 / 数据卡 / 大数字卡 / 标题与章节卡 / 引言卡 / 全片字幕层 / 图片动效容器（见 image-motion.md——Ken Burns 在这里做，不预烘焙 mp4，可调且确定性）。

## WebGL/Three.js 集成(2026-07-15 实战教训)

- **`<script type="module">` 在渲染管线里不执行**(页面走 file:// 加载,ESM 被 CORS 拦死;http:// 预览正常→snapshot/render 全黑,极具迷惑性)。classic script(如 gsap.min.js)不受影响;
- three 要用 **UMD 版**(`three@0.160.0/build/three.min.js`,r160 是最后一个带 UMD 的版本)+ classic script;
- 即便 classic 加载成功,**引擎会按帧重建/接管 DOM,脚本绑定的 canvas 引用会被换掉**——canvas 在预览亮、在 render 黑;
- **可靠路径:程序化 3D 用 headless Chrome 逐帧烘焙成 mp4**(`chrome --headless=new --screenshot` + `?t=` 参数确定性渲染 + ffmpeg 组装),再当普通 video clip 挂入——视频管线是被验证的。渲染器 WebGLRenderer 记得 `preserveDrawingBuffer:true`;
- Seedance 素材挂入前**必须重编码密集关键帧**(`-g 12 -keyint_min 12 -sc_threshold 0`),否则渲染器 seek 冻帧(引擎会 WARN sparse keyframes)。

## 反模式

- 每个条目换一种版式（模板味 + 认知负担）；
- 用 HTML 做"要真运动"的镜头（路由纪律：task_fit 归零）；
- 动画堆砌：同屏 > 2 个并发动画即审视必要性。
