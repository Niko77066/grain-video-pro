# Review · AI 现在会自己黑库了

> ⑨ review。L0 手动仪器（出示证据，"我检查过了"不算数）+ 视觉出厂自查 15 项 + 五维。成片 `out/final.mp4`。

## L0 手动仪器（证据）

| 项 | 结果 | 证据 |
|---|---|---|
| 分辨率/帧率/编码 | 1080×1920 / 30fps / h264+aac | `ffprobe` |
| 时长 | 82.1s（音频 81.936s；no-lock 只记录不设门） | `ffprobe format=duration` |
| 黑帧 | **无** | `blackdetect=d=0.1:pic_th=0.98` 无输出 |
| 冻结（烘焙 clip） | **4 拼贴窗内 0 处 >0.4s 冻结**（全 live） | `freezedetect=n=-60dB:d=0.4` 按窗分类：s02a[5.35–11.31]/s03b[38.07–44.91]/s03c[44.91–52.15]/s04d[67.43–75.11] 无命中 |
| 冻结（版式卡长 hold） | 均落静态卡（s01/doc-hf/doc-isc/s03a/s03d/doc-law/s04e）——typography_led 本征，selfcheck 项4 明确 exempt | 同上 |
| 响度 | **-14.10 LUFS / -0.95 dBTP**（2-pass；raw render -17.72→norm；video 流 copy 保留确定性渲染） | `loudnorm print_format=json` 复测 |
| 回转写 vs 剧本 | **98.96%**（G1，gate02；成片音轨=同一 voiceover.mp3） | faster-whisper + 繁简/数字归一 |

## 承诺复验

- 交付类型 `typography_led + collage_broll`：10 案卷/版式卡 + **4 拼贴 b-roll 真运动** ✓
- 转场词汇 **3 种**（硬切 / 色块横扫 / 白帧）≤ 4 ✓
- 时长：无锁，记录 82.1s（估 77s→TTS 实 81.9s，未变速凑数）✓

## 视觉出厂自查（visual-selfcheck 15 项 · 逐项）

1. 竖屏视觉重心居中：卷宗/纸签内容垂直居中，无上堆下空 ✓
2. 信息层级 ≤2、无 PPT 双角标：案卷用 foldertab + docsrc 极轻脚注（卷宗语言，非左上kicker+左下src 双角标）✓
3. 文件实证：doc-hf/doc-isc/doc-law 卷宗带 docmeta+出处；个保法第51条**同步高亮**（加密 wash+bar）；无"纯版式讲文件" ✓
4. 禁死尾：4 拼贴窗 freezedetect 0 命中（见上）✓
5. 幻灯片化：max 静态卡连跑 4（= 首片 case-file precedent），靠段2/段3 色块横扫章节切+4 拼贴锚定视觉打断；同模板连跑 ≤2 ✓（documented relaxation）
6. 模板味：HF/ISC 网络核武器/隐私反推/密文保险箱/文件果实 均选题专属，换选题不成立 ✓
7. 三面开钩一致：封面「AI 会自己黑库了」= 首帧「现在 AI 自己就能干」= 口播首句 ✓
8. 质感缝合：4 色场（焦橙/深紫/芥末黄/墨绿）+ 版式卡 共享纸颗粒+奶油白keyline+印刷红点色，缝成一家 ✓
9. 文字不拆词：大字均 nowrap/显式 <br>（现在 AI 自己就能干 / 网络核武器 / 又快又便宜 / 它看不懂的保护），无词被拆行 ✓
10. 素材重复：N/A（无实拍池；4 拼贴各异）✓
11. 时代/地点错位：N/A ✓
12. 暗尾黑闪：blackdetect 无黑帧；拼贴窗无死尾 ✓
13. 音画同步：分镜按 seed-audio 自带逐字戳绑真实音频区间（G1 98.96% 佐证）；卡片入场落句读；拼贴 payoff 尾对齐落旁白点 ✓
14. **时效词复核**：旁白相对时间词仅"这两天"——指 ISC2026 + HF 事件（均 7/20 新闻周期），48h 内发布（≤7/22）仍准确；无"昨天/today"硬伤。视觉时效戳 s01「07/20」、卡片「2026-07-20/07」准确 ✓
15. 烘焙镜头拍点：4 拼贴 payoff（电路手抽档案/人形成型/摘果/锁盒）尾对齐落对应旁白 ✓（gate05）

**五维**：版式重心 4 / 层级克制 4 / 实证充分 5 / 动静得当(无死尾) 5 / 缝合统一 4 —— 全 ≥4，出厂。

## 渲染

- `hyperframes render --docker`，CLI + 镜像 **均 0.7.64**（版本匹配确定性渲染；首片曾因 0.7.64 镜像构建超时 fallback 到 0.7.60，本片镜像已就位，**优于首片口径**）。render 6m59s。
- 成片抽帧目检（3/9/27/42/49/72/79.5s）：**CJK 字体渲染正常**（docker）、**4 拼贴视频均 baked in**（非黑场）、品牌角标/加密高亮/金句/标签安全区避让 均正常。
- 保留 `out/final_render_raw.mp4`（loudnorm 前原始渲染，帧级复现用）。

## ⏸ 用户看片（M0 评委门）

成片 `out/final.mp4`（1080×1920 / 30fps / 82.1s / -14.10 LUFS / 无黑帧）。EP 已过 L0 + 视觉 15 项 + 合规；请用户亲自看片校准。

---

## 修订 v2（2026-07-20 用户看片反馈后）

三处改动（详见 ledger dec02/dec03/dec04 + gate09/10/11）：

1. **s03b 重做**（dec02/gate09）：v1「碎片聚成具体男性人脸」概念漂到重识别、标签「一个你」与陌生脸不搭 → v2「AI 回答气泡 → 红色反推箭头 → 拽开个人档案（记录+剪影 chip）」，标签改「一句回答，反推出你」，贴合赵春江「从 AI 输出反推训练数据隐私」。单镜手术，新静帧+新 Seedance，其余镜未动。v1 归档 `anchors/_v1_archive`、`shots/_v1_archive`。
2. **woff2 字体 + 渲染机切默认**（dec03/gate10）：compose 弃 `local("PingFang/Songti")` 系统字体，换自带 `SansSC/SerifSC` woff2（`font-weight:900→700` 避 faux-bold 本地/机器差异）；上渲染机出片。**双跑验收**：全片 SSIM 0.9803 / PSNR 37.76（残差集中在 4 拼贴视频 h264 重编码；卡片段 0.9857 > 拼贴段 0.9700），关键版式帧（个保法卡）local vs server **换行/字形/安全区逐像素级一致**（单帧残差=chromium 光栅 AA，非内容）——首片系统字体的长标题换行漂移已消除。达切默认门：**渲染机切默认、本地 docker 降兜底**。
3. **BGM**（dec04/gate11）：fal `minimax-music/v2.6`（用户指定接口）生器乐床（慢/小调/低 drone+钟摆 tick+微 glitch，无人声），post-mix 置旁白下 ~20LU。发布包设计取消（`out/publish` 删，CLAUDE.md + rednote SKILL 同步）。

**final.mp4（v2）**：渲染机 woff2 片（视频流 copy）+ 旁白 + BGM 混音；1080×1920/30fps/82.0s/**-14.12 LUFS / -0.99 dBTP**；blackdetect 无黑帧；freezedetect 4 拼贴窗 0 死尾。`out/final_server.mp4` 为无 BGM 母版。
