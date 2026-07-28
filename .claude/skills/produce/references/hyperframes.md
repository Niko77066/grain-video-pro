# 引擎参考 · HyperFrames（**不在交付面**）

> 何时读我：storyboard 有镜头路由到 `hyperframes` 时；compose 期要查引擎具体怎么调时。
>
> ## 🔴 先读合同，再读本文件
>
> | 要什么 | 去哪 | 在不在交付面 |
> |---|---|---|
> | **片子必须长成什么样、怎么机器验**（硬规则 / 结构 / 媒体 / 确定性 / 字体 / 字幕 / 机器门清单） | **`compose-contract.md`** | ✅ 在 |
> | 接缝法与表演法（矢量律、五种接缝、禁 idle wobble） | `motion-continuity.md` | ✅ 在 |
> | 动效配方 few-shot（F01–F16） | `hyperframes-recipes.md` | ✅ 在 |
> | **引擎怎么用**（安装、变量、color grading 键、catalog、镜像构建、WebGL 实战） | **本文件** | ❌ 不在 |
> | 上游手册全文（2154 行，基线 0.7.77） | `docs/hyperframes-agent-handbook.md` | ❌ 不在 |
>
> **为什么本文件不在交付面**：宿主 grain 有自己适配版的 HyperFrames 与 `producing-hyperframes-video`
> step-skill，这里的 CLI flag、键名、镜像口径换个适配版就失效；把它带过去会让 agent 照着错的
> 参数调宿主引擎。合同那半跨版本恒定，所以拆走了（2026-07-28 拆分，CLAUDE.md §交付面）。
>
> **CLI 口径 0.7.77**。官方 skill 副本已挖矿后删除，溯源与复原命令见 `vendor/upstream-skills/README.md`。
> <!--# 策略：版本号/Catalog 数量/launch 技巧会老化；本仓 compose 合同与 tools/kuleshov-lint.py
> 永远优先于手册，官网 llms.txt 是细节的活口径。 -->

## 定位

HeyGen 开源（Apache 2.0）的 agent-native 合成框架："写 HTML/CSS/GSAP，渲染视频"。**不产生像素，只做确定性合成**。它是 **MG 动画（motion graphics）/信息图形语言**的主引擎，也是全片叠加层（字幕/角标/数据卡）的宿主——按表达选它，不是按成本选它。

**类型纪律**：全部产出属"幻灯片语法"，**不计入运动占比**——片型承诺只能写 `typography_led` / `data_explainer`，冒充 `motion_led` 是承诺违约。

## 安装与文档

```bash
npx skills add heygen-com/hyperframes   # 8 核心 + 10 工作流技能
```

- 文档索引：hyperframes.heygen.com/llms.txt （细节问题先查这里，别猜 API）
- Playground：hyperframes.dev

## 引擎机制（**合同在 `compose-contract.md`**，这里只讲机制怎么用）

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

### 新版本镜像怎么建（2026-07-28 定法，别再让 CLI 自己 build）

`hyperframes render --docker` 遇到没有的 tag 会现建镜像，走完整 apt（chromium 31MB 那一包）——
实测 0.7.77 在 apt 阶段撞上 CLI 自己的 `spawnSync ETIMEDOUT`（~9 分钟）直接失败，0.7.70 当初是撞代理被拒。
**定法：从上一个可用镜像叠一层，只换 npm 包，不碰 apt**（0.7.77 实测 36 秒建完）：

```bash
printf 'FROM hyperframes-renderer:<上一版>-arm64\nRUN npm install -g hyperframes@<新版> \\\n && rm -rf /usr/local/lib/core && mkdir -p /usr/local/lib/core \\\n && cp -a /usr/local/lib/node_modules/hyperframes/dist /usr/local/lib/core/dist \\\n && test -f /usr/local/lib/core/dist/hyperframe.manifest.json\n' > hf.Dockerfile
docker build --platform linux/arm64 -t hyperframes-renderer:<新版>-arm64-corefix -f hf.Dockerfile .
```

`core/dist` 那两行是 corefix（容器内 CLI 按 monorepo 布局找 `/usr/local/lib/core/dist/hyperframe.manifest.json`）；
**必须 `cp -a` 不许 symlink**——符号链接版 file_server 阶段会间歇性报 manifest 缺失。建完用 `docker run` 直调该 tag
（CLI 的 `--docker` 只认无后缀的 `<版本>-arm64`，认不到 corefix tag）：

```bash
docker run --rm --platform linux/arm64 --shm-size=2g \
  -v "<proj>/compose:/project:ro" -v "<proj>/out:/output" \
  hyperframes-renderer:<新版>-arm64-corefix /project \
  --output /output/final.mp4 --fps 30 --quality high --format mp4 --no-browser-gpu
```

**当前口径：`hyperframes-renderer:0.7.77-arm64-corefix`**（2026-07-28 建，blank 冒烟 300 帧 / 10s / 24.4s 通过）。

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

## 反模式（引擎侧）

- `<script type="module">`：渲染管线走 file://，ESM 被 CORS 拦死（preview 正常 → render 全黑）；
- 直接 blur `<video>`（要套 wrapper）；同一元素同一条 tween 里同时动 blur 与 opacity（headless 合成 bug）；
- 背 catalog 名单：它是快变在线表面，先 `catalog --json` 查活口径再 `add`。

> 表达侧反模式（版式雷同、拿版式冒充运动、动画堆砌）在 `compose-contract.md` §9。
