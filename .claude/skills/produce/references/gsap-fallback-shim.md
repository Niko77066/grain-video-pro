# 引擎知识包 · GSAP 供给纪律 + fallback shim（seek 驱动生命周期全表）

> 何时读我：compose 用到 `gsap.timeline()` / 往 `window.__timelines` 注册时钟时。
> 白板类（whiteboard-generalist / typography-led）兜底合成尤其必读——本文件是
> `e2e-post-less` 那次 `n.timeScale is not a function`（capture rc=1）的根因收口。

## 0. 根因（先读，别再犯）

渲染机的 **seek 驱动**会对注册到 `window.__timelines[compositionId]` 的每条时间线
**逐帧寻位**，并在寻位前后调用一批**生命周期方法做归一**（把 timeScale 归 1、pause、
必要时 invalidate/eventCallback）。真 GSAP 时间线实现了全部这些方法，所以自带真
`gsap.min.js` 的片子从不踩坑。

**手搓的 `window.gsap` shim（如临时写的 `MiniTimeline`）一旦漏实现其中任一方法**，
渲染机在 `capture_disk` 阶段调到它就崩：

```
[Browser:PAGEERROR] n.timeScale is not a function   → exitCode 1，整条渲染报废
```

不同 `hyperframesVersion` 调的方法集会变（0.7.3 实测会调 `timeScale`），所以
**"补齐当前报错的那一个方法"不是修复**——下个版本换调别的方法又崩。真正的收口是
下面两条纪律之一，二选一，`tools/kuleshov-lint.py` ⑥ 机械把关（缺则 error、禁渲染，见 §3）。

## 1. 首选：自带真 GSAP（版本无关，golden 全走这条）

所有 golden 合成与 `projects/ac-26-live` 都是这么做的——**版本无关，永不因引擎升级而崩**：

```html
<!-- <head> 里，早于所有时间线脚本 -->
<script src="assets/gsap.min.js"></script>
```

把真 gsap.min.js 拷进 compose 资产目录（仓内规范来源 `assets/gsap.min.js`，GSAP 3.14.2，72KB）：

```bash
cp assets/gsap.min.js <你的project>/compose/assets/gsap.min.js
```

渲染机 tar 只带 compose 目录 → 用**相对路径** `assets/gsap.min.js`，禁 CDN。
72KB 打进 tar 完全在预算内（渲染契约 11M 级 tar 实测可用）。

## 2. 兜底：完整 fallback shim（万不得已自包含时用整块，别删方法）

只有在**确实不能自带 gsap.min.js**（极致自包含场景）时才用 shim。用就用**下面这一整块**，
它实现了 seek 驱动会调的**生命周期全表**（寻位 `seek/totalTime/time`；归一
`timeScale/pause/paused/play/resume/restart/kill/invalidate/eventCallback/progress/duration`）。
**任何一个方法都不许删**——删哪个，渲染机某个版本调到就崩。

shim 覆盖白板类常用属性：`opacity` / `x` / `y` / `z` / `scale(XY)` / `rotation` /
`skew(XY)` / 任意数值 style（width/height/top/left/blur…）。颜色/路径类补间用真 GSAP。

```bash
# 整块拿去用，别手抄、别删方法：
cat tools/gsap-shim.js    # 内联进 composition 的 <script>
```

> **代码本体 2026-07-28 挪到 `tools/gsap-shim.js`**——它是拿去用的东西，不是读进上下文的知识；
> 留在知识包里每次加载白吃 10KB。下面继续讲它覆盖什么、不覆盖什么、怎么验。

### shim 已知边界（越界就必须走第 1 节自带真 GSAP）

- 只插值**数值**属性（transform / opacity / 数值 style）；颜色、路径 `d`、SVG morph、
  文字逐字打字机等**非数值补间**不支持。
- 同一元素同一属性被**多条 tween 链式接力**（后一条从前一条落点续）时，本 shim 的起点在
  构造期一次性从 CSS 基线解析，不会自动接力——链式接力需求请自带真 GSAP。
- 不支持 `repeat` / `yoyo` / 物理插件 / MotionPath。

## 3. 机械门（`tools/kuleshov-lint.py` ⑥ · 2026-07-28 落地）

> 沿革：这段原先写的是 `tools/lint.py` 的 `compose.lint` 门——**那个脚本在本仓从来不存在**
> （从上游仓搬知识时把门写成了既成事实）。2026-07-28 核实并真正实现，现在它是会开火的门。

渲染前机械检查：**compose 里用了 `gsap.` 或注册了 `__timelines`** 就必须

- **要么** 自带在盘的真 `assets/gsap.min.js`（判据：文件存在 + ≥40KB + 含 `timeScale`/`invalidate`/`eventCallback`——
  小体积空壳和改名文件挡在这里）；
- **要么** 内联 shim 且实现**生命周期全表**（`seek` `totalTime` `time` `timeScale` `pause` `paused` `play`
  `resume` `restart` `kill` `invalidate` `eventCallback` `progress` `duration`）。

判定是**项目级**的（扫 `compose/**/*.html`，任一文件供给即算有——同一页面共享 `window`）。会 error 的四种：

| 情况 | 报什么 |
|---|---|
| 用了 gsap，既无真文件也无 shim | 供给违规（首选 `cp assets/gsap.min.js <proj>/compose/assets/`） |
| `<script src>` 引的 gsap 文件不在盘上 | 缺文件（渲染机 tar 只带 compose 目录 → 页面直接崩） |
| 引的"gsap.min.js"是小体积空壳 | 不是真 GSAP |
| 走 shim 但漏方法 | 列出漏了哪几个 |

顺带把**外链 CDN**（硬规则 5）也一并报 error——渲染期禁网络请求，tar 里也没有它。
走完整 shim 的项目过门但留一条 warn：shim 只覆盖数值/transform 属性，颜色与路径类补间仍需真 GSAP。

本文件第 1/2 节任一条做到位即过门。**收益**：这类错误原本要等 capture 阶段
`[Browser:PAGEERROR] …is not a function` 才暴露——一次 1080p 渲染 8 分钟起，现在 lint 秒级挡下。
