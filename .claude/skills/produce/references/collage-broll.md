# 引擎知识包 · AI 纸拼贴 b-roll（halftone paper-collage）

> 何时读我：storyboard 有镜头路由到 `collage-broll`——把一句 ~5s 口播/观点句/抽象概念压成一个**视觉隐喻**的氛围 b-roll。
> 来源：内化自开源 skill **`gbro-collage-broll`（pyang5166）**——保留其美学 + 三闸门 + visual-spec + prompt 模板；**引擎从 Gemini Omni Flash + Codex image_gen 重绑到我们的栈（GPT-Image-2 + Seedance 首尾帧）**。2026-07-17 冒烟验证通过（openai-78m-logs / s03b 碎片聚人形：首帧近空场 → 逐件组装 → 定格成品，720×1280/24fps/5.04s）。

## 这门语言擅长 / 不擅长（路由用）

- **擅长**：概念、观点句、抽象隐喻的**氛围 b-roll**；高级编辑风、手作温度；垫在口播下。
- **不擅长（改用 HyperFrames）**：精确文字 / 数字 / 法条 / logo / 收尾落款；可逐层编辑的时间线；真人产品口播。**collage 明确规避文字数字**——要文字就用 HyperFrames **叠层在 collage 上**（overlays 混合层，兼得质感与信息）。

## 美学成功标准（源 skill，已验证）

- 一句话只表达一个清晰隐喻；画面是 3–6 个**可分离大组**（利于从空场组装），不是满屏碎片
- 强烈平坦纯色场（按语意选色）；主体黑白 halftone 照片剪贴为骨架
- 关键卡片/纸张可用红、黄、青、橙、紫、奶油白点色，但服务信息层级、不为彩色而彩色
- 所有纸片：清晰裁切边、奶油白 keyline、低透明柔和阴影、纸颗粒
- 动作 = **assemble-from-empty**（从空场逐件滑入、卡位、组装的定格质感），**不是漂移/晃动/慢 zoom**
- 无字幕、无口播全文、无 logo、无水印、无 UI

## 色彩语义（选底色；一批内"同设计语言、不同底色"）

焦橙/红=时间消耗·劳动·紧迫｜芥末黄=工具·警示｜墨绿=认知·系统·重置｜深紫=规范·沉淀·长期记忆｜青绿=判断·协作·自动执行。

⚠️ **缝合纪律（我们新增）**：collage b-roll 与版式卡（如 daily-brief 纸白场）混排时，底色可各异，但靠**共享的半调 + 奶油白 keyline + 品牌点色（印刷红 #C8451B）+ 统一纸颗粒**缝成一家；防止"拼贴段"与"版式段"割裂成两部片。

## 三闸门（强制——这就是我们"廉价品味注入"的纪律）

- **Gate 1 · 隐喻（免费）**：只输出 核心意思 / 情绪 / 一句话视觉命题 / 3–6 关键物件 / 底色+点色 / 组装顺序 → 停，等用户确认。错隐喻改文字免费。
- **Gate 2 · 静帧（便宜）**：确认隐喻后才写 visual-spec + imagegen prompt，用 **GPT-Image-2** 出静帧 → contact sheet → 停，等用户确认。错静帧重生一张图，远比重跑一条视频便宜。
- **Gate 3 · 视频（才烧钱）**：静帧确认后才用 **Seedance 首尾帧**生成。
- 批量支持**部分通过**：只有确认过的条目进入下一阶段。

## 引擎绑定（我们的栈，已冒烟验证 2026-07-17）

### Gate 2 静帧 — GPT-Image-2（契约见 image-motion.md）
`POST {ARK_VIDEO_API_BASE_URL}/v1/images/generations`，`model: gpt-image-2`，`size` 走 9:16（如 720x1280；gateway 可能自判尺寸，产出后 ffprobe 记录），`quality: medium`（概念 hero 静帧；纯版式可 low），`output_format: png`。存 `anchors/`。

### Gate 3 视频 — Seedance 首尾帧（契约见 seedance.md）
1. 首帧 = 空色场：`ffmpeg -y -f lavfi -i color=c=0x<HEX>:s=1080x1920 -frames:v 1 first.png`
2. 尾帧 = 归一静帧：`ffmpeg -y -i still.png -vf "scale=1080:1920:force_original_aspect_ratio=increase,crop=1080:1920" last.png`
3. 两帧 `tools/oss-upload.sh <file>` 传公网（返回 storage.neodrop.ai URL）。⚠️ worktree 无 .env 时先 `ln -sf <主仓库>/.env .env`。
4. `POST {base}/v1/videos`：
```json
{ "model": "doubao-seedance-2-0-260128", "prompt": "<组装 prompt>",
  "metadata": { "content": [
      { "type": "image_url", "image_url": { "url": "<first url>" }, "role": "first_frame" },
      { "type": "image_url", "image_url": { "url": "<last url>" },  "role": "last_frame" } ],
    "resolution": "720p", "ratio": "9:16", "generate_audio": false, "duration": 5 } }
```
content[0]=@Image1（空场首帧），content[1]=@Image2（成品尾帧）。**首尾帧角色实测成立**：首帧近空场、模型向 Image2 插值组装、结尾定格。

