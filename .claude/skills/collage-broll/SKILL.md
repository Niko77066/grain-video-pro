---
name: collage-broll
description: 用 GPT-Image-2 + Seedance 2.0 把一句约 5s 口播／观点句／抽象概念做成高级 editorial **半调纸拼贴**（halftone paper-collage）氛围 b-roll——从空色场逐件组装的定格质感。当用户说"拼贴 b-roll""纸拼贴""半调拼贴""拼贴风格配画面""用这段文稿做拼贴动画"，或 storyboard 有镜头路由到 collage-broll 时使用。强制三闸门：视觉隐喻 → 静帧 → 视频，每闸停下等确认，只有确认过的条目进下一闸。**不许串像素词**：pixel / chunky pixels / dithering / limited palette 属于 pixel-broll，混进来就得到杂交产物。
---

# Collage B-roll · 半调纸拼贴氛围镜头

血统：改编自开源 skill **`gbro-collage-broll`（pyang5166）**。**保留**它的美学标准、三闸门纪律、visual-spec、色彩语义与 prompt 骨架；**换掉／补上**：

| | 上游 gbro-collage-broll | 本 skill |
|---|---|---|
| 引擎 | Gemini Omni Flash + Codex `image_gen` | **GPT-Image-2 + Seedance 2.0**（我们的 neodrop 网关） |
| 画幅 | 只有 9:16 | 9:16 ✅ + **16:9 参数与抗摊散 prompt** ✅（2026-07-28 冒烟，未摊散） |
| 死尾 | 无 | **YDIF 相对判据**（宪法红线：禁冻结帧补时长） |
| 缝合 | 无 | **缝合纪律**：与版式卡靠共享半调 + 奶油白 keyline + 品牌点色 + 统一纸颗粒缝成一家 |
| 留痕 | 无 | `x-oneapi-request-id` 进 `ledger.costs`，payload/response 全留 |

> 像素风走另一条路：`.claude/skills/pixel-broll/SKILL.md`（同一上游的像素分支）。两条链**材质语汇互斥**，不许串词——串词的产物就是浣熊片那种"做旧报纸味的假像素"。

## 1. 这门语言擅长 / 不擅长（路由用）

- **擅长**：概念、观点句、抽象隐喻的**氛围 b-roll**；高级编辑风、手作温度；垫在口播下。
- **不擅长（改用 HyperFrames）**：精确文字 / 数字 / 法条 / logo / 收尾落款；可逐层编辑的时间线；真人产品口播。**collage 明确规避文字数字**——要文字就用 HyperFrames **叠层在 collage 上**（overlays 混合层，兼得质感与信息）。

## 2. 美学成功标准（源 skill，已验证）

- 一句话只表达一个清晰隐喻；画面是 3–6 个**可分离大组**（利于从空场组装），不是满屏碎片
- 强烈平坦纯色场（按语意选色）；主体黑白 halftone 照片剪贴为骨架
- 关键卡片/纸张可用红、黄、青、橙、紫、奶油白点色，但服务信息层级、不为彩色而彩色
- 所有纸片：清晰裁切边、奶油白 keyline、低透明柔和阴影、纸颗粒
- 动作 = **assemble-from-empty**（从空场逐件滑入、卡位、组装的定格质感），**不是漂移/晃动/慢 zoom**
- 无字幕、无口播全文、无 logo、无水印、无 UI

**🔴 不许串的词**（属于 pixel-broll）：`pixel / pixel-art / chunky pixels / pixel grid / dithering / limited N-color palette / animate on twos / no anti-aliasing`。

## 3. 色彩语义（选底色；一批内"同设计语言、不同底色"）

焦橙/红=时间消耗·劳动·紧迫｜芥末黄=工具·警示｜墨绿=认知·系统·重置｜深紫=规范·沉淀·长期记忆｜青绿=判断·协作·自动执行。

不要把 cobalt blue 当唯一默认值。主体可以黑白半调为主，但局部彩色纸张必须服务信息层级。

⚠️ **缝合纪律（我们新增）**：collage b-roll 与版式卡（如 daily-brief 纸白场）混排时，底色可各异，但靠**共享的半调 + 奶油白 keyline + 品牌点色（印刷红 #C8451B）+ 统一纸颗粒**缝成一家；防止"拼贴段"与"版式段"割裂成两部片。

