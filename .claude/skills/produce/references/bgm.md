# 引擎知识包 · BGM（背景音乐床）

> 何时读我：audio 阶段有 BGM 需求时（>10s 的解说片默认该考虑）。蒸馏自 `media-use/audio/references/bgm.md` + 荆华第二片实战（2026-07-20 用户打回第一版）。

## 铁律：床要纹理，不要旋律

BGM 的职责是**垫底氛围**，不是被听见。**主旋律 / 明显节拍 / 音效 hook 会跟人声抢注意力**——荆华第二片第一版 prompt 写了"钟摆 tick + glitch + ominous"，被用户判"影响观感"。

- **prompt 只描述纹理**：软 sustained pad + 低 ambient drone、**无主旋律、无鼓、无节拍**、平淡低动态、loop-friendly、明确"neutral bed to sit under a spoken voiceover, no build, no climax"。
- **按行业/题材选基调**（media-use 归纳）：fintech/金融=calm cinematic + soft strings + subtle piano；tech/cyber/AI 安全=atmospheric electronic，restrained，冷、专业、克制（**不要 ominous/tense/glitch，那是有性格，抢戏**）；~90 BPM、MINOR。
- **反面词表（prompt 里禁）**：lead melody、prominent drums/beat、tension stabs、glitch SFX、build-up、climax、bright/uplifting（除非片子确实要）。

## 音量：压在旁白下 18–22 LU

- post-mix 计算：`目标BGM_LUFS = 旁白_LUFS − 20`（media-use 默认床 ≈ -18dB；荆华第二片取 -22LU 更收）。
- 反算音量因子：`volume = 10^((目标BGM_LUFS − BGM原始_LUFS)/20)`，`amix=inputs=2:normalize=0` 后整体 `loudnorm I=-14:TP=-1`。
- 混音结构：`[voice]full` + `[bgm]volume=<factor>` → amix(normalize=0) → loudnorm。视频流 copy（保确定性渲染），只重编码音频。

## 接口：fal minimax-music/v2.6（本项目 BGM 通路，用户指定）

- `POST $FAL_PROXY_BASE/queue.fal.run/fal-ai/minimax-music/v2.6`，`Authorization: Bearer $FAL_KEY`；body `{prompt, lyrics:"", is_instrumental:true}`。
- **prompt ≤ ~300 字**（超长报 `input_value_error`）；**`is_instrumental:true`** 保证无人声。
- 提交返回 `{request_id, status_url, response_url}`（指向 queue.fal.run 原始域，轮询前把 origin 重写为 `$FAL_PROXY_BASE/queue.fal.run/...`）；轮询 status 到 COMPLETED，结果 `audio` 字段是 mp3 URL；$0.15/次。
- 产物是整曲（100–320s 不定）；裁 82s 床（跳开头 intro 几秒 + 2s 淡入 / 3s 淡出）再 post-mix。

## 出厂

- BGM 是可选层，失败不阻断渲染（旁白+SFX 照出）。
- 记 `film.json.audio.music`：provider / prompt_file / request_id / 原始+床文件 / mount(volume+目标LU) / note。成本进 `ledger.costs`。
- 混完必复测：`loudnorm print_format=json` 确认整体 -14 LUFS / ≤-1 dBTP，且 BGM 主观垫得住不抢戏（评委 D5）。
