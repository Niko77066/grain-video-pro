# 引擎知识包 · 数字人（HeyGen Avatar 4，烘焙型）

> 何时读我：storyboard 有镜头路由到 `avatar`（口播/主持/人设 IP）时。

## 接入（已定并冒烟，2026-07-14；契约源自 grain `fal-client.ts` / `fal.ts` + 实测）

- 走 **fal queue 经灵鲸网关**（与 Seedance 的 neodrop 网关不是同一个）：
  - 提交：`POST $FAL_PROXY_BASE/queue.fal.run/fal-ai/heygen/avatar4/image-to-video`
  - 鉴权：`Authorization: Bearer $FAL_KEY`（网关模式；若某天直连 fal.ai，scheme 换成 `Key`——只切 `FAL_PROXY_BASE`/`FAL_KEY` 两个 env 即可整体切换上游）
- 返回 `{ request_id, status_url, response_url }`——注意这些 URL 指向 `queue.fal.run` 原始域，**轮询前把 origin 重写为 `$FAL_PROXY_BASE/queue.fal.run/...`**；
- 轮询 status_url（10–20s 间隔）：`IN_QUEUE → IN_PROGRESS → COMPLETED`；完成后 GET response_url → `{ "video": { "url", "file_size", ... } }`，**拿到立即下载**；
- 计费：submit 响应头 `trace-id` 留痕进 `ledger.costs`。

## 输入契约

```json
{ "prompt": "<场景/氛围描述——不影响台词与口型>",
  "image_url": "<正面头肩/半身照公网URL>",
  "audio_url": "<TTS 音频公网URL>",
  "aspect_ratio": "16:9|9:16|1:1",
  "resolution": "360p|480p|540p|720p|1080p" }
```

- **台词与口型 100% 由 audio_url 决定**，prompt 只辅助场景氛围——旁白/台词永远先走 TTS 轨定稿（音频先行在数字人镜头上是物理约束，不只是纪律）；
- **时长 = 音频时长**，没有 duration 参数——数字人镜头的时长在 audio 阶段即锁定，storyboard 直接绑节区间，不存在时长调和问题；
- audio：MP3/WAV/M4A，**2–60s**，≤5MB；image：JPG/PNG/WebP/GIF/AVIF，公网 URL（本地文件先 `tools/oss-upload.sh`）；
- **`aspect_ratio` 必填**（grain 实测教训：缺省=横屏特写，竖屏栏目会被 compose 加大黑边）。

## 实测记录（冒烟 2026-07-14，task_RnJGk…）

- 4.8s 音频 → 4.844s 视频，口型自然；480p 实际 854×480 / 25fps / h264+aac；
- 推理 72.7s，含排队总墙钟约几分钟（标称 5–30min 是上限心态）；
- **源图比例 = 实际画面占比**：1:1 肖像 + 16:9 请求 → 模型不外扩，直接左右黑边。**形象锚点必须按目标画幅构图生成**（16:9 栏目就生成 16:9 半身构图的肖像），这是 anchors 阶段的硬要求，不是 compose 能救的；
- 样本：`projects/_smoke/avatar-smoke.mp4`（形象锚点 `avatar-portrait.png` 同目录）。

## 人设纪律

- **人设 = 形象锚点图 + 声音档的固定配对**，跨片跨期不换——两者的生成参数全留痕，栏目级资产；
- 形象图走锚点系统生产（GPT-Image-2，`quality: medium` 起步保面部细节），给用户 N 选 1 后锁定；
- 唇同步质量门：M0 人眼验（重点看爆破音与停顿处），后续接 SyncNet（评估金字塔 L2）；
- 声部语法默认位：数字人 = 主持/结论声部，B-roll 与数据卡在其间穿插——整片从头到尾单人对镜头是反模式。
