# 引擎知识包 · 锚点生产（GPT-Image-2）与图片动效（声明型）

> 何时读我：anchors 阶段开工前；storyboard 有镜头路由到 `image-motion` 时。

## 接入（已定并冒烟，2026-07-14）

- 网关：**与 Seedance 同一把 key、同一个 neodrop 网关**——`$ARK_VIDEO_API_BASE_URL` + `$ARK_VIDEO_API_KEY`（仓库根 `.env`）。
  ⚠️ 不要用 `.env` 里的 `OPENAI_*` 那组（灵鲸网关，其分组无 gpt-image-2 渠道，503 `model_not_found`）；
- 文生图：`POST {base}/v1/images/generations`（JSON）；图生图/参考图编辑：`POST {base}/v1/images/edits`（multipart，`image[]` 文件最多 16 张，其余字段同）：

```json
{ "model": "gpt-image-2", "prompt": "...", "quality": "low|medium|high",
  "output_format": "png|jpeg", "size": "1024x1024", "n": 1 }
```

- `output_format` **禁 webp**（Azure 系部署 400 invalid_value）；`size` 是 `宽x高`（16 的倍数），省略=auto；
- 响应主形态 `data[0].b64_json`，部分渠道回 `data[0].url`——两种都要处理；`usage` 可能为 null；
- 429/5xx 指数退避重试 ≤3 次；响应头 `x-oneapi-request-id` 留痕进 `ledger.costs`；
- **实测（样本 `projects/_smoke/gpt-image-smoke.png`）**：`quality: low` 即可产出合格版式帧，中文文字渲染完整无碎裂——版式类锚点用 low 起步，角色/产品锚点再上 medium/high。

## 一、锚点生产（先锁"长什么样"，再谈"怎么动"）

核心原则："如果角色表或关键帧不稳定，动作步骤会继承这种不稳定"——一致性问题全部在**便宜的图像阶段**解决。图便宜，多轮迭代 + 给用户 N 选 1，别到视频阶段返工。

| 锚点类型 | 内容 | 用途 |
|---|---|---|
| character sheet | 角色多角度（正/侧/背）+ 表情集 | Seedance @ref 保脸 |
| product / prop sheet | 产品多角度；**道具合图**：多件道具拼一张白底图 | 1 个 @ref 槽位盖 N 件道具（参考位只有 9 个，合图省槽位） |
| style frame | 2–3 张定调帧（色板/光感/质感） | 全片风格锚；HTML 段 CSS 变量取色来源；统一 LUT 基准 |
| keyframe | 关键镜头首帧/尾帧 | Seedance 首尾帧控制；高价值镜头构图锁定 |
| avatar portrait | 数字人形象照（正面头肩/半身，**按目标画幅构图**：16:9 栏目生成 16:9 构图） | HeyGen Avatar 4 驱动图；人设 IP 跨片一致的唯一来源（见 avatar.md） |

生产要点：
- GPT-Image-2 擅长角色表、故事板页、文字渲染、信息密集构图；
- **标题 / logo 这类"动起来就碎"的元素单独生成静态资产，后期叠加**（overlays 层），不进视频生成；
- 每张锚点记录完整生成参数（模型/seed/prompt/参考图）回填 `anchors[]`，可复现可微调；
- 锚点要给 Seedance/数字人当 `@ref` 时，用 `tools/oss-upload.sh projects/<片名>/anchors/<文件>` 上传并把返回的公网 URL 回填 `anchors[].cdn_url`（本地文件是真身，URL 是引用副本）；
- 验收过的锚点未来可提升为跨片资产（M0 先留在片内，别删）。

## 二、图片动效（声明型——在 HyperFrames 里做，不预烘焙 mp4）

Ken Burns / 视差 / 多图 crossfade 一律写成 HyperFrames 声明式元素。刻意决策，三个理由：**可调**（节奏不对改一个缓动，不重生成）、**确定性**（帧级复现）、免一次转码。

参数手感（与翻译总表联动）：

| 感受 | Ken Burns 参数 |
|---|---|
| 干脆 / 有能量 | 时长 ≤ 3s，位移 ≥ 8%，ease `power2.out` |
| 沉稳 / 抒情 | 时长 4–6s，位移 3–5%，linear 或极缓 ease |

纪律：
- 属"降级运动"，**不计入运动占比**；
- **连续使用 ≤ 2 镜**（防幻灯片化，storyboard 自查第 4 项）；
- 单图动效时长 > 6s 必须换构图或加前景视差层，禁一张图从头缓推到尾；
- 图与图 crossfade ≤ 0.5s，超过就是在拖节奏。
