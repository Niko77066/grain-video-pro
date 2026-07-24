# 引擎知识包 · HyperFrames 动效配方库（F01–F16 few-shot）

> 何时读我：compose 阶段被要求"做得更炫酷/更有动效/像发布片"，或不知道某个叙事动作
> （出现/替换/完成/比较/进入另一个世界/展示并行规模）该用什么 motion 语言时。
> 本文件是**引擎工艺**（`docs/knowledge-governance.md` §2：引擎工艺→知识包），三套风格包
> （whiteboard / research-dossier / pixel-explainer）compose 时都可取用——不是某个风格的专属。
>
> 资料基线：HyperFrames Agent Handbook 2026-07-23（HyperFrames 0.7.68）的 §13.2 launch
> few-shot，按**本仓 compose 合同**重写。<!--# 策略@hf-handbook-2026-07-23：配方数值/灵感来源随
> launch 仓库变化，题面老化即重标；motion grammar 本身稳定。 -->

## 0. 优先级（冲突时的裁决顺序）

配方是 **motion grammar（抄结构、时序、参数组织），不是模板（不照抄内容/皮肤）**。遇冲突：

1. **本仓 compose 硬规则**（`../SKILL.md` + `hyperframes.md`）与 `tools/lint.py` compose 门——最高；
2. 本文件配方结构与时序；
3. 手册/官网/launch 历史源码——最低，仅供灵感，旧语法（`width/top/left/filter/display`
   动画、CDN 引 GSAP、`master.add(child)` 手工嵌套）一律按本仓合同重写，不照抄。

**每次套用配方后必过**：`python3 tools/lint.py projects/<片名>` 无 error；关键时刻 snapshot 肉眼过。

## 1. 通用骨架（所有配方共用，先建一次）

配方片段里的 `root`/`tl` 指下面这一支。**同一 composition 只保留一支 `tl`**，按
"查询 root → 建 paused tl → 加所选配方的 tween → 注册"组织；`fx-` 前缀换成本 composition 唯一前缀：

```html
<!-- <head>：早于所有时间线脚本，自带在盘真 GSAP（禁 CDN；渲染机 tar 只带 compose 目录） -->
<script src="assets/gsap.min.js"></script>
```

```js
const compositionId = 'replace-with-your-composition-id';   // 必须 === 根的 data-composition-id
const root = document.querySelector(`[data-composition-id="${compositionId}"]`);
const tl = gsap.timeline({ paused: true });                 // 硬规则：paused，同步创建，禁 tl.play()

// … 把所选配方的 tween 加到这一支 tl 上 …

window.__timelines = window.__timelines || {};
window.__timelines[compositionId] = tl;                     // key 精确等于 compositionId
```

**时间口径（本仓铁律，覆盖手册）**：配方里的秒数是**参考节奏，不是魔法数**。真实挂载时间
从 `audio.timeline` 派生（VO 词点 / music beat / section 区间）——先按词点/拍点换算 `data-start`
与各 tween 的起始时刻，再微调 duration 与 stagger。禁手写脱离 audio.timeline 的秒数。

**每个配方都遵守的合同**（否则 lint/render 报废，细节见 `hyperframes.md`）：可视计时 DOM 带
`class="clip"` + `data-start/duration/track-index`；`<video>` `muted` 且是 composition 根的直接子节点、
声音走独立 `<audio>`；ID 全片唯一；禁 `Math.random`/`Date.now`/`requestAnimationFrame`/`repeat:-1`；
只 tween transform/opacity/color/borderRadius 白名单属性，禁 tween `width/height/top/left`（尤其媒体）。

---

## 2. 按叙事动作选配方（先定动作，再挑 motion）

面对"做得更有动效"这类模糊要求，**不要随机叠效果**，按此顺序决定：

1. **先找叙事动作**：出现 / 替换 / 完成 / 比较 / 交互 / 进入另一个世界 / 展示并行规模？
2. **选一个主配方**：出现→F01/F07；替换→F02/F08；完成→F06/F15；交互→F03/F04/F05；
   世界切换→F09/F16；流程关系→F10；材质标题→F11；设备内视频→F12。
