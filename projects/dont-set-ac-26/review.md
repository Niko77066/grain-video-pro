# Review · 空调别开 26 度（v3 出厂自查）

**成片 `out/final.mp4`=v3** · 198.9s · -14.23 LUFS/TP-1.50 · 渲染机。修 v2 用户反馈：
| 反馈 | 修法 | 验证 |
|---|---|---|
| 字幕/tts/画面完全错乱 | **根因**：换B音色后 compose/assets/voiceover.mp3 没同步(仍v1 A,185.6s)→渲染用A音频跑B时间轴。已改B | 5锚点切片转写全对齐 ✓ |
| 左上小标题不需要 | 去掉 #logo 水印 | 渲染抽帧确认无 ✓ |
| 中间内容叠加可读性差 | 温度带 26℃卡中缝(不压band文字)+折中数移下方 | 渲染抽帧确认 ✓ |
| BGM 有人声哼唱 | song模型(minimax)会哼→换器乐原生 **MusicGen**(无人声能力),-30垫底 | 器乐,物理无人声 ✓ |
| 走渲染机+默认 | render-remote.sh,egress东京 | ✓ |

**教训**：换音频后必验 (a) compose/assets/*.mp3 同步 (b) 音画对齐锚点抽查(切片转写 vs 该刻应说的话)——v2 只测了源wav+回转写(同剧本必过),漏了渲染音频时间戳是否匹配字幕。

---
## (历史) v2 出厂自查

成片：`out/final.mp4`(=v2) · 1280×720 · 30fps · **198.9s** · -14.05 LUFS/TP-1.49 · 渲染机(服务端270s)。
v1 存档 `out/final_v1_audiobook.mp4`；渲染母版 `out/final_v2_render_raw.mp4`。

## v2 相对 v1 的三处返修（用户反馈）
| # | 反馈 | 修法 | 证据 |
|---|---|---|---|
| 音色 | A(audiobook)前后不一致 | 换 **Gentle_Senior**(风格包实证音色,calm/1.0),新时间轴198.9s全链重对齐 | ECAPA verify_files MIN **0.952**(A其实0.940也达标;我首轮4s窗裸余弦0.703是错测,已纠) |
| 视觉 | 拼贴少得可怜/MG一大半 | 像素叙事 6%→**40%**：11条纸拼贴collage承担打脸章节 | collage40%/MG44%/footage15% |
| BGM | 要,且禁人声哼唱+禁鼓点 | fal minimax-music/v2.6 重生成(纯器乐平铺)→loop→-30垫底,data-volume0.25 | -14成片里~20LU低于旁白 |
| 渲染 | 走渲染机+以后默认 | tools/render-remote.sh 服务端渲染 | egress东京13.158.136.168;抽帧与本地snapshot一致 |

## L0 手动仪器（v2）
- 容器：1280×720/30fps/198.9s ✓ ｜ 黑帧 blackdetect **0 段** ✓
- 冻结 freezedetect **39 段全部落在 MG 数据卡停留区间**（逐段分类：collage/footage **0 冻结**——拼贴clip有组装运动、实拍有真运动）✓
- 响度：渲染 -22.45 → loudnorm → **-14.05 LUFS / TP -1.49** ✓
- 回转写 vs 剧本：去数字后 **96.8%** ≥95% ✓
- **ECAPA 声纹**（v1 跳门的补课）：verify_files 整节 6 段 pairwise **MIN 0.952** ≥0.88 **PASS** ✓

## 视觉出厂自查（v2，抽帧25帧全时间轴 + compose snapshot）
- ✅ 拼贴叙事主导打脸章节（闷热人/汗蒸发受阻/脆弱人群/空调内部霉/压缩机启停/霉味扩散/遥控加键/冷气下沉/居家暖场）
- ✅ MG 只承载硬数据（26℃报题/湿度对照/两档温度带/tips榜单/设问）——不再幻灯片感失衡
- ✅ 素材零重复 / 无暗尾黑闪（唯一黑场=金句淡出）/ 纸纹+褪色LUT缝合横跨 collage/MG/footage
- ✅ 字幕 ≤16字无拆词 / 时效词无 / collage 死尾检查全过（11条assemble铺满到末帧）
- ✅ 渲染机 spot-check：final_v2 抽帧与本地 compose snapshot 帧级一致（compose 自带 woff2,无 local() 系统字体依赖）

## ⚠️ 遗留（待用户看片裁决）
1. **s06「温度计」空镜仍偏弱（24.9s，~5s）**：Pexels 命中的是视频 timecode 显示器(LTC/VITC)，非温度计。v2 未动它（用户本轮聚焦音色/视觉/BGM）。可选：换真温度计空镜 or 转 collage，批量修时一起重渲。**非阻塞。**
2. 成本单价待回填（TTS×3、GPT-Image×11、Seedance×11、fal-music×2、渲染机×1）。

## 待用户（M0 评委）
- ⏸ 亲自看片 `out/final.mp4`（v2）
- 认可 → `/video-score` 登记9维 → 合 main（[[worktree-merge-discipline]]，尚未合）
