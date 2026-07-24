# Review / 交接文档 · 英国和阿根廷：什么仇什么怨

> **状态**：compose v5 draft 已出（`out/draft_v5.mp4`，258.1s），针对用户 v4 三项反馈定点重做。待用户看片。

## v5 相对 v4 改了什么（对应用户 2026-07-18 反馈）

1. **字幕略快于声音** → 根因：`forced_align.py` 分块 emission 拼接每缝重复 125 帧 + 均匀缩放，中段时间戳整体偏早 0.3~0.5s。改**核心区精确平铺**（各块核心 [OVL/2, CHUNK-OVL/2]，帧距固定 20ms）；验证升级为 6 锚点切片转写（40.9s~247.4s 全片，词均在切片开头，零偏）。
2. **音色换 MiniMax 官方 ID** → 从 grain `minimax-voices-zh.tsv`（官方音色快照）取 6 个纪录片/播客向女声候选，韵律初筛（停顿结构+音高动态）→ 决赛两条整轨声纹：`Laid_BackGirl` 0.804 出局（表现力=漂移），**`Chinese (Mandarin)_Gentle_Senior` 0.889/0.908 选定**（官方 Documentary 标签，暖沉稳）。shaonv 版留档 `audio/vo_mmC.mp3` 备退。音轨 256.7s（语速更从容），BGM 相应加长到 256.2s（`bgm_v5.mp3`）。
3. **素材重复画面 + 足球特写过久/黑屏** → builder v5 (`build_compose_v5.py`) 硬性 **一素材全片一次**（41 切段 41 素材，断言零重复），切段放宽 2.2~5s，素材窗尾留 0.8s 余量防暗尾黑闪；池耗尽走 fallback 链，**关键素材按段预留**（azteca 航拍→墨西哥段、双夜景→金句收尾、横幅新闻→"横幅在亚特兰大"位，防连锁挪用）；banner 像素复用取消，改真实横幅新闻 ≤3.2s；缝隙 <1.3s 自动并入前段。

---

## （下为 v4 记录，背景保留）

## v4 相对 v3 改了什么（对应用户 2026-07-17 反馈）

1. **音色漂移** → 实测对比 seed-audio vs MiniMax 长音频：
   - seed-audio `original_duration=120` **硬上限坐实**（整条 1215 字：两次 500 `TextPromptAgentResultError`/截断；790 字被压进 109s 语速失真 6.4 字/s）；两段拆分跨段声纹 **0.824**（漂移明显）。长音频能力不成立，出局。
   - MiniMax speech-2.8-hd 整条 single-pass 三候选（shaonv 1.0 / 1.05 / 1.0+calm）声纹两两对比，**选定 shaonv + calm + speed 1.0**（244.6s，min 0.904 / mean 0.928，追平 v3 一致性且语速不赶）。whisper 反查全文无念错（差异全是数字格式/同音字转写噪声）。
   - 天花板提示不变：要 >0.95 需用户提供真人音源走 MiniMax 克隆（`ndclone-`）。