3. **最多叠一个辅助配方**（如 F07 卡片 + F13 pop SFX；F03 打字 + F04 click；F10 路径 + F06 完成态）。
4. **保留视觉呼吸**：0.3–0.7s 入场、0.6–1.5s 阅读、0.25–0.5s 离场是可靠起点；信息密时**延长阅读**，
   不是加速所有动画。
5. **品牌变量只换皮肤，不改 motion grammar**：先复制结构与时序，再换字体/颜色/圆角/纹理/资产。
6. **最后才上 VFX**：普通 DOM/GSAP 能表达时不为炫技引 WebGL；只有材质/粒子/3D 空间本身承担叙事才用 F14。

| 想要的效果 | 主配方 | 灵感来源（launch，仅结构参考） |
|---|---|---|
| 大字逐词进出、跟旁白卡点 | F01 | timeline-launch/act0-intro-bell、cloud-render-launch/textbeat |
| 一行文案里不断换动词 | F02 | HF-heygen-stripe/rotary、variables-launch/scene-01 |
| 终端打字、提示词输入 | F03 | HF-heygen-stripe/terminal、variables-launch/scene-05 |
| 光标飞入、点击、界面反馈 | F04 | cloud-render-launch/opener、HF-heygen-stripe/commands |
| 聊天消息持续堆叠 | F05 | timeline-launch/act2-merged-chat、cloud-render-launch/responds |
| 多任务并行渲染、进度完成 | F06 | cloud-render-launch/fleet、variables-launch/scene-08 |
| 视频/案例卡片矩阵展开 | F07 | variables-launch/scene-06、cloud-render-launch/payoff |
| 代码或变量值发生变化 | F08 | variables-launch/scene-04、pr-to-video-launch/feature-code |
| 全屏界面收成悬浮窗口 | F09 | cloud-render-launch/opener、finished |
| 流程线、轨迹、连接关系 | F10 | hyperframes-launch/engine、frame-md/scene-05-ui-flow |
| 纹理填充标题 | F11 | texture-launch-video |
| 视频在设备框/产品框中播放 | F12 | figma-launch、timeline-launch/act4-video |
| 动作同时有 click/pop/whoosh | F13 | sfx-music-launch、pr-to-video-launch |
| Canvas/WebGL 随时间确定性渲染 | F14 | hyperframes-launch/flex-shader、vfx-heygen-combined |
| Logo/CTA 结束卡 | F15 | timeline-launch/act6-logo、website-to-hyperframes/end-card |
| 硬切、方向接力、zoom-through | F16 | HF-heygen-stripe、vfx-heygen-combined |

---

## F01｜逐词 Kinetic Typography

**叙事动作：** 出现。关键词按语音逐个落位，停留后成组离场。适合 hook、价值主张、章节标题。

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

```js
const words = root.querySelectorAll('.fx-word');
tl.fromTo(words,
  { x:82, opacity:0 },
  { x:0, opacity:1, duration:.32, stagger:.055, ease:'power4.out' }, 0.12);
tl.to(root.querySelector('.fx-accent'),
  { scale:1.04, duration:.28, yoyo:true, repeat:1, ease:'power2.inOut' }, 1.15);
tl.to(words,
  { y:180, opacity:0, duration:.38, stagger:.05, ease:'power3.in' }, 2.45);
```

**可调：** `x:50–100` 定冲入力度；`stagger:.04–.09` 定语速；强调词用颜色 + 一次有限 pulse。
有精确词点时**不用 stagger**，逐条把 tween 放到对应词的绝对时间。
**别抄错：** section 外壳不要先 `gsap.set(...opacity:0)` 永久隐藏——外壳可见性由 HyperFrames 的
`class="clip"` 管，内部词才由 GSAP 管状态。

## F02｜3D 动词轮 / Rotary Word Dial