## 4. 三闸门（强制——这就是"廉价品味注入"的纪律）

| 闸 | 产物 | 成本 | 停下问什么 |
|---|---|---|---|
| **Gate 1 · 隐喻** | 每条：核心意思 / 情绪 / 一句话视觉命题 / 3–6 关键物件 / 底色+点色 / 组装顺序 | 免费 | 隐喻对不对（错隐喻改文字免费） |
| **Gate 2 · 静帧** | visual-spec → GPT-Image-2 出图 → 编号 contact sheet | 便宜 | 静帧成不成立（错静帧重生一张图，远比重跑一条视频便宜） |
| **Gate 3 · 视频** | Seedance 首尾帧 → QA | ~$2.7/条 | 组装是否铺满全片、有没有死尾 |

**批量支持部分通过**：用户只确认 1、2、4 时，只有这三条进下一闸，3 和 5 留在原闸修改——**不许让未确认条目蒙混过关**。重生的 contact sheet 递增 `v2`/`v3`，旧版不覆盖，方便对比。逐条 QA 结论（含带瑕疵通过的判定理由）写 `<项目>/gate2-qa.md` 与 `gate3-qa.md`。

开工前先跑 `bash tools/check-media-setup.sh`；全绿直接进 Gate 1，别把配置信息复述给用户。

### Gate 2 · visual-spec

```json
{ "script_meaning": "", "visual_metaphor": "",
  "style_signature": "flat bold color field, mixed black-and-white halftone cut-outs and colored cardstock accents, crisp cut edges, cream keylines, soft paper shadows, editorial paper collage",
  "aspect_ratio": "9:16",
  "color_field": {"background_hex": "", "accent_colors": [], "paper_grain": "fine uncoated-paper fiber"},
  "elements": [{"what": "", "role": "", "motion": "", "placement": ""}],
  "composition": {"layout": "", "negative_space": "", "final_frame": ""},
  "motion_plan": "structure first, subject or cards second, action and result last",
  "avoid": "typography, readable letters, numerals, logos, watermark, UI, subtitles, glossy 3D, photoreal environment" }
```

## 5. 画幅参数（9:16 / 16:9）

镜头画幅由 storyboard / 风格包决定（`pixel-chronicle` 横屏、`case-file` 竖屏），**不由本 skill 默认**。下表是全链路唯一需要按画幅切换的量；其余（美学标准、三闸门、色彩语义、死尾判据）两个画幅通用。

| 环节 | 9:16 竖屏（✅ 2026-07-17 冒烟） | 16:9 横屏（✅ 2026-07-28 冒烟） |
| --- | --- | --- |
| imagegen `size` | `720x1280` | `1280x720` |
| 首帧空色场 `-s` | `1080x1920` | `1920x1080` |
| 尾帧归一 scale/crop | `scale=1080:1920:...,crop=1080:1920` | `scale=1920:1080:...,crop=1920:1080` |
| Seedance `metadata.ratio` | `"9:16"` | `"16:9"` |
| imagegen prompt 画幅句 | `vertical 9:16 locked poster frame` | `horizontal 16:9 locked poster frame` |
| Seedance prompt 镜头句 | `locked-off vertical shot` / `Preserve the 9:16 framing` | `locked-off horizontal shot` / `Preserve the 16:9 framing` |
| 720p 实产尺寸 | 720×1280 | 1280×720 |
| contact sheet `scale` | `180:320` | `320:180` |

`size` 必须是 16 的倍数（见 `produce/references/image-motion.md`），故 imagegen 走 1280x720 而非 1920x1080；1920x1080 只出现在 ffmpeg 首尾帧（lavfi/crop 不受 16 倍数约束）。

### 16:9 实测结论（2026-07-28 首次横屏测试 clip）

三条已知未知的验证结果：

- **摊散风险 → 未发生**。「中央 60% 聚簇 + 外三分之一留空」的约束句成立，锁体与钥匙读作一个聚簇。竖屏靠画幅天然挤，横屏靠这句 prompt 挤——**这句不许删**。
- **组装节奏 → 确有偏前重**。横屏尾段运动量只有全片的 **27%**（竖屏 54%），刚过 25% 下限。横向滑入路径更长这条**被证实**：排产横屏时把「末件在最后一秒落位」写得更重，或把该镜槽位缩短。
- **首尾帧角色 → 横屏成立**。首帧近空场、向 Image2 插值组装。

