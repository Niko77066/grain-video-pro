# Review · openai-78m-logs（⑨ L0 手动仪器）

## v3 案卷档案（2026-07-20）— 当前交付版

> `out/final.mp4` — 1080×1920 · 30fps · h264+aac · **65.8s** · ~29MB · Docker 渲染 `hyperframes@0.7.60`（v2 同镜像同口径；0.7.64 镜像构建超时，0.7.60 为 v2 出厂实际版本，非降级）。响度 **-14.02 LUFS / -0.97 dBTP**（2-pass loudnorm linear）；**无黑帧**；check（0.7.64）0 error / 对比度 **20/20 WCAG AA**。

- **起因**：观众反馈 v2 两条「明显」问题（已登记看片记录 2026-07-20）：① 版式卡（纸白平底）与拼贴 b-roll 割裂（底色 + 字体质感）；② s02a 叠层文字压天平主体。
- **选向**：出 7 候选风格卡（`style-explore/card-variants.html`，V1–V7 + V0 现状 + 2 锚点对照），用户拍板 **V3 案卷档案**。
- **重构**：7 张 HyperFrames 卡全部案卷化——**拼贴色场做卡底**（随相邻拼贴章节轮换：焦橙→深紫→青绿→墨绿），其上摆**奶油白卷宗/纸签**（卷宗标签 + 等宽字元数据 + 红章「指控」+ 红条高亮）。s01 案卷封面、doc-nyt「证据 A」报道卷宗（count-up 保留）、s03a/s04d/s04f 纸签、s03d 对比纸页（「已删除」加划除线）、doc-cac 公文卷宗（第16/17条同步高亮保留）。
- **s02a 叠层修复**：改奶油白案卷标签贴纸（贴上去动效）；按锚点静帧实测天平边界（顶珠 y≈380 起、仅占中央），标签落 y120–350 全宽安全区，单行不折行。成片 6.5s 抽帧确认不压天平。
- **修复过程**（check 驱动）：`.folder` 补 z-index:11（色场 bg clip 曾盖住卷宗）；`.article` 补 position:relative（hl-bar 曾漂位）；callout fig 行高解包围盒重叠；headline/金句断行除孤字；红章两次挪位避开日期。
- **L0 仪器**：ffprobe 65.8s≈音频 65.71s ✓；blackdetect 无黑帧段 ✓；loudnorm 2-pass -17.57→-14.02 LUFS ✓；成片 12 帧抽帧确认 4 拼贴播放 + 7 案卷卡 + 标签避让 + 品牌角标正常 ✓；音频未动（沿用 audio 阶段 G1）。
- ⏸ **待用户亲自看片**（M0 评委门）→ 通过后 /video-score 登记 + ⑩ deliver（合 main + commit）+ 发布包更新。

---

## v2 重构（case-file 风格包，2026-07-17）— 已被 v3 迭代（版式卡割裂 + s02a 压主体）

> `out/final.mp4` — 1080×1920 · 30fps · h264+aac · **65.8s** · ~30MB · Docker 渲染（10.5 分钟）。响度 **-14.05 LUFS / -1.10 dBTP**；**无黑帧**；check 0 error / 对比度 16/16 WCAG AA。

- **起因**：v1（daily-brief）被用户判「版式卡全军覆没」（PPT 味 / 上堆下空 / 提文件却摆字），归档为反例 `out/final_v1_daily-brief.mp4`。
- **重构（case-file 三语言）**：① 数字（78M/20M/数十亿）→ **TechCrunch 报道面板**（浏览器 chrome + 真 headline + 数字 callout count-up）；② 法规 → **cac.gov.cn 公文面板**（第十六/十七条真文本 + 加密/不满十四周岁**同步高亮**，条号已核）；③ 钩子/引言/收尾 → **居中极简**，砍掉角标；④ 保留 4 拼贴 b-roll + 手机↔服务器分屏 + 密态计算标题。
- 三处小修：s01/s03a 拆行修正、s02a scrim、对比度达标。

---

## v1（daily-brief，已淘汰）L0 记录（存档反例）

> `out/final_v1_daily-brief.mp4` — 1080×1920 · 30fps · h264 + aac · **65.8s** · Docker 渲染（renderJobId 459af90d）。

## L0 仪器证据（不空口，附命令）

| 项 | 结果 | 命令 |
|---|---|---|
| 时长 | 65.8s ≈ 音频 65.71s ✓ | `ffprobe -show_entries format=duration` |
| 分辨率/帧率/编码 | 1080×1920 / 30fps / h264+aac ✓ | ffprobe streams |
| 黑帧 | **无黑帧段** ✓（时间轴无缝隙/断层） | `blackdetect=d=0.08:pix_th=0.10` |
| 响度 | 归一前 -17.57 LUFS → **2-pass loudnorm → -14.05 LUFS / -1.10 dBTP** ✓ | `loudnorm=I=-14:TP=-1:LRA=11 linear` |
| 回转写 | 音频内容未变（loudnorm 仅调电平），沿用 audio 阶段 G1：faster-whisper 0.9321，生僻词「拟人化/密态计算」同音字反证发音正确 ✓ | asr_g1_check.py |
| composition | check **0 error**；对比度 **15/15 WCAG AA**；15 帧快照 + 成片 7 帧抽帧确认拼贴播放/版式/品牌/文字均正常 ✓ | `hyperframes check` |

## 承诺复验

- 片型：`typography_led + collage_broll`（12 版式卡 + 4 拼贴 b-roll）；版式卡本征静态属 typography_led 承诺内，非「冻结帧补时长」反模式；拼贴 clip 死尾已在生成阶段用 YDIF 治理。
- 时长：**无锁**（音频/内容自然定 = 65.7s）。
- 转场词汇：硬切 / 色块横扫（章节）/ 白帧（收尾前）= 3 种 ≤ 4 ✓。
- 事实：法规官方全名 + cac 角标；第 16/17 条号已拿 cac 全文核实；OpenAI 全程「起诉文件指控/涉嫌」归因。

## 待办 / DEBT

- ⏸ **用户亲自看片**（M0 评委门）→ 通过后 /video-score 登记 9 维分。
- DEBT：track10 元素密（单文件取舍，check warning，不阻塞）；s02a 首次提交超时可能留 1 个孤儿 Seedance 任务（无 list 接口，查不到/停不掉，最坏 +$2.7）；品牌用默认印刷红 #C8451B（业务侧品牌 hex 到位可覆写重渲）。
- 出厂随片：小红书 + 抖音双平台发布包（走 /rednote-mentor）。
