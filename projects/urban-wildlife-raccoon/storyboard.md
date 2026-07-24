# Storyboard · 城市浣熊（EP01）

- 24 镜 / 6 Seedance 组。时长为 **provisional 估算**（字数派生），待 ④ 真实 TTS timeline 覆盖后逐镜重对齐。
- G1 全门通过（`kuleshov-ir validate` → 0 error / 0 warning，含 `style_contract_plan`）。
- 份额：**HyperFrames 49%**（合同带宽 25–60%）· **Seedance 像素叙事 27%**（≥15%）· **footage 实拍 24%**。声明型图形最长连续 15s（≤26s）。
- 真运动占比：seedance 27% + footage 24% = **51%**（承诺可达）。
- 交替节奏（playbook §7 硬规则）：MG↔实拍/像素严格交替，无连续 3 镜同类。

## 逐镜路由表

| 镜 | 时间带 | 来源 | intent | 声部/trait |
|---|---|---|---|---|
| s01 | 0–6 | HyperFrames | 3100万金色大字+防浣熊桶旋转锁 | 数据骨架 |
| s02 | 6–12 | HyperFrames | 计时器00:30+锁弹开 | 数据骨架 |
| s03 | 12–18 | Seedance | 浣熊拧开旋转锁（钩子核心） | 像素叙事 |
| s04 | 18–24 | Seedance | 浣熊推倒桶脱锁（'完败'） | 像素叙事 |
| s05 | 24–31 | footage | 多伦多夜景天际线空镜 | 证据/纪实 |
| s06 | 31–37 | HyperFrames | 品牌闸门+系列主视觉卡 | 报题 |
| s07 | 37–43 | Seedance | 浣熊街灯下探头（主角登场） | 像素叙事 |
| s08 | 43–49 | HyperFrames | 章节卡『一·吃』 | 章节 |
| s09 | 49–57 | Seedance | 溪边'洗食'（野外基线） | 像素叙事 |
| s10 | 57–65 | HyperFrames | 城市餐桌vs树林 食物密度对比 | 数据实物化 |
| s11 | 65–75 | footage | 真浣熊翻猫粮盆（+血糖角标） | 证据/纪实 |
| s12 | 75–81 | HyperFrames | 章节卡『二·走』 | 章节 |
| s13 | 81–90 | HyperFrames | 活动范围 乡下圈vs城市点（红箭头） | 数据实物化 |
| s14 | 90–98 | Seedance | 密集街区就近觅食（小家域） | 像素叙事 |
| s15 | 98–105 | HyperFrames | 密度铺格 5–10→100→300+ | 数据实物化 |
| s16 | 105–111 | footage | 夜间浣熊过街/下水道（夜班） | 证据/纪实 |
| s17 | 111–115 | Seedance | 爬排水管上屋顶（立体路网） | 像素叙事 |
| s18 | 115–121 | HyperFrames | 章节卡『三·生』 | 章节 |
| s19 | 121–129 | HyperFrames | 空心树→烟囱剖面图解+日历 | 数据实物化 |
| s20 | 129–137 | Seedance | 母浣熊烟囱挡烟板育幼 | 像素叙事 |
| s21 | 137–145 | footage | 屋顶烟囱空镜（落点） | 证据/纪实 |
| s22 | 145–152 | HyperFrames | 虚实呼应叠化 桶⇄果树/烟囱⇄树洞 | 签名动作 |
| s23 | 152–161 | footage | 真浣熊翻桶收尾（呼应s03开场） | 证据/纪实 |
| s24 | 161–170 | HyperFrames | 末卡 logo+手写体金句（零CTA） | 结尾 |

## Seedance 组 + 接缝契约（6 组，均 ≤15s）

- **g1_hook** [s03,s04] 12s · 内部 B 硬切（拧锁/推倒两拍并置）· 组后硬切实拍夜景
- **g2_peek** [s07] 6s · 主角登场，前后接 MG
- **g3_wash** [s09] 8s · 野外食性基线，后接 MG 餐桌对比
- **g4_near** [s14] 8s · 小家域，前后接 MG 地图/密度
- **g5_roof** [s17] 4s · 立体路网收章二
- **g6_kits** [s20] 8s · 育幼，后接实拍屋顶

## 可复现生成 prompt（"prompt 模式"资产 · M0 核心交付物）

> 完整 prompt 已存入 `film.json` 各镜 `source.params.prompt_plan`。共享风格底：`Retro 16-bit PIXEL-ART paper-collage, aged-yellow #C9A876 paper grain, pixel dithering, cream keylines, chunky pixels, soft shadows. Locked-off 16:9, no camera movement, no scene cuts, no morphing, no text/numbers/logos, no sound.` 角色底：`one chunky pixel-art raccoon — grey body, black eye-mask, black-and-grey ringed bushy tail, dexterous pale front paws`。

- **共享角色锚 `anc_raccoon_char`**（GPT-Image-2）：像素浣熊角色表，所有 seedance 镜挂此锚保一致；锚内禁文字数字。
- 6 个 seedance 镜各有首帧锚（`anc_s0x_first`，status=planned），首帧出图 → Seedance 慢组装 10s（尾对齐）→ QC。

## 出厂自查八项（结果记 ledger.gates；coded 门已由 validate 复核）

1. 区间无缝隙/重叠、首尾对齐 170s ✓（timeline_coverage 门 pass）
2. 每 6–8s 一次视觉变化 ✓（visual_change 门 pass）
3. 连续同版式/景别 ≤2 ✓（framing_repeat 门 pass）
4. 幻灯片风险：静态类连续 ≤2 镜 ✓（slides_risk 门 pass）
5. 声部匹配 intent ✓
6. 运动承诺可达：真运动 51% ✓
7. Seedance 组算术：每镜属一组、组 ≤15s ✓（groups_arithmetic 门 pass）
8. 每镜一主动作+运镜词 ✓（motion_word 门 pass）
9. 风格合同预检 ✓（style_contract_plan：份额/图形连续全在带宽，0 error）

## ⛔ 凭据墙（下一步需 .env）

- **③b hero-frames 品味门**（未执行）：需出 3 张 hero frame（s03 钩子/s22 虚实呼应/s24 金句）与 Golden 并排送 G2 评委——**必须在任何 seedance/anchor 花钱前跑**，未达 Golden 下限禁铺开生成。需 GPT-Image + Kimi 凭据。
- **④ TTS + 强制对齐**：需 `MINIMAX_*`；真实 timeline 覆盖 provisional 估时，画面 cue 重派。
- **⑥⑦ anchors + Seedance motion**：需 `ARK_VIDEO_*`（+ OSS 上传 @ref）。
- **⑧ compose + 远程渲染**：需 `RENDER_URL` + `FFMPEG_RENDER_HTTP_TOKEN`（自带 woff2）。
- **⑨ G2 评委门**：需 `KIMI_API_KEY`。
- **footage**：需 `PEXELS_API_KEY` / `PIXABAY_API_KEY` / archive.org 公域。