**叙事动作：** 替换。固定句式里只换一个高价值动词（"Agent discovers / provisions / generates / pays"）。

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
  .fx-axis { position:absolute; inset:0; transform:translateZ(-260px); transform-style:preserve-3d; }
  .fx-cylinder { position:absolute; inset:0; transform-style:preserve-3d; }
  .fx-cylinder span { --step:30deg; position:absolute; inset:50% 0 auto; text-align:center;
    color:#35c838; transform:translateY(-50%) rotateX(calc(var(--i) * -1 * var(--step))) translateZ(260px); }
</style>
```

```js
const cylinder = root.querySelector('.fx-cylinder');
tl.fromTo(cylinder, { rotationX:0 }, { rotationX:30, duration:.35, ease:'power3.inOut' }, 1.12)
  .to(cylinder, { rotationX:60, duration:.35, ease:'power3.inOut' }, 1.87)
  .to(cylinder, { rotationX:90, duration:.35, ease:'power3.inOut' }, 2.79);
```

**可调：** `--step` 与 `translateZ` 必须配套；每次落点对齐动词的 spoken onset。词宽差异大时，
**设计阶段测出最大宽度写成常量**，禁在 tween 过程测布局（`getBoundingClientRect` 破确定性）。

## F03｜可 Seek 的打字机

**叙事动作：** 交互（输入）。在 terminal/composer/code block 里逐字显示。**预建字符节点控 `opacity`**，
不靠真实键盘事件。

```html
<div class="fx-command" aria-label="hyperframes render">
  <span class="fx-char">h</span><span class="fx-char">y</span><span class="fx-char">p</span><!-- 继续预建 -->
  <span class="fx-caret"></span>
</div>
<style>
  .fx-command { font:600 34px/1.4 ui-monospace,monospace; }
  .fx-char { opacity:0; }
  .fx-caret { display:inline-block; width:4px; height:1em; background:currentColor; vertical-align:-.12em; }
</style>
```

```js
const chars = root.querySelectorAll('.fx-char');
const caret = root.querySelector('.fx-caret');
tl.set(chars, { opacity:0 }, 0)
  .to(chars, { opacity:1, duration:.01, stagger:.045, ease:'none' }, .25)
  .to(caret, { opacity:0, duration:.18, repeat:5, yoyo:true, ease:'steps(1)' }, .25)
  .to(caret, { opacity:0, duration:.01 }, 1.8);
```

字符 span 可在构建期用脚本拆出，但**最终 HTML 里必须已经存在这些 span**。长文本可 tween 一个数值代理
并在 `onUpdate` 里用 `Math.round(progress)` 重算 `textContent`——回调只依赖当前 tween progress，禁累积状态；
**此法需自带真 GSAP（fallback shim 不驱动 onUpdate 文本，见 gsap-fallback-shim.md 边界）**。

## F04｜光标飞入、点击与界面反馈

**叙事动作：** 交互。把"Agent 操作了产品"可视化：光标画外入场→点击时光标与目标同时压缩→恢复。

```js
const cursor = root.querySelector('.fx-cursor');
const target = root.querySelector('.fx-target');
tl.fromTo(cursor,
  { x:520, y:360, opacity:0, rotation:-6 },
  { x:0, y:0, opacity:1, rotation:0, duration:.62, ease:'power3.out' }, .30);
tl.to(cursor, { scale:.82, duration:.09, ease:'power2.in', transformOrigin:'20% 15%' }, .96);
tl.to(target, { scale:.96, backgroundColor:'#d97757', duration:.09, ease:'power2.in' }, .96);
tl.to([cursor,target], { scale:1, duration:.16, ease:'power2.out' }, 1.05);
tl.to(cursor, { opacity:0, duration:.22 }, 1.35);
```

**对位：** 先在 1920×1080（或本片画幅）设计坐标里算好光标终点，把 cursor SVG 的**尖端**（非外框中心）
对到按钮；click SFX 的 `data-start` 放在压缩开始的同一时刻（见 F13）。

## F05｜持久聊天栈

**叙事动作：** 交互（多轮）。prompt/reply 从底部持续堆叠，旧消息上移淡出；同一产品 UI 不因 cut 跳变。

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
```

```js
const stack = root.querySelector('.fx-thread');
const old = root.querySelector('.fx-old');
const user = root.querySelector('.fx-user');
const reply = root.querySelector('.fx-reply');
tl.fromTo(user, { y:18, opacity:0 }, { y:0, opacity:1, duration:.35, ease:'power3.out' }, .25)
  .to(stack, { y:-92, duration:.48, ease:'power3.out' }, .80)
  .fromTo(reply, { y:12, opacity:0 }, { y:0, opacity:1, duration:.35, ease:'power3.out' }, .88)
  .to(old, { opacity:0, duration:.35 }, .88);
```

**关键约束：** 所有消息**预建**，禁 `tl.add(() => appendChild(...))` 运行时改 DOM（破确定性）。
跨 scene 续同一聊天时优先合并为一支 composition；必须拆分则前一终帧与后一初帧用同一组坐标与消息内容。

## F06｜并行任务 / Render Fleet

**叙事动作：** 展示并行规模 + 完成。多条任务依次出现，进度线 0→满，完成态随后显示。

```html
<div class="fx-job"><span>Worker 01</span><i></i><b>✓ done</b></div>
<div class="fx-job"><span>Worker 02</span><i></i><b>✓ done</b></div>
<div class="fx-job"><span>Worker 03</span><i></i><b>✓ done</b></div>
<style>
  .fx-job { display:grid; grid-template-columns:180px 1fr 120px; gap:20px; align-items:center; opacity:0; }
  .fx-job i { height:14px; border-radius:99px; background:#35c838; transform:scaleX(0); transform-origin:left center; }
  .fx-job b { opacity:0; color:#35c838; }
</style>
```

```js
const jobs = [...root.querySelectorAll('.fx-job')];
jobs.forEach((job,i) => {
  const t = .25 + i*.24;
  tl.fromTo(job, { x:-14, opacity:0 }, { x:0, opacity:1, duration:.28 }, t)
    .to(job.querySelector('i'), { scaleX:1, duration:.65+i*.08, ease:'power1.out' }, t+.12)
    .to(job.querySelector('b'), { opacity:1, duration:.2 }, t+.77+i*.08);
});
```

进度条用 `scaleX`（`transform-origin:left`）替代历史案例的 `width:0%→100%`——视觉一致但不触发布局动画。

## F07｜卡片矩阵 / Capability Reel

**叙事动作：** 出现（多个）。中卡先立住，上下/左右卡随后扇出。适合一次展现多个案例/hook/结果。

```js
const center = root.querySelector('.fx-card-center');
const top = root.querySelectorAll('.fx-card-top');
const bottom = root.querySelectorAll('.fx-card-bottom');
const all = root.querySelectorAll('.fx-card');
tl.fromTo(center, { scale:.78, opacity:0 }, { scale:1, opacity:1, duration:.48, ease:'expo.out' }, .05);
tl.fromTo(top, { y:-180, opacity:0 }, { y:0, opacity:1, duration:.5, stagger:.06, ease:'power3.out' }, .42);
tl.fromTo(bottom, { y:180, opacity:0 }, { y:0, opacity:1, duration:.5, stagger:.06, ease:'power3.out' }, .50);
tl.to(all, { scale:1.025, duration:.7, stagger:.025, yoyo:true, repeat:1, ease:'sine.inOut' }, 1.45);
```

**媒体注意：** 视频必须是 composition 根的直接子节点。若视觉上在卡片中，把 `<video>` 与卡片壳做成
**兄弟节点**，用完全相同的静态坐标和同一组 transform tween；**不能把 `<video>` 塞进 `.fx-card`**（会渲染成黑/空）。

## F08｜代码 Diff / 变量替换

**叙事动作：** 替换 / 比较。旧值上滑消失，新值从下进入，最后揭示对应视觉结果。

```html
<span class="fx-swap"><code class="fx-old-value">duration: 8</code><code class="fx-new-value">duration: 3</code></span>
<style>
  .fx-swap { position:relative; display:inline-block; width:260px; height:44px; overflow:hidden; }
  .fx-swap code { position:absolute; inset:0; }
  .fx-new-value { color:#35c838; opacity:0; transform:translateY(12px); }
</style>
```

```js
const swaps = root.querySelectorAll('.fx-swap');
swaps.forEach((swap,i) => {
  const t = .55 + i*.16;
  tl.to(swap.querySelector('.fx-old-value'), { y:-12, opacity:0, duration:.18, ease:'power2.in' }, t)
    .to(swap.querySelector('.fx-new-value'), { y:0, opacity:1, duration:.22, ease:'power2.out' }, t+.09);
});
```

变化行可用固定背景色标 added/removed，但**不要逐帧改 DOM 内容**；长 diff 先在 HTML 里备好两层状态。

## F09｜全屏产品界面收成悬浮窗口

**叙事动作：** 进入另一个世界（尺度切换）。从沉浸式产品画面退到"产品运行在一个窗口里"。
**不 tween `width/height`，用预设尺寸 + `scale`。**

```html
<div class="fx-window"><div class="fx-titlebar">•••</div><!-- UI 内容 --></div>
<style>
  .fx-window { position:absolute; left:160px; top:90px; width:1600px; height:900px;
    border-radius:26px; overflow:hidden; background:#fff; transform-origin:center; }
  .fx-titlebar { opacity:0; }
</style>
```

```js
const win = root.querySelector('.fx-window');
const bar = root.querySelector('.fx-titlebar');
// 1600×900 放大 1.2 后覆盖 1920×1080
tl.fromTo(win, { scale:1.2, borderRadius:0 }, { scale:1, borderRadius:26, duration:.6, ease:'power3.inOut' }, 0)
  .to(bar, { opacity:1, duration:.3, ease:'power2.out' }, .28);
```

反向（窗口→全屏）只交换 from/to。前后若有媒体，媒体层与窗口壳用同一 transform，不改 video DOM 层级。

## F10｜SVG 路径绘制与流程节点

**叙事动作：** 流程关系。展示 agent 流程/数据路径 / "source → composition → render"。

```html
<svg class="fx-flow" viewBox="0 0 1200 400">
  <defs><clipPath id="fx-flow-reveal"><rect class="fx-reveal" width="1200" height="400" /></clipPath></defs>
  <path class="fx-path" clip-path="url(#fx-flow-reveal)" d="M80 300 C340 40 760 360 1120 100" />
  <circle class="fx-dot" cx="80" cy="300" r="12" />
  <circle class="fx-dot" cx="600" cy="205" r="12" />
  <circle class="fx-dot" cx="1120" cy="100" r="12" />
</svg>
<style>
  .fx-path { fill:none; stroke:#35c838; stroke-width:8; stroke-linecap:round; }
  .fx-reveal { transform:scaleX(0); transform-origin:left center; transform-box:fill-box; }
  .fx-dot { fill:#fff; stroke:#35c838; stroke-width:6; opacity:0; }
</style>
```

```js
tl.to(root.querySelector('.fx-reveal'), { scaleX:1, duration:1.15, ease:'power2.inOut' }, .2)
  .fromTo(root.querySelectorAll('.fx-dot'),
    { scale:.4, opacity:0 }, { scale:1, opacity:1, duration:.24, stagger:.45, ease:'back.out(1.5)' }, .2);
```

历史案例用 `strokeDashoffset` 画线；本仓安全版用 `scaleX` 扩展 SVG clipPath——路径不变形、不越动画白名单。
无 MotionPath 插件时**别假装圆点精确沿贝塞尔运动**：要么只画线 + 点亮节点，要么设计阶段采样路径生成确定性 keyframes。

## F11｜纹理填充文字

**叙事动作：** 材质标题。把金属/纸张/石材等 texture 填进大标题，让 typography 自带材质感。

```html
<h1 class="fx-texture-word">TEXTURE</h1>
<style>
  .fx-texture-word { font-size:210px; font-weight:900; color:transparent;
    background-image:linear-gradient(rgba(255,255,255,.12),rgba(0,0,0,.16)), url('assets/masks/diamond-plate.png');
    background-size:100% 100%, 166% 166%; background-position:center,42% 50%;
    background-clip:text; -webkit-background-clip:text; -webkit-text-fill-color:transparent;
    will-change:transform,opacity; }
</style>
```

```js
const word = root.querySelector('.fx-texture-word');
tl.fromTo(word, { scale:.72, y:48, opacity:0 }, { scale:1, y:0, opacity:1, duration:.58, ease:'expo.out' }, .1)
  .to(word, { scale:1.035, duration:.7, yoyo:true, repeat:1, ease:'sine.inOut' }, .8);
```

纹理位置/尺寸/对比度按每个单词单独设定；把 texture 当填充，别再叠无意义霓虹 glow。
**资产路径必须本地可渲染**（相对路径，禁 CDN；渲染机 tar 只带 compose 目录）。

## F12｜设备框 / 产品框中的视频

**叙事动作：** 设备内视频。展示 screen recording，同时遵守"媒体必须直属 root"合同。

```html
<!-- 两者都是 composition root 的直接子节点 -->
<video class="fx-screen" src="assets/demo.mp4" muted playsinline
  data-start="0" data-duration="4" data-media-start="1.5" data-track-index="1"></video>
<div class="fx-device-shell clip" data-start="0" data-duration="4" data-track-index="2"></div>
<style>
  .fx-screen,.fx-device-shell { position:absolute; left:420px; top:120px;
    width:1080px; height:810px; border-radius:36px; transform-origin:center; }
  .fx-screen { object-fit:cover; }
  .fx-device-shell { border:18px solid #151515; box-shadow:0 36px 90px rgba(0,0,0,.3); }
</style>
```

```js
const pair = root.querySelectorAll('.fx-screen,.fx-device-shell');
tl.fromTo(pair, { y:90, scale:.88, opacity:0 }, { y:0, scale:1, opacity:1, duration:.62, ease:'expo.out' }, .12)
  .to(pair, { scale:1.035, duration:1.2, ease:'sine.inOut' }, 1.5);
```

禁 JS 调 `video.play()`/`currentTime`/循环——由 HyperFrames 按 composition time 控制媒体。
text-behind-subject：先生成透明/抠像媒体资产（见 generating-shot-motion 与 media-use），
背景/文字/前景主体分占独立 z 层。

## F13｜SFX 卡点轨道

**叙事动作：** 辅助（音画因果）。whoosh 对齐进入、click 对齐按压、pop 对齐卡片出现、chime 对齐完成态。

```html
<!-- audio 直接放在 composition root 下；时间与 audio.timeline 对齐 -->
<audio src="assets/sfx/whoosh.mp3" data-start="0.10" data-duration="0.55" data-volume="0.8" data-track-index="60"></audio>
<audio src="assets/sfx/click.mp3"  data-start="0.96" data-duration="0.22" data-volume="1"   data-track-index="61"></audio>
<audio src="assets/sfx/chime.mp3"  data-start="1.82" data-duration="0.70" data-volume="0.65" data-track-index="62"></audio>
```

**语法：** whoosh 通常从视觉移动前 1–3 帧起；click 与压缩第一帧同点；pop 与元素由不可见变可见同点；
chime 与 `done`/成功色出现同点。多个 SFX 用不同 track；整片 music/VO 放根层长轨，不在 scene JS 里 `.play()`。
本仓 SFX 绑定视觉因果、BGM 提供结构——别把每个字都做成噪声（judge 会打"音画不同步/噪声堆砌"）。

## F14｜Canvas / WebGL 的确定性时间适配器

**叙事动作：** VFX（仅当材质/粒子/3D 本身承担叙事）。shader/粒子/3D/2D canvas 必须按 timeline 当前时间重绘，
不靠独立 RAF 时钟。

```js
const state = { t:0 };
function renderAt(t) {
  // 纯函数：所有视觉只由 t 和固定常量决定。gl.uniform1f(uTime,t); drawScene(); 或 ctx.clearRect(...); drawFrame(ctx,t);
}
renderAt(0);
tl.to(state, { t:4, duration:4, ease:'none', onUpdate:() => renderAt(state.t) }, 0);
```

**硬规则：** 禁内部 `requestAnimationFrame`/`Date.now`/`performance.now`/未播种随机数/异步网络状态。
粒子随机种子和几何常量在初始化固定；同一个 `t` 必须绘出同一帧。
**本仓 WebGL 补充教训（见 hyperframes.md）**：`<script type="module">` 在 file:// 渲染管线不执行→snapshot/render 全黑；
three 用 UMD r160 + classic script；程序化 3D 更可靠的是 headless Chrome 逐帧烘焙成 mp4 再当普通 video clip 挂入。
复杂 VFX 优先从 Catalog 安装现成 block（`npx hyperframes add …`）再按其时间适配器改，别从零手搓。

## F15｜Logo / CTA 结束卡

**叙事动作：** 完成 / 收尾。前景退场后 Logo 一次清晰 scale settle，随后 CTA/命令 pill 落位，留 0.8–1.5s 可读。

```js
const oldWorld = root.querySelector('.fx-old-world');
const mark = root.querySelector('.fx-logo');
const cta = root.querySelector('.fx-cta');
tl.to(oldWorld, { scale:1.16, opacity:0, duration:.34, ease:'power3.in' }, 0)
  .fromTo(mark, { scale:.72, opacity:0 }, { scale:1, opacity:1, duration:.55, ease:'expo.out' }, .18)
  .fromTo(cta, { y:24, opacity:0 }, { y:0, opacity:1, duration:.38, ease:'power3.out' }, .60)
  .to(mark, { scale:1.018, duration:.7, yoyo:true, repeat:1, ease:'sine.inOut' }, .85);
```

结束卡不再堆新信息——Logo + 品牌关系 + 一个 CTA 足够。停留时长由 composition 的静态 `data-duration` 提供，
**禁加空 tween 垫时长**（本仓硬规则：clip/root 用 `data-duration`，不用空 tween 凑时长）。

## F16｜三种 Scene Seam（接缝）

接缝**两边一起设计**：方向、位移、速度、blur、end/start pose 要匹配；别只修一边。转场词汇 ≤4（本仓合同）。

**A. 连续背景硬切：** 相邻 scene 用同一背景视频源，各自 `data-media-start` 对齐到同一全局源时间，边界只换前景。
**不要把两份背景 crossfade**（中点会变暗）。

**B. 方向接力（tail_relay）：** 前 scene 内容向左 `x:-220, opacity:0` 退出，后 scene 从右 `x:220, opacity:0` 进入，
时长与 ease 相近，观众读作同一次运动（呼应 generating-shot-motion 的 `tail_relay` seam）。

```js
// 前一 scene 尾部
tl.to(root.querySelector('.fx-out'), { x:-220, opacity:0, duration:.28, ease:'power3.in' }, 2.72);
// 后一 scene 头部
tl.fromTo(root.querySelector('.fx-in'), { x:220, opacity:0 }, { x:0, opacity:1, duration:.34, ease:'power3.out' }, 0);
```

**C. Zoom-through：** 前景迅速放大淡出，下一世界从略小/略大 settle 到 1。缩放方向要讲得通：穿过前景→前层放大；
镜头退出→前层缩小。

```js
tl.to(outgoing, { scale:1.28, opacity:0, duration:.24, ease:'power3.in' }, 3.1);        // 出场
tl.fromTo(incoming, { scale:.78, opacity:0 }, { scale:1, opacity:1, duration:.42, ease:'expo.out' }, 0); // 入场
```

**验收：** 分别 snapshot 边界前 2 帧 / 边界 / 边界后 2 帧，检查构图中心、运动方向、速度、背景亮度是否连续。

---

## 3. 组合示例（可审计，不是盲套模板）

用户说"做一个 8 秒 Agent 产品功能演示，结尾带安装命令"，可直接组合（秒数按 VO 词点/beat 重算）：

```text
0.00–1.20  F01：逐词标题 "Ask. Build. Render."
1.20–3.20  F03：在 composer 中输入任务
3.20–4.00  F04 + F13：cursor 点击，click SFX 同点
4.00–6.10  F06：3 个 worker 并行完成，最后一个 chime
6.10–8.00  F15：Logo + `npx hyperframes create` CTA
接缝       F16-B：标题向左退，composer 从右接力
```

套用后必须写清：**用了哪些配方、每个对应什么叙事动作、关键时间点、替换了哪些品牌变量、lint/snapshot 结果**——
这样 few-shot 是可审计的创作依据，而不是模板味来源（judge 模板味专项会直接打）。