证据：`projects/_smoke/broll-skills-2026-07-28/evidence/`（cl_h / cl_v 的 QA JSON 与 contact sheet）。

**换画幅、换模型版本、大改 prompt 骨架后仍守测试 clip 纪律**：Gate 3 先只跑 1 条目检再批量，**不许跳过直接批量**——那是静默降级。


## 6. 引擎绑定（9:16 已冒烟验证 2026-07-17）

> 下面命令与模板按 **9:16** 写；做 16:9 时逐项换成上表右列，**其余一字不改**。

### Gate 2 静帧 — GPT-Image-2（契约见 `produce/references/image-motion.md`）

`POST {ARK_VIDEO_API_BASE_URL}/v1/images/generations`，`model: gpt-image-2`，`size` 按画幅（9:16 → `720x1280`；16:9 → `1280x720`；gateway 可能自判尺寸，产出后 ffprobe 记录），`quality: medium`（概念 hero 静帧；纯版式可 low），`output_format: png`。存 `anchors/`。

### Gate 3 视频 — Seedance 首尾帧（契约见 `produce/references/seedance.md`）

```bash
P=projects/<片>
# 尾帧 = 归一静帧；首帧 = 同底色纯空场
ffmpeg -y -i $P/anchors/s03.png \
  -vf "scale=1080:1920:force_original_aspect_ratio=increase,crop=1080:1920" $P/anchors/s03_last.png
ffmpeg -y -f lavfi -i color=c=0x<底色HEX>:s=1080x1920 -frames:v 1 $P/anchors/s03_first.png

python3 tools/seedance.py submit --jobs $P/shots/jobs.json --state $P/shots/state.json --dry-run
python3 tools/seedance.py submit --jobs $P/shots/jobs.json --state $P/shots/state.json
python3 tools/seedance.py poll   --state $P/shots/state.json --out $P/shots/
python3 tools/clip-qa.py $P/shots/s03_raw.mp4 --expect-size 720x1280 \
        --json $P/evidence/collage-qa-s03.json --contact $P/evidence/s03-contact.jpg
```

`jobs.json`：

```json
{ "defaults": {"ratio":"9:16","resolution":"720p","duration":10,"oss_prefix":"kuleshov/<片>/collage"},
  "jobs": [ {"name":"s03","prompt":"<Seedance prompt>",
             "first":"projects/<片>/anchors/s03_first.png",
             "last":"projects/<片>/anchors/s03_last.png"} ] }
```

`tools/seedance.py` 把三条最容易写错的契约固化成会报错的形状：`duration` 必须在 `metadata` 内（顶层会被忽略，恒出 5.04s）、`ratio` 不许省略（省略由上游自判画幅）、越界 duration 提交前本地拦截（越界会在**排队后**才拒且**已计费**）。首尾帧自动过 `tools/oss-upload.sh` 传公网；worktree 无 `.env` 时先 `ln -sf <主仓库>/.env .env`。

**组装类镜头 `duration` 直接要 10s**——5s 组装被用户打回"过得太快"是必然，定格拼装需要呼吸（`seedance.md`）。旧 5s 库存补救走 `ffmpeg setpts=2.0*PTS`，**不用插帧**（插帧出鬼影，毁纸艺质感）。

## 7. 提示词模板

### imagegen（9:16 竖屏 · ✅ 冒烟过）

```
Create a finished editorial paper-collage still for a 9:16 image-to-video B-roll clip. Visual proposition: [一句话视觉命题]. Scene: perfectly flat [颜色] paper field ([hex]) with subtle uncoated paper fiber. Style: premium editorial stop-motion paper collage; black-and-white halftone photographic cut-outs [主体元素], with selective cream-white and [品牌点色] colored cardstock accents. Composition: vertical 9:16 locked poster frame; central subject within the middle 70 percent; generous clean color-field negative space; 3 to 6 large separable paper groups for later assemble-from-empty animation. Materials: visible printed halftone dots, crisp machine-cut edges, thin warm-cream paper keylines, soft low-opacity physical drop shadows. Constraint: [必须一眼看懂的关系]. Avoid: no typography, no readable letters, no numerals, no logos, no watermark, no UI, no subtitles, no glossy 3D, no photoreal environment, no clutter.
```

