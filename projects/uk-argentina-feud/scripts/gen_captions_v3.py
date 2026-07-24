#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""字幕 v3：强制对齐 timeline（剧本每字真实戳，1:1）→ 句级字幕零漂移。
用法: gen_captions_v3.py <timeline_fa.json> [out_js]"""
import json, re, sys

ROOT = "/Users/admin/kuleshov/.claude/worktrees/estee-lauder-night-video-7162e0/projects/uk-argentina-feud"
tl_path = sys.argv[1]
out_js = sys.argv[2] if len(sys.argv) > 2 else f"{ROOT}/compose/assets/captions_data.js"
tl = json.load(open(tl_path, encoding="utf-8"))
words = tl["words"]  # 每项 = 剧本一个 norm 字，顺序与剧本严格一致

d = json.load(open(f"{ROOT}/film.json", encoding="utf-8"))
secs = d["audio"]["voiceover"]["sections"]
def norm(s): return re.sub(r"[^一-鿿A-Za-z0-9]", "", s)

# 校验 1:1
total = sum(len(norm(s["text"])) for s in secs)
assert total == len(words), f"字数不匹配 script={total} timeline={len(words)}"

def split_line(text):
    units = [u.strip() for u in re.split(r"(?<=[。！？；])", text) if u.strip()]
    out = []
    for u in units:
        if len(u) <= 16:
            out.append(u)
        else:
            buf = ""
            for s in re.split(r"(?<=[，、：])", u):
                if len(buf) + len(s) <= 16:
                    buf += s
                else:
                    if buf: out.append(buf)
                    buf = s
            if buf: out.append(buf)
    return out

caps, pos = [], 0
for sec in secs:
    for line in split_line(sec["text"]):
        n = len(norm(line))
        if n == 0: continue
        t0 = words[pos]["t"][0]
        t1 = words[pos + n - 1]["t"][1]
        caps.append({"text": line.rstrip("，、：。"), "start": round(t0, 2), "end": round(t1 + 0.12, 2)})
        pos += n
# 相邻句防重叠/防闪缝：后句起点若与前句终点距离 <0.24s，直接对接
for i in range(1, len(caps)):
    if caps[i]["start"] - caps[i-1]["end"] < 0.24:
        caps[i-1]["end"] = caps[i]["start"]

open(out_js, "w", encoding="utf-8").write(
    "window.__captions = " + json.dumps(caps, ensure_ascii=False) + ";\n")
print(f"字幕 v3：{len(caps)} 句（forced-align 1:1，无比例估算）")
for c in caps[:4] + caps[-3:]:
    print(f"  [{c['start']:>7.2f}-{c['end']:>7.2f}] {c['text']}")
