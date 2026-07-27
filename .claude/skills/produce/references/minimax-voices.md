# 引擎知识包 · MiniMax 官方音色（实测固化表）

> 何时读我：长片（>120s）TTS 必走 MiniMax 官方音色（seed-audio 硬上限 120s + 分节漂移，见 `tts-audio.md`）时——**不再裸猜音色 id**，从本表按需调用。
> 由来：2026-07-20 用户指令"做实验固化比较稳的音色 id"。grain 的 `minimax-voices-zh.tsv` 真相源不在本机，故用**探测 + ECAPA 声纹实测**建此表。

## 接口（按需调用）

`POST $MINIMAX_MUSIC_BASE_URL/audio/speech`（= `https://new-api.neodrop.ai/v1`，OpenAI 兼容网关），`Authorization: Bearer $MINIMAX_MUSIC_API_KEY`：

```json
{ "model":"speech-2.8-hd", "voice":"<下表 voice_id>", "input":"<全文一次>",
  "metadata":{ "audio_setting":{"format":"mp3"},
               "voice_setting":{"speed":1.0,"emotion":"calm","english_normalization":true},
               "language_boost":"Chinese" } }
```

响应体 = 二进制 mp3（网关忽略 `response_format:hex`，直接 `curl -o out.mp3`）；无时长上限、不带时间戳（对齐走 forced-alignment）。**改一个字整条重生成**。

## 已验证 voice_id（2026-07-20 探测）

有效：`Chinese (Mandarin)_Warm_Girl` / `_Soft_Girl` / `_Sweet_Lady` / `_Gentle_Youth` / `_Gentle_Senior` / `_Lyrical_Voice` / `_Mature_Woman`。
无效（报 `2054 voice id not exist`）：`Chinese (Mandarin)_Kind-hearted_Girl`（裸猜就会中这种）。命名规律 `Chinese (Mandarin)_<Descriptor>`，但**必须探测确认存在**（短生成 → ffprobe 有时长 = 有效）。

### 男声补测（2026-07-27 探测，china-h1-2026-econ 男主播财经片）

上表全是女声。做男声片时补探如下 6 个 id，**全部有效**（短样本 20 字均正常返回 mp3）。性别按 F0 中位数判（自相关法，16kHz 单声道，70–400Hz 搜索窗）：

| voice_id | F0 中位 | F0 IQR | 判定 |
|---|---|---|---|
| `Chinese (Mandarin)_News_Anchor` | 198.8 Hz | [168, 223] | ⚠️ **女声** |
| `Chinese (Mandarin)_Male_Announcer` | 127.0 Hz | [103, 142] | 男声 |
| `Chinese (Mandarin)_Radio_Host` | 131.1 Hz | [112, 157] | 男声 |
| `Chinese (Mandarin)_Reliable_Executive` | 108.8 Hz | [91, 119] | 男声 |
| `Chinese (Mandarin)_Gentleman` | 99.4 Hz | [87, 110] | 男声 |
| `Chinese (Mandarin)_Refreshing_Young_Man` | 118.5 Hz | [96, 140] | 男声 |

> ⚠️ **坑：`Chinese (Mandarin)_News_Anchor` 是女声。** 名字最像"男主播"，实测 F0 中位 198.8 Hz，性别与直觉相反。做男主播片千万别按名字选它——**名字不代表性别，仍须实测**。

## 声纹一致性实测（ECAPA，6 窗 ×8s，两两 cosine）

同一段 ~80s 单次生成内，6 个均布 8s 窗的 speechbrain `spkrec-ecapa-voxceleb` 两两相似度：

| voice_id | min | mean | 备注 |
|---|---|---|---|
| **Chinese (Mandarin)_Warm_Girl** | **0.862** | **0.903** | **最稳；年轻温暖女声=品牌嗓匹配 → 长片首选** |
| Chinese (Mandarin)_Gentle_Senior | 0.820 | 0.866 | 校准锚（tts-audio 记 0.889，见下方口径差）；偏年长 |
| Chinese (Mandarin)_Sweet_Lady | 0.791 | 0.856 | |
| Chinese (Mandarin)_Soft_Girl | 0.790 | 0.857 | |
| Chinese (Mandarin)_Gentle_Youth | 0.745 | 0.853 | 本组最不稳 |
| **Chinese (Mandarin)_Male_Announcer** | **0.858** | **0.894** | 男声决赛 #1（2026-07-27）；≈ Warm_Girl、高于校准锚 → **男声长片首选** |
| Chinese (Mandarin)_Radio_Host | 0.759 | 0.839 | 男声决赛 #2（2026-07-27）；低于校准锚 0.820 → 出局 |

**判读（重要）**：本次测得的**绝对值比 tts-audio 参考协议低 ~0.07**（同一 Gentle_Senior：本测 0.820 vs 参考 0.889）——窗口策略/样本长度不同所致。所以**别拿参考的 0.88 当本测的硬线**，按**相对锚**判：`Warm_Girl 0.862 > 校准锚 Senior 0.820`，即 Warm_Girl 在同口径下至少不逊于"已判可用"的 Senior，且更贴品牌 → **固化为长片首选**。

**男声两行同口径判读（2026-07-27）**：用 `tools/minimax-voice-ecapa.py` 原样跑（358 字 / ~80s 整片单次生成，6 窗 ×8s 两两 cosine），沿用同一相对锚 `Gentle_Senior min 0.820 = 已判可用线`：`Male_Announcer 0.858` 与固化首选 `Warm_Girl 0.862` 基本持平且高于校准锚 → 可作男声长片首选；`Radio_Host 0.759` 低于校准锚 → 出局。语速实测 **4.37 字/s**（`speed=1.0`），落在协议记的 4.2–4.8 区间内。

## 结论 & 待办

- **长片（>120s）默认音色（女主播）：`Chinese (Mandarin)_Warm_Girl`**（品牌年轻温暖女声 + 本组最稳）。备选 `_Gentle_Senior`（更年长、更沉稳的题材用）。
- **长片（>120s）默认音色（男主播）：`Chinese (Mandarin)_Male_Announcer`**（男声决赛最稳，min 0.858 ≈ Warm_Girl）。备选 `_Radio_Host`——但它低于校准锚，非必要不用。实证片：`projects/china-h1-2026-econ`（2026-07-27 男主播财经片）。
- 上面两条是**并列的两个默认**，不是主备关系：**按片子的主播性别选**（女主播 → Warm_Girl，男主播 → Male_Announcer），不存在"全局唯一默认音色"。
- **诚实的未完项**：① 本测样本 ~80s，**未进 >120s 漂移区**（MiniMax 固化的真正战场）——首用长片前补一次 >120s 单次生成的 ECAPA 复测；② 单次生成、未测 seed 方差；③ 音色"耳听像不像品牌嗓"仍需用户耳判拍板（如首片 seed-audio 选 take 那样）。
- **男声这批同样的未完项（2026-07-27）**：① 决赛样本 ~82s，**同样未进 >120s 漂移区**——`Male_Announcer` 首用 >120s 长片前，补一次 >120s 单次生成的 ECAPA 复测；② 单次生成、未测 seed 方差；③ 另 4 个男声（`_Reliable_Executive` / `_Gentleman` / `_Refreshing_Young_Man` / 以及女声 `_News_Anchor`）只过了存在性 + F0 性别探测，**未进 ECAPA 决赛**，换音色前需补测。
- 复现脚本留档：探测 + 长样 + `ecapa.py`（scratchpad/minimax）；下次可直接改 voice 列表重跑。
