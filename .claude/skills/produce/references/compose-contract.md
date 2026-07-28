# 产物合同 · compose（交付面 · 引擎版本无关）

> 何时读我：**compose 阶段开工前必读**；review 出厂前对照第 8 节机器门清单。
> 定位：这份文件只写「**片子必须长成什么样、怎么机器验**」——约束与失败模式，不写某个 CLI 的
> flag 和 API 用法。它跨引擎版本恒定，宿主换成自己适配版的 HyperFrames 也照样成立，
> 所以**它在交付面里**（CLAUDE.md §交付面）。
>
> 分工：
> - **引擎怎么用**（安装、CLI、catalog、color grading 键、镜像构建、WebGL 实战）→ `hyperframes.md`，**不在交付面**；
> - **动效语法**（接缝法、表演法）→ `motion-continuity.md`；配方 few-shot → `hyperframes-recipes.md`；
> - **上游手册全文** → `docs/hyperframes-agent-handbook.md`（外部参考，基线 0.7.77，与本文件冲突以本文件为准）。
>
> 沿革：2026-07-28 从 `hyperframes.md` 拆出（原文件把合同与 API 混写，交付面切不干净）。

## 1. 六条硬规则（违反 = lint 不过 = 禁 render）

1. **时间线必须是暂停态的、并且被注册**：`gsap.timeline({paused:true})` 同步创建，注册到
   `window.__timelines[compositionId]`，key 精确等于根的 `data-composition-id`。禁 `tl.play()`。
2. **`<video>` 必须 `muted`**，声音走独立 `<audio>` 轨（即使同源文件）。混音归 compose 契约管。
3. **禁一切非确定性源**：`Math.random` / `Date.now` / `performance.now` / `requestAnimationFrame` /
   渲染期网络请求 / hover-focus-scroll 状态 / `repeat:-1` / 依赖前帧累计的粒子物理。
   **一切必须由帧时钟驱动、对任意时间重复 seek 结果一致。**
4. **计时元素必须带 `class="clip"` + `data-start` / `data-duration` / `data-track-index`。**
5. **资产全部本地文件，禁 CDN。** 渲染机 tar 只带 compose 目录，渲染期又禁网络请求——外链等于必崩。
6. **GSAP 供给纪律**：用了 `gsap.timeline()` 就必须**自带在盘的真 `assets/gsap.min.js`**（首选，版本无关），
   或**整块**抄 `gsap-fallback-shim.md` §2 的 shim（实现生命周期全表）。**禁手搓半截 shim**——渲染机 seek
   驱动会调 `timeScale()`/`invalidate()`/`eventCallback()`，漏一个就 `[Browser:PAGEERROR]`→capture rc=1。
   机器门：`tools/kuleshov-lint.py` ⑥。

## 2. 结构合同

### 2.1 属性

- **根**：`data-composition-id`（必需，与 `window.__timelines[id]` 一致）、`data-width`/`data-height`
  （1920×1080 / 1080×1920 / 1080×1080）、`data-duration`（**强烈建议显式写**，编译期锁定总渲染秒数）；
  全屏背景放 **full-bleed 子节点**，不放根本身（否则 preview 正常、render 黑帧）。
- **clip**：`id` 全 assembled page 唯一；`data-start`（绝对秒或同 composition 内相对引用）；
  `data-duration`（div/img/子 composition host 必需，video/audio 可用素材固有时长）；`data-track-index` 必需；
  可视 DOM 才加 `class="clip"`（video / audio 不加）。可见窗口**含**结束时刻（`start ≤ t ≤ start+duration`，末帧保持终态）。
- **track ≠ z-index**：`data-track-index` 是"时间车道"（**同轨不得时间重叠**），视觉前后用 CSS `z-index`；
  惯例 0=底层视频、1+=视觉/overlay、10+=音频；两个重叠的 scene wrapper 必须不同轨。
- **相对时间**：`data-start="intro"` / `"intro - 0.5"` 只在同 composition 内引用，被引用 clip 须有可知时长，
  不可成环，链 ≤3–4 层。

