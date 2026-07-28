---
name: pixel-broll
description: 用 GPT-Image-2 + Seedance 2.0 生成**像素风**动画镜头（角色重演 / 机制图解 / 数据实物化），并用主调色板 + 栅格归一把「AI 的软像素」钉成真像素。当用户说"像素风""像素动画""pixel art""做个像素镜头""seedance 出像素""浣熊那种像素镜"，或 storyboard 有镜头路由到 pixel-broll 时使用。强制四闸门：主调色板 → 视觉/动作方案 → 静帧 → 视频，每闸停下等确认。**严禁做旧**：paper / halftone / aged / newsprint / grain / sepia 一律不许进提示词——做旧只能是 compose 层的 LUT，烤进画面就再也剥不掉。
---

# Pixel B-roll · 像素风生成镜头

血统：改编自开源 skill **`gbro-collage-broll`（pyang5166）**。**保留**它的三闸门纪律、visual-spec、assemble-from-empty 首尾帧机制与 QA 结构；**换掉**三样东西：

| | 上游 gbro-collage-broll | 本 skill |
|---|---|---|
| 引擎 | Gemini Omni Flash + Codex `image_gen` | **GPT-Image-2 + Seedance 2.0**（我们的 neodrop 网关） |
| 美术 | 半调纸拼贴（halftone paper collage） | **像素画**（限定调色板 + 硬边栅格） |
| 归一 | 无 | **主调色板锁色 + 栅格归一**（本 skill 的技术脊柱，见 §4） |

> 拼贴风走另一条路：`.claude/skills/collage-broll/SKILL.md`（同一上游的拼贴分支，9:16 已冒烟）。两条链**材质语汇互斥**，不许串词——串词的产物就是"做旧报纸味的假像素"。

## 0. 为什么要有这个 skill（读一遍，别跳）

浣熊片的 7 个 seedance 镜共用同一段手抄提示词前缀：

```
Retro 16-bit PIXEL-ART paper-collage animation, aged-yellow #C9A876 paper grain, ...
```

这段文本在仓库里**不存在**——它靠"抄上一条片的 film.json"传播，而它本身是拼贴模板 find/replace 成像素的杂交产物。于是每条知识片都拿到同一件东西：**报纸拼贴的材质语法 + 像素的词**，再被 compose 的 `#lut`/`#grain` 缝合层压第二遍做旧。像素是有意为之的；**做旧被烤进生成画面**不是。

本 skill 存在的意义就是把这件事变成不可能：模板有唯一出处、禁用词有明文、锁色与栅格由脚本验证。

## 1. 这门语言擅长 / 不擅长（路由用）

- **擅长**：角色重演（版权画面规避位）、机制/因果图解、数据实物化、历史事件重演、抽象概念的可感知化。
- **不擅长（改用 HyperFrames）**：精确文字 / 数字 / 法条 / logo。**锚点内禁一切文字数字**（`seedance.md` TAIL 约束）——数字信息由 HTML 角标叠在像素画上，两层分工。
- **不要用**：需要真实质感的证据位与情感落地位（那是实拍的活）；真人产品口播。

## 2. 🔴 禁用词表（本 skill 的宪法条款）

下列词**一个都不许出现**在 imagegen prompt 与 Seedance prompt 里：

```
paper / paper-collage / cardstock / paper field / uncoated paper fiber / paper grain
halftone / halftone dots / printed dots / newsprint / newspaper
cream keylines / machine-cut edges / soft paper drop shadows
aged / aged-yellow / yellowed / faded / vintage / sepia / archival / weathered
film grain / grain / dust / scratches / #C9A876（编年史纸底 hex）
```

理由分两层：① 前三行是**拼贴风的材质语法**，混进来就得到杂交产物；② 后两行是**做旧**——它必须留在 compose 层的 LUT/grain 里，因为那层可调、可关、可对全片五个来源统一；一旦烤进生成画面就不可逆，而且会和 compose 层叠成第二遍。

**该用的像素语汇**：`chunky pixels` / `consistent pixel grid` / `hard pixel edges, no anti-aliasing` / `limited N-color palette` / `flat color blocks` / `crisp 1-pixel outlines` / `side-view` 或 `isometric` / `sprite` / `animate on twos`。

