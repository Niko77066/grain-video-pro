# 引擎知识包 · TTS 与音频先行

> 何时读我：audio 阶段开工前；storyboard 需要节拍网格时；compose 混音时。

## 为什么音频先行

文字估时是 OpenMontage 时长反馈环（TTS 超时 → 打回重写）的病根。顺序倒过来：**旁白先定稿，视觉对齐真实音频**。`audio/timeline.json` 定稿后就是全片的时钟，任何视觉时长争议以它为准。

## 🔴 引擎路由先看时长（2026-07-18 英阿片实战定版）

| 旁白总长 | 引擎 | 理由 |
|---|---|---|
| ≤ 120s | seed-audio-1.0 **整片一次生成**（下节） | 单次调用内音色一致；描述式声音档灵活 |
| > 120s | **MiniMax speech-2.8-hd 官方音色 single-pass**（必须） | seed-audio `original_duration=120` 是**硬上限**（超长：500 报错或被压缩语速塞进 120s，790 字→109s 失真）；分节生成跨段声纹 0.82 级漂移且 `reference/speaker` 锁定字段被接口静默忽略 |

**MiniMax 长片契约**：`POST {MINIMAX_MUSIC_BASE_URL}/audio/speech`（new-api 网关，OpenAI 兼容），`Authorization: Bearer`，body `{model:"speech-2.8-hd", voice:<官方音色id>, input:<全文一次>, response_format:"hex", metadata:{audio_setting:{format:"mp3"}, voice_setting:{speed:1.0, emotion:"calm", english_normalization:true}, language_boost:"Chinese"}}`——响应体即二进制 mp3。无时长上限（实测 257s 单次），无审核拦截，**代价：不带时间戳**（对齐走 `forced-alignment.md`）。

### 官方音色选型协议（别再用 shaonv 这类旧别名裸猜）

1. **音色表真相源**：grain `packages/db/prisma/seed-data/tts-voices/minimax-voices-zh.tsv`（官方全量快照，voice_id/gender/age/use_cases）。按 use_cases 先筛（Documentary / Corporate & Narration / Podcasts）。**tsv 不在本机时/日常复用：查 `references/minimax-voices.md`——已探测有效 id + ECAPA 声纹排名的实测固化表，长片默认 `Chinese (Mandarin)_Warm_Girl`，复现脚本 `tools/minimax-voice-ecapa.py`。**
2. **韵律初筛**（一节文本 × 每候选）：停顿数与总停顿时长（贴句读=自然）、音高中位与 IQR（IQR 过小=平板电音味，过大警惕漂移）、语速 4.2–4.8 字/s。
3. **整轨声纹决赛**（全文 × 前 2 名）：ECAPA（speechbrain spkrec-ecapa-voxceleb）全片 6 窗两两比对，**pairwise min ≥ 0.88 才准用**——表现力强的音色往往漂移（实测 Laid_BackGirl min 0.804 出局）；纪录片片型实证可用：`Chinese (Mandarin)_Gentle_Senior`（min 0.889，Documentary 标签）。
4. **内容 QA**：whisper 独立转写 diff 剧本——中文数字→阿拉伯数字、同音字是转写噪声不算错；真吞字/念错才打回。
5. 天花板：MiniMax 公共音色整片声纹 0.85–0.91 是生成式常态；要 >0.95 用真人音源克隆（`ndclone-` 前缀，网关账号隔离）。
6. 改一个字也**整条重生成**（禁分节补丁拼接），并重跑对齐全链。

## 接入：火山引擎 seed-audio-1.0（短片 ≤120s 用）

- 端点：`POST https://openspeech.bytedance.com/api/v3/tts/create`（**同步**，非流式）
- 鉴权：单 header `X-Api-Key: $VOLC_TTS_API_KEY`，key 在仓库根 `.env`（gitignored，禁入库）；控制台管理页 console.volcengine.com/speech/new/setting/apikeys
- 硬限制：单次输出 ≤ **120s**；`text_prompt` ≤ **3000 字符**；按 `original_duration` 秒计费
- 返回：`url`（**有效期 2 小时，拿到立即下载**）或 `audio`（Base64）；`duration` / `original_duration`
- ⚠️ 曾踩坑：curl 传 JSON 文件要用 `--data-binary @file`，`--data-raw` 不解析 `@`

请求模板（每次调用的完整 payload 与响应都留痕到 `film.json.ledger`）：

```bash
source .env && curl -sS -X POST 'https://openspeech.bytedance.com/api/v3/tts/create' \
  --max-time 300 -H 'Content-Type: application/json' -H "X-Api-Key: $VOLC_TTS_API_KEY" \
  --data-binary @payload.json
```

```json
{
  "model": "seed-audio-1.0",
  "text_prompt": "<声音档描述>朗读：“<旁白文本>”",
  "audio_config": { "format": "mp3", "sample_rate": 48000, "pitch_rate": 0,
                    "speech_rate": 0, "loudness_rate": 0, "enable_subtitle": true },
  "watermark": {}
}
```

### text_prompt 纪律（Kuleshov 专用约束，比 API 能力更严）

seed-audio-1.0 是生成式音频模型：能在一条音频里混环境音、BGM、多角色。**我们禁用这些能力于旁白轨**——旁白轨必须干净（混音契约：音乐/音效独立轨、独立闪避），所以：