### 2.2 子 composition 三条不可违反的跨文件规则

（"左上角小字 / SVG 铺满整屏"这类怪象全是踩这里）

1. 运行时**只 clone `<template>` 内**的内容——`<style>`/`<script>`/markup 必须全在 `<template>` 内；
2. host `data-composition-id`、子根 `data-composition-id`、`window.__timelines` 注册 key **三者完全相同**；
3. 子根用 `#root` 样式，**别依赖根自身 class 选择器**（编译器给普通选择器加 scope，根 class 会被改写成命不中的 descendant）。

host `data-duration` 是可见窗口（子 timeline 短则保持末帧，host 窗口短则到点隐藏）。**禁手工 `master.add(child)`**
把子 timeline 嵌进根 timeline——框架独立 seek，手工嵌套 = 双重 seek。子 composition 内 element id 加前缀防重复。
入场优先 `fromTo()`（明确两端，减少 seek-back 与 `from()` 初值捕获差异）。

### 2.3 媒体（黑帧 / 白帧 / 停帧的头号根因）

- `<video>`/`<audio>` **不要放进带时间的 wrapper**（这是仅存的红线；嵌套深度本身在 0.7.77 已放开，
  运行时按祖先累计起点重算 `data-start`——细节见手册 §0.3）；
- `<video>` 必须 `muted playsinline`；声音走独立 `<audio>`；
- **禁** `.play()` / `.pause()` / 写 `currentTime`——框架拥有播放与 seek；
- **禁**在媒体上 tween `width/height/top/left`；用不计时 wrapper，只 tween transform/opacity；
- 子 composition timeline **不能**驱动 host 媒体；host 媒体的 scale/opacity 写在根 timeline，时间用全局秒；
- 入点 `data-media-start`；wrapper 源偏移 `data-playback-start`；倍速 `data-playback-rate`（0.1–5）；
- **本仓附加**：Seedance / 拼贴素材挂入前必须重编码密集关键帧
  （`-g 12 -keyint_min 12 -sc_threshold 0`），否则渲染器 seek 冻帧。

## 3. 动画与确定性

- **优先 tween**：`x`/`y`/`scale`/`scaleX`/`scaleY`/`rotation`、`opacity`、`color`/`backgroundColor`/`borderRadius`；
- **禁 / 慎**：不 tween `display`/`visibility`（`autoAlpha` 只用于非 clip 元素或 clip 内 wrapper；硬切用
  `tl.set()` 落在明确边界）；不 tween 布局属性 `width/height/top/left`；不让多条 timeline 写同一元素同一属性；
  tween 期间禁 `getBoundingClientRect()` 动态推位（初始化测一次或预计算常量）；
- **有限循环**：`const repeats = Math.max(0, Math.floor(duration / cycleDuration) - 1)`——必须 `floor` 不能 `ceil`。
  引擎在 0.7.77 对有限 `data-duration` 把 `repeat:-1` 降为 warning，**本仓仍按有限次数写**（确定性规范未跟着改）。

## 4. 渲染正确性

- **舞台底必须不透明**：`#root { background: var(--canvas-deep, var(--canvas, #000)); }`。接缝会开出
  "两个 wrapper 透明度之和 < 1"的窗口，`#root` 不painted 时渲染器把它合成到默认**白**页面 → 每个接缝闪一次白。
- **clip 门控**：`data-start` 早于入场 tween 的 clip 会以初始透明度直接亮相。必须 `autoAlpha:0` 起手
  **且** `data-start` = 切点时刻。
- 逐帧寻位（整数帧时钟），动画时长换算成帧数思考（30fps：0.3s = 9 帧）。
- 接缝的方向/速度/相位法见 `motion-continuity.md`。

## 5. 字体

**compose 一律自带 woff2，禁 `local("系统字体")` 承担正文/标题**——渲染机是 Linux，`local()` 落 font-kit 兜底
会造成字宽微差 → 长标题换行点漂移（实证：SSIM 0.981 那次差异的全部根因）。`local()` 只允许作为
woff2 之后的最末兜底。`font-weight` 只取 woff2 实有档，别让浏览器 faux-bold。
机器门：`tools/kuleshov-lint.py` ①。