## 3. 四闸门（强制。每闸停下等确认，部分通过就只放通过的进下一闸）

| 闸 | 产物 | 成本 | 停下问什么 |
|---|---|---|---|
| **Gate 0 · 主调色板** | `palette/master.png` + 色卡 | 免费 | 这套颜色是这条片的世界吗？（**一部片一张，定了就不改**） |
| **Gate 1 · 视觉与动作** | 每镜：核心意思 / 情绪 / 一句话视觉命题 / 3–6 关键物件 / 运动原型 A 或 B / 组装或动作顺序 | 免费 | 隐喻对不对、动作能不能一眼读懂 |
| **Gate 2 · 静帧** | GPT-Image-2 出图 → **归一** → contact sheet | 便宜 | 归一后的像素画本身成不成立 |
| **Gate 3 · 视频** | Seedance 首尾帧 → **归一** → verify + contact sheet | ~$2.7/条 | 组装/动作是否铺满全片、有没有死尾 |

Gate 0 先跑 `bash tools/check-media-setup.sh`；全绿就直接开工，别把配置信息复述给用户。

**批量支持部分通过**：用户只确认 1、2、4 时，只有这三条进下一闸，3 和 5 留在原闸修改——**不许让未确认条目蒙混过关**。重生的 contact sheet 递增 `v2`/`v3`，旧版不覆盖。逐条 QA 结论（含带瑕疵通过的判定理由）写 `<项目>/gate2-qa.md` 与 `gate3-qa.md`。

## 4. 归一层（技术脊柱）

扩散模型给不出真像素，它给的是「像素味的软图」：栅格漂移、抗锯齿边、上万种颜色。归一层用三步物理办法钉回去——**面积降采样到逻辑分辨率 → 对主调色板量化 → 最近邻整数倍放大**。

归一之后有两件事变成**可验证的事实**而不是形容词：

1. 一个逻辑像素 = 输出图上一个 N×N 纯色方块；
2. 全片所有静帧与所有 clip 只用主调色板里的颜色 → **跨镜头主色漂移在生成之前就被锁死**，不靠 compose 调色补救（对 `pixel-chronicle` 的 `render.palette_drift_max` 是直接收益）。

```bash
python3 .claude/skills/pixel-broll/scripts/make-palette.py \
  --hex 1a1c2c,5d275d,b13e53,ef7d57,ffcd75,a7f070,38b764,257179,29366f,3b5dc9,41a6f6,73eff7,f4f4f4,94b0c2,566c86,333c57 \
  --out projects/<片>/palette/master.png --swatch projects/<片>/palette/swatch.png
```

- **色数 16–32 是甜区**（脚本带宽 4–64）。色太多就不是像素画了，太少表达不了层次。
- **抖动默认关**（`--dither none`）。ordered dither 的网点纹理会被读成半调/纸颗粒——那正是要划清界限的东西。渐变实在压不住时才 `--dither bayer:bayer_scale=4`，并记进 `ledger.decisions`。
- **`--crf 0`（无损）是默认，别省**。有损压缩会在方块边缘长出振铃，把 32 色打回上千色（实测 crf 10 → 678 色 / 4349 个非纯色方块；crf 0 → 31 色 / 0 个）。像素画本身压得极小，无损中间产物不贵。
- `-g 12 -sc_threshold 0` 已内置：挂进 HyperFrames `<video>` 后 seek 不冻帧。

## 5. 画幅与几何（唯一需要按画幅切换的表）

| 环节 | 16:9 横屏 | 9:16 竖屏 |
|---|---|---|
| GPT-Image-2 `size` | `1280x720` | `720x1280` |
| 逻辑分辨率（grid 4） | `320x180` | `180x320` |
| Seedance 首/尾帧（grid 6） | `1920x1080` | `1080x1920` |
| Seedance `metadata.ratio` | `"16:9"` | `"9:16"` |
| 归一输出（grid 4） | `1280x720` | `720x1280` |