### imagegen（16:9 横屏 · ✅ 冒烟过）

差异仅在 Composition 段：画幅句改 horizontal、中央 70% 改为**水平中央 60% 的聚簇约束**（抗摊散），并显式禁止沿画幅摊平；其余与竖屏逐字相同。

```
Create a finished editorial paper-collage still for a 16:9 image-to-video B-roll clip. Visual proposition: [一句话视觉命题]. Scene: perfectly flat [颜色] paper field ([hex]) with subtle uncoated paper fiber. Style: premium editorial stop-motion paper collage; black-and-white halftone photographic cut-outs [主体元素], with selective cream-white and [品牌点色] colored cardstock accents. Composition: horizontal 16:9 locked poster frame; central subject clustered within the middle 60 percent of the width, reading as one tight group rather than spread across the frame; the outer thirds stay as clean empty color field; generous clean color-field negative space; 3 to 6 large separable paper groups for later assemble-from-empty animation. Materials: visible printed halftone dots, crisp machine-cut edges, thin warm-cream paper keylines, soft low-opacity physical drop shadows. Constraint: [必须一眼看懂的关系]. Avoid: no typography, no readable letters, no numerals, no logos, no watermark, no UI, no subtitles, no glossy 3D, no photoreal environment, no clutter, no elements spread evenly across the full width, no symmetrical left-right filler.
```

### Seedance 组装（9:16 竖屏 · ✅ 冒烟过）

```
Paper-collage stop-motion assembly. Use Image 1 as the exact empty first frame (a flat [颜色] paper field) and Image 2 as the exact completed last frame. One continuous locked-off vertical shot, no camera movement. Open on the empty [颜色] paper field, then assemble the scene piece by piece with crisp physical stop-motion timing, PACED EVENLY ACROSS THE ENTIRE CLIP: pieces keep sliding in and snapping into place continuously through the whole shot — do NOT finish early, do NOT hold a long static frame; [按顺序描述 3–6 元素如何滑入/卡位/连接], with the final fragments snapping into place in the last second to complete Image 2. Preserve the 9:16 framing, [hex] color field, cardstock accents, uncoated paper grain, halftone dots, cream keylines, crisp cut edges and soft shadows. Restrained tactile 2D paper craft only. No scene cuts, no camera movement, no zoom, no morphing, no new objects, no text, no letters, no numbers, no logos, no watermark, no UI, no sound.
```

### Seedance 组装（16:9 横屏 · ✅ 冒烟过，但偏前重）

差异：`vertical` → `horizontal`、`Preserve the 9:16` → `Preserve the 16:9`，并加一句锁住聚簇（防组装过程把纸片往左右两侧拉开）。

```
Paper-collage stop-motion assembly. Use Image 1 as the exact empty first frame (a flat [颜色] paper field) and Image 2 as the exact completed last frame. One continuous locked-off horizontal shot, no camera movement. Open on the empty [颜色] paper field, then assemble the scene piece by piece with crisp physical stop-motion timing, PACED EVENLY ACROSS THE ENTIRE CLIP: pieces keep sliding in and snapping into place continuously through the whole shot — do NOT finish early, do NOT hold a long static frame; [按顺序描述 3–6 元素如何滑入/卡位/连接], with the final fragments snapping into place in the last second to complete Image 2. Keep every piece inside the central cluster of Image 2 — pieces travel in from off-frame but settle into the middle of the width; do NOT spread the collage across the full width, do NOT add filler pieces in the outer thirds. Preserve the 16:9 framing, [hex] color field, cardstock accents, uncoated paper grain, halftone dots, cream keylines, crisp cut edges and soft shadows. Restrained tactile 2D paper craft only. No scene cuts, no camera movement, no zoom, no morphing, no new objects, no text, no letters, no numbers, no logos, no watermark, no UI, no sound.
```

## 8. Gate 3 后 QA（看组装进程，不只看尾帧）

机器码判走 `tools/clip-qa.py`（规格 / **死尾** / contact sheet）：

