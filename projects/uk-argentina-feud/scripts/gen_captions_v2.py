#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""字幕 v2：用 timeline.words 逐词真实戳精确对齐(替代字数比例估算)。
剧本句→whisper全字位置(全局累积映射)→句首尾词真实戳。同时导出 shot cue 供画面对齐。"""
import json, re

ROOT = "/Users/admin/kuleshov/.claude/worktrees/estee-lauder-night-video-7162e0/projects/uk-argentina-feud"
tl = json.load(open(f"{ROOT}/audio/timeline.json", encoding="utf-8"))
words = tl["words"]
def isw(ch): return bool(re.match(r'[一-鿿A-Za-z0-9]', ch))
# whisper 逐字 + 每字真实戳
wch, wt0, wt1 = [], [], []
for w in words:
    for ch in w["w"]:
        if isw(ch):
            wch.append(ch); wt0.append(w["t"][0]); wt1.append(w["t"][1])
Wn = len(wch)

d = json.load(open(f"{ROOT}/film.json", encoding="utf-8"))
secs = d["audio"]["voiceover"]["sections"]
def norm(s): return re.sub(r'[^一-鿿A-Za-z0-9]', '', s)
reftotal = sum(len(norm(s["text"])) for s in secs)

def split_line(text):
    units = [u.strip() for u in re.split(r'(?<=[。！？；])', text) if u.strip()]
    out = []
    for u in units:
        if len(u) <= 16: out.append(u)
        else:
            buf = ""
            for s in re.split(r'(?<=[，、：])', u):
                if len(buf)+len(s) <= 16: buf += s
                else:
                    if buf: out.append(buf)
                    buf = s
            if buf: out.append(buf)
    return out

caps, refpos = [], 0
for sec in secs:
    for line in split_line(sec["text"]):
        nl = norm(line)
        if not nl: continue
        wi_s = min(int(round(Wn * refpos / reftotal)), Wn-1)
        wi_e = min(int(round(Wn * (refpos+len(nl)) / reftotal)) - 1, Wn-1)
        wi_e = max(wi_e, wi_s)
        caps.append({"text": line.rstrip("，、：。"), "start": round(wt0[wi_s], 2), "end": round(wt1[wi_e]-0.03, 2)})
        refpos += len(nl)

open(f"{ROOT}/compose/assets/captions_data.js", "w", encoding="utf-8").write(
    "window.__captions = " + json.dumps(caps, ensure_ascii=False) + ";\n")
print(f"字幕 v2：{len(caps)} 句，逐词真实戳对齐(whisper 全字 {Wn})")
for c in caps[:5]: print(f"  [{c['start']:>6.2f}-{c['end']:>6.2f}] {c['text']}")