**整数倍是硬约束**：1280→1920 是 1.5 倍，直接放大会把栅格糊掉；正确路径是从逻辑图 `320x180` 用 grid 6 放到 `1920x1080`。`pixelize.py` 不是整数倍会直接报错，不会静默糊掉。

## 6. 两种运动原型（Gate 1 必须二选一并写进 IR）

| | **A · 组装型** | **B · 角色动作型** |
|---|---|---|
| 用在 | 图解、机制、数据实物化、地图 | 重演、生活场景、情绪落点 |
| 首帧 | 空色场（调色板里的底色，纯色） | 场景 + 角色**起始**姿态 |
| 尾帧 | 组装完成的图解 | 动作**完成**姿态 |
| 提示词骨架 | 逐件滑入 / 卡位 / 连接，铺满整条 clip | 一个主动作，连续进行，末拍落在最后一秒 |

两者都：`duration: 10`（**5s 会被打回"过得太快"**，定格质感需要呼吸，见 `seedance.md`）、锁死机位（`locked-off`，像素画的运镜靠元素动不靠相机动）、`generate_audio: false`。

## 7. 提示词模板

**角色一致性铁律**：角色长相只在 Gate 2 的 imagegen prompt 里描述一次。Seedance prompt 里**不许重复描述长相**，只写 `the character shown in Image 2`——外观描述与锚点冲突时以锚点为准（`seedance.md` 提示词纪律末条）。浣熊片每镜复述一遍全套长相，是这条纪律的反例。

### Gate 2 · imagegen（`[]` 内替换；画幅句按 §5 切换）

```
Create a finished pixel-art still for a [16:9 horizontal|9:16 vertical] image-to-video shot.
Visual proposition: [一句话视觉命题].
Style: crisp retro pixel art on a consistent pixel grid; chunky pixels, hard edges, no anti-aliasing,
no gradients; flat color blocks with crisp 1-pixel outlines; strictly limited palette of these colors
only: [列出主调色板 hex]. [side-view|isometric] framing.
Scene: [场景], background is a single flat [底色 hex] field.
Subject: [主体/角色外观——全片只在这里描述一次].
Composition: locked poster frame; subject reads as one clear silhouette within the central [70|60] percent;
[3 到 6 个可分离元素组，为后续逐件组装留位（原型 A）|起始姿态清晰可读（原型 B）].
Avoid: no typography, no readable letters, no numerals, no logos, no watermark, no UI, no subtitles,
no photoreal texture, no soft shading, no blur, no anti-aliased edges, no paper texture, no grain,
no aged or faded look, no sepia, no halftone dots, no clutter.
```

### Gate 3 · Seedance（原型 A · 组装型）

```
Pixel-art animation. Use Image 1 as the exact empty first frame (a flat [底色] field) and Image 2 as the
exact completed last frame. One continuous locked-off [horizontal|vertical] shot, no camera movement.
Open on the empty field, then assemble the scene piece by piece with crisp stepped timing, PACED EVENLY
ACROSS THE ENTIRE CLIP: pieces keep sliding in and snapping into place continuously through the whole
shot — do NOT finish early, do NOT hold a long static frame; [按顺序描述 3–6 元素如何滑入/卡位/连接],
with the final pieces snapping into place in the last second to complete Image 2.
Preserve the [16:9|9:16] framing, the exact limited palette, chunky pixels, hard pixel edges and flat
color blocks of Image 2. Animate on twos, stepped motion, no smoothing.
No scene cuts, no camera movement, no zoom, no morphing, no new objects, no anti-aliasing, no motion blur,
no text, no letters, no numbers, no logos, no watermark, no sound.
```

### Gate 3 · Seedance（原型 B · 角色动作型）

```
Pixel-art animation. Use Image 1 as the exact first frame and Image 2 as the exact last frame.
One continuous locked-off [horizontal|vertical] shot, no camera movement.
The character shown in Image 2 [单一主动作，写清怎么动], moving continuously and PACED EVENLY ACROSS THE
ENTIRE CLIP — do NOT finish early, do NOT hold a long static frame; the action completes in the last second
to match Image 2 exactly.
Preserve the [16:9|9:16] framing, the exact limited palette, chunky pixels, hard pixel edges and flat
color blocks. Animate on twos, stepped motion, no smoothing.
No scene cuts, no camera movement, no zoom, no morphing, no new objects, no anti-aliasing, no motion blur,
no text, no letters, no numbers, no logos, no watermark, no sound.
```