## 6. 字幕（2026-07-28 起按 grain 发布硬门收口）

**字幕是外挂 sidecar，不烧进画面。**

1. **产物形态**：交付物是 `out/final.mp4` + `out/final.vtt` 两件。compose 里**不许有字幕层**——
   grain 的发布三件套（`carrier-contracts/video.md`）要求 `metadata.subtitles=[{lang,url,format:'vtt',…}]`，
   且**禁烧进画面、禁手写**。
2. **same-source**：VTT 的**文本**来自剧本（`audio/narration.txt`），**时间**来自强制对齐
   （`audio/timeline_fa.json` 的真实字戳）。禁用 ASR 转写文本当字幕（中文数字与同音字会漂），
   ASR 只允许用来提供时间锚。工具：`tools/make-vtt.py`。
3. **不带标点**：句末标点删除，句中停顿换全角空格。**切分仍然用标点**（断句依据），只在输出层剥离。
4. **没有烧录通道**（2026-07-28 用户拍板）：不做"社媒烧录变体"这条支线——默认且唯一的形态就是不烧。
   存量片（status 已 `review`/`delivered`）按旧政策烧录，不追溯；重做或复用其 compose 时必须改成外挂。

机器门：`tools/kuleshov-lint.py` ⑤（无标点）+ ⑦（禁烧 / VTT 齐备）。

## 7. 时间口径

- **音频是全片时钟**：所有视觉区间绑定 `audio.timeline` 的真实时间戳。禁按剧本字数估时。
- 文字元素的入场 `data-start` 对齐其内容词的 timeline 戳（卡片按句首戳、字幕按 forced-align 词戳）；
  与口播听感差 >0.2s 即打回（`visual-selfcheck.md` 硬查 13）。
- 时长调和顺序：尾部裁切（保动作完成点）→ 变速 ±5% → 均不可则该镜重做。**禁止冻结帧补时长。**

## 8. 机器门清单（哪些会开火，哪些只是纸面）

| 门 | 查什么 | 状态 |
|---|---|---|
| `tools/kuleshov-lint.py` ① | woff2 纪律（禁 local 承担正文） | ✅ error |
| ② | 时效词（相对时间词出厂复核） | ⚠️ warn |
| ③ | 脚注 / 角标压容器边框（启发式） | ✅ error |
| ④ | 组件底板 / PPT 味（宪法级） | ✅ error |
| ⑤ | 字幕标点 | ✅ error |
| ⑥ | GSAP 供给 + 禁 CDN | ✅ error |
| ⑦ | 字幕外挂（禁烧进画面 / VTT 齐备） | ✅ error |
| `npx hyperframes check` | Lint / Runtime / Layout / Motion / Contrast | ✅ 不过禁 render |
| `tools/measure-render.py` | 终渲反测：静态持有、媒体计数、时长、响度、主色漂移 | ✅ 喂 `style.contract.render` |
| `kuleshov-ir validate` | Film IR 结构 + 风格合同阈值 | ✅ error |
| 接缝一致性 | 方向/速度/相位/白闪 | ❌ **无机器门**，靠边界三帧 snapshot 目检 |
| 字幕叠加律（不留死带） | 构图真中心 | ❌ **无机器门**，靠抽帧目检 |

**别把纸面写成机器门**：这张表里 ❌ 的两项目前只有人工，说"lint 会拦"就是谎报。
新增门要同时改这张表和 `visual-selfcheck.md` 的清单。

## 9. 合同侧反模式

- 用 HTML 做"要真运动"的镜头（路由纪律：task_fit 归零，别拿版式冒充 `motion_led`）；
- 每个条目换一种版式（模板味 + 认知负担）；
- 同屏 > 2 个并发动画（先审视必要性）；
- 冻结帧 / 慢速 Ken Burns 冒充运动；
- 为了给字幕腾地方把构图整体上移、留一条死带（`visual-selfcheck.md` 硬查 19）。
