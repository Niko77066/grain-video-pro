# 隔离评审任务 · node=hero_frames

> 你是 Kuleshov 独立评委（G2），与创作者物理隔离：只看下列证据，不接受、不索取任何创作过程解释。

## 评分/评审标准
你是独立评委，评 hero-frame 品味门（分镜铺开前）。证据：本片 3 张 hero frame
+ 该风格包 Golden 基准 contact sheet。判断每张 hero frame 是否达到 Golden 的视觉下限
（风格贴合 / 版式克制——克制≠稀疏，元素孤立漂浮、留白无信息承载 = 扣分 / 质感缝合），
并逐条核风格包反模式。未达下限 = 打回，禁止铺开全片生产。逐帧引用 frame 序号。只输出 JSON：
{"per_frame": [{"frame": "..", "pass": bool, "reason": "..引用.."}],
 "antipatterns": [".."], "template_test": "..", "verdict": "pass|fail",
 "notes": {"overall": "..引用.."}, "must_fix": ["..引用.."]}

## 证据文件（附给你评审，逐个看）
- hero frame: /Users/admin/deeplang/grain-video-pro/.claude/worktrees/finance-video-production-bd1929/projects/china-h1-2026-econ/evidence/judge-pack-hero/frames/frame1-hook.png
- hero frame: /Users/admin/deeplang/grain-video-pro/.claude/worktrees/finance-video-production-bd1929/projects/china-h1-2026-econ/evidence/judge-pack-hero/frames/frame2-core.png
- hero frame: /Users/admin/deeplang/grain-video-pro/.claude/worktrees/finance-video-production-bd1929/projects/china-h1-2026-econ/evidence/judge-pack-hero/frames/frame3-conclusion.png
- Golden 基准 contact sheet: /Users/admin/deeplang/grain-video-pro/.claude/worktrees/finance-video-production-bd1929/projects/china-h1-2026-econ/evidence/judge-pack-hero/golden-contact-sheet.jpg

## 镜头事实清单（id/区间/意图/景别/来源，零创作理由）
[{"id": "hero1", "t": [0.0, 6.91], "intent": "钩子：同一张表两组反向数字", "framing": "主播中景 + 右侧双数字组 + 左下标题条", "provider": "avatar+hyperframes"}, {"id": "hero2", "t": [37.24, 48.52], "intent": "外贸扛住增长", "framing": "实拍港口全景 + 右侧数据卡", "provider": "footage+hyperframes"}, {"id": "hero3", "t": [74.84, 81.96], "intent": "收束于未决问题", "framing": "全屏字卡 + 右侧三指标对比", "provider": "hyperframes"}]

## 合同带宽内调整（评审时须知悉）
{}


## 交回
只输出上面 schema 规定的一个 JSON 对象。扣分/判断必须引用镜头 ID 或时间码，无引用的判断无效。