## 8. 跑起来（16:9 为例）

```bash
S=.claude/skills/pixel-broll/scripts; P=projects/<片>
# Gate 2：出图 → 归一 → 验静帧
#   GPT-Image-2: POST {ARK_VIDEO_API_BASE_URL}/v1/images/generations
#   {"model":"gpt-image-2","size":"1280x720","quality":"medium","output_format":"png","n":1}
#   （契约与 b64/url 双形态处理见 produce/references/image-motion.md）
python3 $S/pixelize.py still  --in $P/anchors/s03_raw.png --out $P/anchors/s03.png \
        --palette $P/palette/master.png --size 1280x720 --grid 4
python3 $S/verify.py $P/anchors/s03.png --palette $P/palette/master.png --grid 4

# Gate 3：首尾帧（从逻辑图整数倍放大）→ 提交 → 轮询
python3 $S/pixelize.py still  --in $P/anchors/s03_raw.png --out $P/anchors/s03_last.png \
        --palette $P/palette/master.png --size 1920x1080 --grid 6
ffmpeg -y -f lavfi -i color=c=0x<底色HEX>:s=1920x1080 -frames:v 1 $P/anchors/s03_first.png  # 原型 A
python3 tools/seedance.py submit --jobs $P/shots/jobs.json --state $P/shots/state.json --dry-run  # 先离线验形状
python3 tools/seedance.py submit --jobs $P/shots/jobs.json --state $P/shots/state.json
python3 tools/seedance.py poll   --state $P/shots/state.json --out $P/shots/

# 归一 clip → 机器验收
python3 $S/pixelize.py video --in $P/shots/s03_raw.mp4 --out $P/shots/s03.mp4 \
        --palette $P/palette/master.png --size 1280x720 --grid 4
python3 $S/verify.py $P/shots/s03.mp4 --palette $P/palette/master.png --grid 4 \
        --json $P/evidence/pixel-qa-s03.json --contact $P/evidence/s03-contact.jpg
```

`jobs.json`：

```json
{ "defaults": {"ratio":"16:9","resolution":"720p","duration":10,"oss_prefix":"kuleshov/<片>/pixel"},
  "jobs": [ {"name":"s03","prompt":"<Seedance prompt>",
             "first":"projects/<片>/anchors/s03_first.png",
             "last":"projects/<片>/anchors/s03_last.png"} ] }
```

`tools/seedance.py` 把三条最容易写错的契约固化成会报错的形状：`duration` 必须在 `metadata` 内（顶层会被忽略，恒出 5.04s）、`ratio` 不许省略（省略由上游自判画幅）、越界 duration 提交前本地拦截（越界会在**排队后**才拒且**已计费**）。`x-oneapi-request-id` 自动留痕进 `state.json`。

## 9. 验收判据

码判分两层，**error 不清零不进人眼环节**：`scripts/verify.py` 出像素专属的**栅格 + 锁色**，并自动调 `tools/clip-qa.py` 补上通用项（规格 / 死尾 / contact sheet——那份实现与 collage-broll 共用，两条链只有一份死尾判据）：

| 项 | 判据 | 抓的是什么 |
|---|---|---|
| 栅格 | 非纯色方块占比 ≤ 0.2% | AI 软像素、有损压缩振铃 |
| 锁色 | 到最近调色板项的距离 ≤ 容差（静帧 0 / 视频 3） | 做旧色、模型自己长出来的脏色 |
| 死尾 | 尾 2s 运动量 ≥ 全片中位的 25%（相对判据，`tools/clip-qa.py`） | 冻结帧补时长（宪法红线） |
| 规格 | 尺寸为 grid 整数倍、零音轨 | 挂载前的物理前提 |