### imagegen prompt 模板（9:16 拼贴静帧）
```
Create a finished editorial paper-collage still for a 9:16 image-to-video B-roll clip. Visual proposition: [一句话视觉命题]. Scene: perfectly flat [颜色] paper field ([hex]) with subtle uncoated paper fiber. Style: premium editorial stop-motion paper collage; black-and-white halftone photographic cut-outs [主体元素], with selective cream-white and [品牌点色] colored cardstock accents. Composition: vertical 9:16 locked poster frame; central subject within the middle 70 percent; generous clean color-field negative space; 3 to 6 large separable paper groups for later assemble-from-empty animation. Materials: visible printed halftone dots, crisp machine-cut edges, thin warm-cream paper keylines, soft low-opacity physical drop shadows. Constraint: [必须一眼看懂的关系]. Avoid: no typography, no readable letters, no numerals, no logos, no watermark, no UI, no subtitles, no glossy 3D, no photoreal environment, no clutter.
```

### Seedance 组装 prompt 模板
```
Paper-collage stop-motion assembly. Use Image 1 as the exact empty first frame (a flat [颜色] paper field) and Image 2 as the exact completed last frame. One continuous locked-off vertical shot, no camera movement. Open on the empty [颜色] paper field, then assemble the scene piece by piece with crisp physical stop-motion timing, PACED EVENLY ACROSS THE ENTIRE CLIP: pieces keep sliding in and snapping into place continuously through the whole shot — do NOT finish early, do NOT hold a long static frame; [按顺序描述 3–6 元素如何滑入/卡位/连接], with the final fragments snapping into place in the last second to complete Image 2. Preserve the 9:16 framing, [hex] color field, cardstock accents, uncoated paper grain, halftone dots, cream keylines, crisp cut edges and soft shadows. Restrained tactile 2D paper craft only. No scene cuts, no camera movement, no zoom, no morphing, no new objects, no text, no letters, no numbers, no logos, no watermark, no UI, no sound.
```

## Gate 3 后 QA（看组装进程，不只看尾帧）

- 首帧近空场（边缘轻微提前露片可接受）；中段能看到结构/主体**逐件进入**而非整体淡入；无切镜/zoom/3D 漂移；无假字/logo/水印；尾帧≈确认静帧（轻微姿态/细节漂移不影响隐喻语义即通过，不为此重跑）；720×1280/24fps/~5s 无声。
- **🔴 死尾检查（宪法红线：禁冻结帧补时长）**：Seedance 默认会把组装塞在前段、尾部长时间 hold（实测 s03b v1：~3.0s 就停、留 ~2s 近静止，YDIF<1）。**必须查**：`ffmpeg -i clip.mp4 -vf "select='gte(t,2)',signalstats,metadata=print:file=-" -f null - 2>/dev/null | grep YDIF`——若尾段 >~0.8s 处于 YDIF<1（近静止）即 **fail**。修法：① 重生时 prompt 强制"铺满整条 clip、末件在最后一秒落位、不许提前完成"；② 光尾裁救不了组装过早的情况（可用运动 < 槽位就得重生或缩短该镜槽位）。freezedetect 阈值太死会漏报，以 YDIF 为准。
- contact sheet：`ffmpeg -y -i clip.mp4 -vf "fps=1,scale=180:320,tile=Nx1" -frames:v 1 contact.jpg`。
- 时长：Seedance 实产≈5.04s 常态；compose **尾裁**掉末端残余 hold 到 shot 槽位（前提是组装已铺满、只剩很短 hold；组装过早完成→回上一条重生）。

## 成本 / 留痕

每条 = 1 张 GPT-Image（响应头 `x-oneapi-request-id`）+ 1 条 Seedance（`x-oneapi-request-id`，满价约 $2.7），全进 `ledger.costs`。first/last PNG、payload、response 一并留痕。

## 什么时候不要用

需要精确图层/遮挡/镜头穿越/可编辑时间线 → HyperFrames；只要 prompt 不要成片 → 直接写；真人产品口播 → 不走本流程。
