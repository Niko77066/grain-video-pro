#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""音色 gate 第二轮：用户要 年轻女声 + 更快。更新 voice_profile，重置 sec01 重生成。"""
import json

ROOT = "/Users/admin/kuleshov/.claude/worktrees/estee-lauder-night-video-7162e0/projects/uk-argentina-feud"
d = json.load(open(f"{ROOT}/film.json", encoding="utf-8"))
vo = d["audio"]["voiceover"]

vo["voice_profile"] = "一位中文年轻女性讲述者，二十多岁，声音清亮自然，冷静克制、平实零表演腔，像向一个人平静讲述而不是新闻播报，语速明快偏快"
vo["voice_profile_note"] = "用户 2026-07-16 音色 gate 反馈：更快+更年轻+换女声（原中年男声）。守 pixel-chronicle 冷静克制零表演腔基调不变；跨节复用，首片确认后回填 playbook 资产化。"
vo["target_wpm_cn"] = None  # 换音色+提速，重测

for s in vo["sections"]:
    if s["id"] == "sec01":
        s["status"] = "planned"
        s["gen"] = None

d["ledger"]["decisions"].append({
    "date": "2026-07-16", "stage": "audio", "by": "用户",
    "decision": "音色人设改为『年轻女声（二十多岁）+ 语速更快』，原中年男声废弃",
    "options_considered": ["保留中年男声样本"],
    "reason": "用户听 sec01 首版后反馈；基调仍守 pixel-chronicle 冷静克制零表演腔（不滑向甜美/播音腔）"
})
json.dump(d, open(f"{ROOT}/film.json", "w", encoding="utf-8"), ensure_ascii=False, indent=2)
print("voice_profile →", vo["voice_profile"])
print("sec01 reset to planned for regeneration")