- 旁白 `text_prompt` 只写两样：**声音档描述 +「朗读：」+ 文本**；禁止写音效/音乐/多角色标注；
- 声音档描述模板固定在风格包里（如 daily-brief：`一位专业的中文新闻播报员（中年女性，普通话，冷静克制，语速中快）`），跨期逐字复用；
- BGM / 音效**可以**用同一接口单独生成（独立调用、独立轨、独立留痕）——这是白捡的能力，音乐选型时优先考虑。

### 声音一致性（跨节、跨片）

纯文本描述模式下**分节生成音色会漂移**。规则：
- 60s 片 ≤ 120s 上限 → **整片旁白一次生成**（默认）；
- 必须分节时（长片/单节重做），用 `references` 锚定：`speaker`（豆包 2.0 音色 ID）或 `audio_url`/`audio_data`（≤30s 参考音频，可用本栏目首期成品旁白截段——人设声音资产化）；三者互斥只填一个；
- 单节重做后**必须回听接缝两侧**确认音色无跳变。

### 时间戳（2026-07-14 冒烟实测核实）

`enable_subtitle: true` → 响应带**逐字级**时间戳，单位毫秒：

```json
"subtitle": { "sentences": [ {
  "start_time": 193, "end_time": 2072, "text": "库勒肖夫链路冒烟测试。",
  "words": [ { "start_time": 193, "end_time": 340, "text": "库" }, ... ]
} ] }
```

- **audio_timeline 直接从响应构建**：sentences → 分节区间，words → 逐字轴；毫秒转秒；
- 标点也作为 word 条目返回（时长为 0 或极短），构建时轴时过滤；
- **WhisperX 不再承担对齐**，只保留一个用途：回转写校验（G1 门的 ≥95% 是拿**独立转写**对比剧本——TTS 自带字幕反映的是"想读什么"，不是"实际读出了什么"，不能作为自己的证据）。

### 实测记录（冒烟 2026-07-14）

- 响应同时带 `url` 和 `audio`(Base64)——**直接解码 Base64**，省一次下载且不受 2h 过期约束；
- ffprobe 核实：mp3 / 48kHz / 立体声 / 128kbps，时长与 `duration` 字段一致（4.8s）；
- 开通服务后有 **~20s 授权传播延迟**（期间报 `45000030 not granted`，重试即可）；
- 样本：`projects/_smoke/tts-smoke.mp3`。

## 字数预算表（script 阶段硬校验）

| 语言 / 密度 | 60s 预算 | 说明 |
|---|---|---|
| 中文 · 常速叙事 | 220–260 字 | explainer 默认 |
| 中文 · 快报体 | 280–320 字 | news_recap，语速指令调快 |
| 英文 · 常速 | 130–150 词 | |
| 英文 · news 密度 | 165–180 词 | |

超预算砍内容，不掺水、不指望 TTS 加速救场。

## TTS 表演指令写法

每节剧本附带：语速（常速 / 快 / 慢）、停顿点（用 `……` 或 SSML break 标注）、重音词（**加粗**）、语气（陈述 / 设问 / 收束）。忌"表演腔"——宪法条款：宁可平实克制。

## 强制对齐（audio_timeline 的来源）

**必读 `forced-alignment.md`**：剧本已知 → wav2vec2-zh CTC `forced_align` 逐字真实戳（1:1 零估算）。**禁用** whisper 转写戳做字幕/画面映射（中文数字转写差异必致中段漂移——英阿片 v3 反例）。seed-audio 短片自带逐字 subtitle 可直接用；MiniMax 长片必走 forced_align。

**G1 自查（不过必须重做，禁放行）**：
- 回转写文本 vs 剧本，词准确率 ≥ 95%（低于线 = TTS 吐词有问题或音频损坏）；
- 时长：**不设硬门**（2026-07-16 用户拍板去除"时长锁"）——音频/内容自然定长，只记录实际总时长、视觉对齐它；不得为凑预设秒数拉长/砍内容或偷偷变速。字数预算表仅作规划估值与内容控水，不作通过门。

无法安装对齐工具时的降级：按节用 `ffprobe -show_entries format=duration` 取节级时长 + 句级均分估算，**标记 DEBT**（分镜只能绑到节级精度），出厂前补齐。

## 音乐（有 BGM 需求才读）

- 选曲后记录：BPM、段落结构（intro/verse/chorus）、能量曲线（低/中/高分段）；
- 卡点片：storyboard 的剪辑点布在节拍网格上，chorus 对应视觉能量峰值；
- 授权来源记入 `ledger`（provenance 习惯从 M0 养成）。

## 混音契约（compose 阶段执行，全部机器可验）

- 旁白是主轨；音乐自动闪避（旁白在场时 -12 dB，闪避攻击/释放 ≈ 0.3s/0.8s，风格包可覆写）；
- 生成视频的原生音频只保留环境声层，≤ **-18 dB**；
- 成片响度归一 **-14 LUFS**（`ffmpeg loudnorm`），真峰 ≤ -1 dBTP；
- review 阶段用 ffmpeg `loudnorm print_format=json` 出示证据。
