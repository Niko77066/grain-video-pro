---
name: collage-broll
description: 用 GPT-Image-2 + Seedance 2.0 把一句约 5s 口播／观点句／抽象概念做成高级 editorial **半调纸拼贴**（halftone paper-collage）氛围 b-roll——从空色场逐件组装的定格质感。当用户说"拼贴 b-roll""纸拼贴""半调拼贴""拼贴风格配画面""用这段文稿做拼贴动画"，或 storyboard 有镜头路由到 collage-broll 时使用。强制三闸门：视觉隐喻 → 静帧 → 视频，每闸停下等确认，只有确认过的条目进下一闸。**不许串像素词**：pixel / chunky pixels / dithering / limited palette 属于 pixel-broll，混进来就得到杂交产物。
---

# Collage B-roll → `broll-studio` 的 `collage` profile

**本文件是指针壳，内容已经不在这里。** 半调纸拼贴是八套生成型材质语言之一，它们共用一套引擎：

👉 **去读 `.claude/skills/broll-studio/SKILL.md`，profile = `collage`。**

```bash
python3 tools/broll-profile.py plan collage [--aspect 16:9]  # 工序清单（本 profile 没有额外工序）
python3 tools/broll-profile.py show collage                  # 色彩语义表、失败标准、状态、IR 写回
python3 tools/broll-profile.py render collage --gate 2 --var ...   # 提示词唯一出处
```

为什么只留指针：三闸门、画幅几何、引擎绑定、QA 判据、IR 写回**跨材质恒定**，抄成八份就有八个会各自漂移的副本。拼贴专属的东西——四段实测提示词（9:16 与 16:9 各两段）、**色彩语义表（全仓唯一一份就在这个 profile 里）**、缝合纪律、横屏抗摊散约束与偏前重实测——全部在 `profiles/collage.json`。

- 旧的 `visual-spec.json` 中间文件**已退役**：2026-07-28 收敛进变量层（`broll-profile.py vars` 看逐字段落点），因为没有任何程序读它。
- 批次总览三张图升进引擎：`tools/clip-batch-sheets.py`（八套通用）。
- 考卷：合并进 `.claude/skills/broll-studio/evals.json`（19 条，`profile: "collage"` 标出守拼贴知识的那 6 条）。