> **死尾为什么用相对判据**：原来的绝对阈值（YDIF<1 视为近静止）是拿半调拼贴/摄影内容标的。平色像素画在暗底上，相邻帧平均亮度差本来就只有 0.3–0.4——2026-07-28 冒烟实测里四条片误报三条，对照表一看动作明明铺满全片。改成「尾段/全片自身运动量之比」后与内容亮度脱钩，负对照仍然开火（真冻尾 0%、全程动 157%）。
>
> 视频锁色容差为什么不是 0：x264 哪怕无损也只是 YUV 空间无损，RGB→YUV420p→RGB 的取整会让通道漂 ±1~2。这是编码的物理事实，所以判「贴合最近调色板项的距离」，不判等值。（负对照实测：未归一的原片贴合距离 162、越界色 12 万种。）

人眼再看两项脚本查不了的：**动作是否一眼读懂**、**角色是否对得上锚点**。

## 10. 写回 IR

镜头仍是 `provider: "seedance"`（合同 `traits.pixel_narrative` 的 fallback 就是按 provider 认的，别新造 provider 把它绕过去）：

```json
{ "source": { "provider": "seedance",
    "params": { "pixel_narrative": true, "ai_stylized": false,
                "craft": "pixel-broll", "motion_archetype": "A|B",
                "palette": "palette/master.png", "grid": 4, "dither": "none" },
    "note": "像素叙事·<一句话>" } }
```

留痕：`gen` 记 model / 完整 prompt / seed / 首尾帧 / `x-oneapi-request-id` / 实测时长；`qc` 挂 `evidence/pixel-qa-<镜>.json`；成本进 `ledger.costs`（1 张 GPT-Image + 1 条 Seedance ≈ $2.7）。选调色板、选运动原型、开抖动都进 `ledger.decisions`。

## 11. 常见问题

- **像素在动的时候"沸腾"**（方块逐帧乱跳）：先降 `--step-fps` 到 8–10（拍数更慢，抖动更少）；仍沸腾说明 Seedance 在生成时就没守住栅格，回 Gate 3 重生并在 prompt 里加重 `stepped motion, no smoothing`。
- **组装提前做完、尾部长 hold**：`verify.py` 的死尾项会判 fail。修法是重生时强化"铺满整条 clip、末件在最后一秒落位"；**尾裁救不了组装过早**（可用运动短于槽位就得重生或缩短槽位）。
- **归一后主体糊成一坨**：逻辑分辨率太低承载不了这个构图。别调 grid（会破坏与其他镜的一致），回 Gate 2 简化构图——3–6 个大组，不是满屏碎片。
- **出现假字**：回 Gate 2 重生静帧，不要用视频 prompt 修补。
- **worktree 里 oss-upload 失败**：`ln -sf <主仓库>/.env .env`。

## 12. 状态

- **归一层 / 验收层**：✅ 已本地验证（正负对照四组：真像素 clip 与静帧全过；未归一原片、1.46s 冻尾片按预期判 fail）。
- **闸门与禁用词纪律**：`evals.json` 6 条考卷（改本 skill 的流程或提示词后跑一遍，验五类偷跑：Gate 0/1 提前烧钱、部分通过被蒙混、做旧词回流、归一层被跳过、未冒烟就批量）。
- **端到端出片（GPT-Image-2 → Seedance → 归一）**：✅ **已冒烟**（2026-07-28，`projects/_smoke/broll-skills-2026-07-28`，调色板 midnight-neon 16 色，横竖各 1 条，运动原型 B）。实测结论：
  - **归一层是必需的，不是可选后处理**：Seedance 原始输出非纯色方块 **30.5%（横）/ 49.0%（竖）**、越界色 10 万+；归一后 **0.0000% / 0 种**。不归一就没有像素画，只有像素味的软图。
  - **做旧彻底剥干净**：锁色判据把画面钉死在 16 色内，`#C9A876` 那类做旧色物理上进不来。
  - **角色一致性靠 `edits` 挂参考图**（首帧归一图当 ref 出尾帧姿态），横竖两条角色、桌椅、台灯、窗户全部对得上。
  - **实产时长 10.042s**（请求 10s），四条一致。
  - request-id 见 `projects/_smoke/broll-skills-2026-07-28/runs/`。
  - ⚠️ 仍未验：多镜头间的角色一致性（本次每条独立）、长片里连续多个像素镜的观感疲劳。
