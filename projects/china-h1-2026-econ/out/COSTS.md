# 成本小结 · 《经济半年报》4.7% 背后的两组数字

> 汇总自 `film.json.ledger.costs`。**标注为估算的项目**：neodrop / fal 网关不在响应里回单价，只回 request_id 与 token 用量，
> 故 gpt-image-2、MiniMax TTS、HeyGen Avatar 4 三项按各自公开价折算，逐条在备注里写明是估值——不把估算写成实付。

| id | 阶段 | 项目 | 模型 / 通路 | USD |
|---|---|---|---|---|
| `c001` | anchors | 主播形象锚点 3 候选 | gpt-image-2 (neodrop) | 0.18 |
| `c002` | audio | TTS 音色探测 6 短样 + 2 条整片候选 | speech-2.8-hd (MiniMax via neodrop) | 0.03 |
| `c003` | motion | 数字人 3 镜（HeyGen Avatar 4） | fal-ai/heygen/avatar4/image-to-video | 0.90 |
| `c004` | motion | 实拍视频 6 条 + 实拍图片 3 张 | Pexels API 检索 | 0.00 |
| `c005` | compose | 本地 Docker 渲染（1920x1080 / 30fps / 82s / quality=high） | hyperframes-renderer:0.7.64-arm64-corefix | 0.00 |
| | | | **合计** | **1.11** |

预算上限：用户未设（`meta.budget.cap_usd = null`），只记账不熔断。

## 备注

- **c001**：1792x1008 quality=medium ×3，各 4632 output image tokens。网关未回单价，按 OpenAI 公开 gpt-image 中质量横幅价 ~$0.06/张估算，标注为估值。
- **c002**：短样 6×20 字 + 整片 2×358 字。网关未回单价，按公开字数价估算。
- **c003**：6.94s + 5.57s + 3.60s = 16.11s 成片时长。网关未回单价，按 HeyGen Avatar4 公开秒级价估算，标注为估值。
- **c004**：Pexels 免费授权（license=pexels），逐条记 pexels_id 与页面 URL 于 footage/manifest.json。
- **c005**：自有算力，无 provider 计费。墙钟约 8 分钟（2459 帧）。

## 未计入金额的资源

- **Pexels 实拍素材**（6 视频 + 3 图片）：免费授权，`license=pexels`，逐条 `pexels_id` 与页面 URL 见 `footage/manifest.json`。
- **本地 Docker 渲染**：自有算力。两次整片渲染（初版 + G2 回炉后重渲），各约 8 分钟 / 2459 帧。
- **对齐与转写**：wav2vec2-zh CTC 强制对齐、mlx-whisper large-v3-turbo 回转写、speechbrain ECAPA 声纹比对，均为本机推理。