2. **音画/字幕不同步** → **根因坐实并根治**：v3 字幕是"剧本字数→whisper 转写字数"按**全局比例**映射（`gen_captions_v2.py:44`），whisper 把中文数字写成阿拉伯数字（"四十四"→"44"），全片差 ~80 字，中段字幕系统性拉歪数秒。v4 改**已知文本强制对齐**：`scripts/forced_align.py`（wav2vec2-zh CTC + torchaudio.forced_align，40s 块/5s 重叠拼接），剧本 1076 字每字直拿真实戳（1069 直对齐 + 7 OOV 插值），silencedetect 交叉验证中段零漂移。字幕 `gen_captions_v3.py`（1:1，无估算），画面 cue `find_cues_v2.py` → `audio/cues_v4.json`。
3. **像素动画太快/不匹配** → 8 条 5.04s 旧镜头 `setpts 2x` 降到 10.03s（15fps 有效帧=定格质感）；挂载**尾对齐**（`media_start = clip_len - mount_len`，组装完成拍点落在对应文案上；belgrano 例外头对齐防空纸场撞沉船文案）。**新增 4 条** 10s 原生慢组装：s02_map（两国点亮拉线）/s03_trade（贸易线）/s04_ruler（距离标尺）/s05_9802（点球）——`shots/backfill_v4.json`。像素叙事覆盖 41s → **105.8s**。
4. **真实画面重复/相关性差** → broll3 重构（36 条 + broll2 留 10 剔 9）：Pexels/Pixabay 只做纯空镜；叙事素材走 archive.org/Wikimedia 公域（1806 版画、1928 阿根廷纪录片×3、1920 伦敦、1982 IWM/AP 档案）+ **APIhub youtube 下载**（Sky/AP 2026 半决赛横幅新闻，标 broadcast-risk 限 ≤3s 闪切）。池按 desc 关键词过滤防时代错位（1806 段禁 1920s 汽车街景）、全局轮换 + 复用时错开 media-start 防同画面重复（34 素材/最多复用 2 次，v3 是 28 素材大量循环）。manifest（含 gaps 7 项、license 分级）：`compose/assets/broll3/manifest.json`。
5. **BGM** → MiniMax music-2.6 生成 82.6s → 交叉淡化拼 243s（-29.7 LUFS / LRA 4.2），composition 内挂 `data-volume 0.23`（低旁白 20 LU），随渲染一体输出。`compose/assets/bgm_meta.json`。

## 当前产物
- **draft_v4**：`out/draft_v4.mp4`（246.0s = VO 244.6 + 尾黑场；1280x720/30fps）
- 抽帧自查：`out/v4_review1.jpg` / `v4_review2.jpg`（两轮，第二轮修掉 1806 段 1920s 街景、"昨天"段夜景雕像/晴天国旗错位、belgrano 空头）
- 历史：draft.mp4(v1) / draft_v2 / draft_v3

## 关键资产（v4）
- 音轨：`audio/voiceover_v4.mp3`（=compose/assets/voiceover.mp3，mmC）；候选与 seed-audio 实验响应都在 `audio/`（vo_mmA/B/C、vo_seedA/B、response_full_seed*）
- 对齐：`audio/timeline_fa.json`（逐字 1076 戳）+ `audio/cues_v4.json`（52 锚点）
- 字幕：`compose/assets/captions_data.js`（108 句）
- 像素：`compose/assets/s0*_s.mp4`（13 挂载用；8 降速 + 4 新 + banner 复用）
- compose：`compose/index.html`（v4，由 `scripts/build_compose_v4.py` 生成——改 PIX/POOL_SEGS/TAG_FILTER/BADGE 后重跑）

## 未做 / 待办
1. 用户看片 draft_v4 → 反馈定点改
2. 响度归一 -14 LUFS（渲染后处理，命令见下）+ `docker high` final render → `out/final.mp4`
3. ⑩ deliver：发布包（双平台）+ `/video-score` 登记 + 成本单价回填（Seedance/GPT-Image 无计价字段，x-oneapi-request-id 在 backfill_v4.json 可反查；BGM 两笔 trace 见 bgm_meta.json）
4. broadcast-risk 素材使用告知用户（Sky/AP/1966 转播/1982 AP 档案共 9 条，都 ≤3s 闪切；manifest 有全清单）
5. 响度归一命令：`ffmpeg -i out/draft_v4.mp4 -c:v copy -af loudnorm=I=-14:TP=-1.5:LRA=11 -c:a aac -b:a 192k out/final.mp4`

## 凭据/工程坑（沿用 + 新增）
- 沿用 v3 记录（Pexels UA/Referer、Seedance @ref、HyperFrames GOP12/muted）。
- 新增：volc openspeech 认证头是 **`X-Api-Key`**（不是 Bearer）；new-api 网关封 python-urllib UA（轮询用 curl）；torchaudio forced_align 分块 emission 要在重叠中点拼接。