| 项 | 判据 |
|---|---|
| 死尾 | 尾 2s 运动量 ≥ 全片中位的 **25%**（相对判据）。**这是宪法红线的码判投影**——Seedance 默认会把组装塞在前段、尾部长时间 hold（实测 s03b v1：~3.0s 就停、留 ~2s 近静止）。用相对量而非绝对阈值：绝对阈值跨不了内容类型（见 `tools/clip-qa.py` 常量处的实测说明） |
| 规格 | 720p 下 9:16 → 720×1280、16:9 → 1280×720；24fps；~5s / 10s；**零音轨** |

人眼再看脚本查不了的：

- 首帧近空场（边缘轻微提前露片可接受）；中段能看到结构/主体**逐件进入**而非整体淡入；无切镜/zoom/3D 漂移；无假字/logo/水印；尾帧≈确认静帧（轻微姿态/细节漂移不影响隐喻语义即通过，**不为此重跑**）。
- **横屏加查一项（摊散）**：纸组是否仍读作**一个聚簇**、左右外三分之一是否保持空色场。摊平成"满屏均匀碎片"= fail，修法同源：先补强 prompt 的聚簇句重生静帧（Gate 2，便宜），静帧本身就摊了就别进 Gate 3。

**批量总览三张图**（多条一起做时必出，单看逐条会漏掉批次级问题）：

```bash
# 全部成片逐秒抽帧 / 全部实际首帧（验真的从空场开始）/ 确认静帧与视频末帧并排
ffmpeg -y -i <run>/final.mp4 -vf "fps=1,scale=180:320,tile=5x1" -frames:v 1 <run>/contact-sheet.jpg
```

- `omni-contact-sheet-all.jpg`、`video-first-frame-all.jpg`、`end-frame-comparison-all.jpg`

**时长调和**：Seedance 实产 ≈5.04s / 10.04s 是常态。compose **尾裁**掉末端残余 hold 到 shot 槽位——前提是组装已铺满、只剩很短 hold；**组装过早完成就得重生或缩短槽位，尾裁救不了**。挂载尾对齐规则见 `seedance.md`。

## 9. 写回 IR

```json
{ "source": { "provider": "collage_broll",
    "params": { "ai_stylized": true, "background_hex": "#...", "accent_colors": ["#..."] },
    "note": "拼贴 b-roll·<一句话隐喻>" } }
```

留痕：`gen` 记 model / 完整 prompt / seed / 首尾帧 / `x-oneapi-request-id` / 实测时长；`qc` 挂 `evidence/collage-qa-<镜>.json`；成本进 `ledger.costs`（1 张 GPT-Image + 1 条 Seedance ≈ $2.7）。选底色、部分通过、带瑕疵放行都进 `ledger.decisions`。

## 10. 什么时候不要用

需要精确图层/遮挡/镜头穿越/可编辑时间线 → HyperFrames；只要 prompt 不要成片 → 直接写；真人产品口播 → 不走本流程；要像素质感 → `pixel-broll`。

## 11. 状态

- **9:16 端到端**：✅ 冒烟验证通过（2026-07-17，`openai-78m-logs` / s03b 碎片聚人形：首帧近空场 → 逐件组装 → 定格成品，720×1280 / 24fps / 5.04s）。
- **16:9 端到端**：✅ **已冒烟**（2026-07-28，`projects/_smoke/broll-skills-2026-07-28`，深绿场 #1E4438 咖啡因锁孔隐喻，横竖各 1 条，即 §5 要求的首次横屏测试 clip）。实测结论：
  - **摊散没有发生**：16:9 prompt 的「中央 60% 聚簇 + 外三分之一留空」约束成立，锁体与钥匙读作一个聚簇。
  - **组装铺开了但偏前重**：横屏尾段运动量只有全片的 **27%**（竖屏 54%），刚过 25% 下限。横屏滑入路径更长这一条已知未知**被证实**——排产横屏时把「末件在最后一秒落位」写得更重，或把该镜槽位缩短。
  - **实产时长 10.042s**，零音轨，规格达标。
  - request-id 见 `projects/_smoke/broll-skills-2026-07-28/runs/`。
- **闸门纪律**：`evals.json` 4 条考卷（改本 skill 的流程或提示词后跑一遍，验四类偷跑：Gate 1 提前出图、Gate 2 提前调视频模型、部分通过被蒙混、模型选择被抛回用户）。
