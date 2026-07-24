#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""字幕：剧本原文切 8–16 字/屏，时间按 timeline 分节区间字数比例分配。输出 captions_data.js。"""
import json, re

ROOT = "/Users/admin/kuleshov/.claude/worktrees/estee-lauder-night-video-7162e0/projects/uk-argentina-feud"
d = json.load(open(f"{ROOT}/film.json", encoding="utf-8"))
tl = json.load(open(f"{ROOT}/audio/timeline.json", encoding="utf-8"))
secmap = {s["id"]: s["t"] for s in tl["sections"]}

def split_line(text):
    # 先按强句读切
    units = re.split(r'(?<=[。！？；])', text)
    units = [u for u in units if u.strip()]
    out = []
    for u in units:
        u = u.strip()
        if len(u) <= 16:
            out.append(u)
        else:
            # 过长：按逗号/顿号再切，贪心合并到 ≤16
            sub = re.split(r'(?<=[，、：])', u)
            buf = ""
            for s in sub:
                if len(buf) + len(s) <= 16:
                    buf += s
                else:
                    if buf: out.append(buf)
                    buf = s
            if buf: out.append(buf)
    # 合并过短(<5字)到前一句
    merged = []
    for c in out:
        if merged and len(c.rstrip("。！？；，、：")) < 5 and len(merged[-1]) + len(c) <= 18:
            merged[-1] += c
        else:
            merged.append(c)
    return merged

caps = []
for sec in d["audio"]["voiceover"]["sections"]:
    sid, text = sec["id"], sec["text"]
    t0, t1 = secmap[sid]
    lines = split_line(text)
    total = sum(len(l) for l in lines)
    cur = t0
    for l in lines:
        span = (t1 - t0) * len(l) / total
        disp = l.rstrip("，、")  # 屏上不显示行尾逗号
        caps.append({"text": disp, "start": round(cur, 2), "end": round(cur + span - 0.06, 2)})
        cur += span

js = "window.__captions = " + json.dumps(caps, ensure_ascii=False, indent=0) + ";\n"
open(f"{ROOT}/compose/assets/captions_data.js", "w", encoding="utf-8").write(js)
print(f"字幕 {len(caps)} 句 → compose/assets/captions_data.js")
for c in caps[:6]:
    print(f"  [{c['start']:>6.2f}-{c['end']:>6.2f}] {c['text']}")
print("  ...")
mx = max(len(c["text"]) for c in caps)
print(f"最长句 {mx} 字 | 平均 {round(sum(len(c['text']) for c in caps)/len(caps),1)} 字")
