---
name: pixel-broll
description: 用 GPT-Image-2 + Seedance 2.0 生成**像素风**动画镜头（角色重演 / 机制图解 / 数据实物化），并用主调色板 + 栅格归一把「AI 的软像素」钉成真像素。当用户说"像素风""像素动画""pixel art""做个像素镜头""seedance 出像素""浣熊那种像素镜"，或 storyboard 有镜头路由到 pixel-broll 时使用。强制四闸门：主调色板 → 视觉/动作方案 → 静帧 → 视频，每闸停下等确认。**严禁做旧**：paper / halftone / aged / newsprint / grain / sepia 一律不许进提示词——做旧只能是 compose 层的 LUT，烤进画面就再也剥不掉。
---

# Pixel B-roll → `broll-studio` 的 `pixel` profile

**本文件是指针壳，内容已经不在这里。** 像素风是八套生成型材质语言之一，它们共用一套引擎：

👉 **去读 `.claude/skills/broll-studio/SKILL.md`，profile = `pixel`。**

```bash
python3 tools/broll-profile.py plan pixel --variant A|B   # 完整工序清单（含归一层与主调色板闸门）
python3 tools/broll-profile.py show pixel                 # 禁用词表、失败标准、状态、IR 写回
python3 tools/broll-profile.py status                     # 冒烟状态（唯一出处）
```

为什么只留指针：三闸门、画幅几何、引擎绑定、QA 判据、IR 写回**跨材质恒定**，抄成八份就有八个会各自漂移的副本——「做旧报纸味的假像素」正是这么长出来的。像素专属的东西（主调色板闸门 Gate 0、栅格归一、栅格+锁色码判、禁用词表、两种运动原型）全部声明在 `profiles/pixel.json` 的 `pipeline_extras` / `banned_vocab` / `variants` 里，引擎照单执行。

- 归一与验收脚本：`tools/{make-palette,pixelize,verify}.py`（原 `.claude/skills/pixel-broll/scripts/`，2026-07-28 移入 `tools/`——它们已经是引擎的一部分）
- 考卷：合并进 `.claude/skills/broll-studio/evals.json`（19 条，`profile: "pixel"` 标出守像素知识的那 6 条）
