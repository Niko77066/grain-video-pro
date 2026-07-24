#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""音色定稿：用户选 候选B（气泡音个性），要求放慢。更新 voice_profile，重置 sec01。"""
import json

ROOT = "/Users/admin/kuleshov/.claude/worktrees/estee-lauder-night-video-7162e0/projects/uk-argentina-feud"
d = json.load(open(f"{ROOT}/film.json", encoding="utf-8"))
vo = d["audio"]["voiceover"]

vo["voice_profile"] = "一位中文年轻女性讲述者，二十多岁，声音清亮里带一点气泡音的轻微沙质感，慵懒而自然、有记忆点，冷静克制、平实零表演腔，语速平稳从容"
vo["voice_profile_note"] = "用户 2026-07-16 音色 gate 定稿：4 候选中选 B『气泡音个性』（最有辨识度）；语速较候选版放慢（描述『明快偏快』→『平稳从容』+ speech_rate 下调）。守冷静克制零表演腔。跨节复用，首片确认后回填 pixel-chronicle playbook。"
vo["chosen_candidate"] = "B-气泡音个性"

for s in vo["sections"]:
    if s["id"] == "sec01":
        s["status"] = "planned"
        s["gen"] = None

d["ledger"]["decisions"].append({
    "date": "2026-07-16", "stage": "audio", "by": "用户",
    "decision": "音色定稿：候选 B（年轻女声 / 气泡音个性），语速较候选版放慢",
    "options_considered": ["A 磁性电台", "C 温柔讲述", "D 知性清冷"],
    "reason": "用户听 4 候选后选 B『最对味/有辨识度』，要求语速再慢一些"
})
json.dump(d, open(f"{ROOT}/film.json", "w", encoding="utf-8"), ensure_ascii=False, indent=2)
print("chosen: B-气泡音个性 | voice_profile 已更新为『平稳从容』 | sec01 reset")
