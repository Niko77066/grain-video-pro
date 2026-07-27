#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""字幕生成：从 forced-alignment 逐字轴派生 captions_data.js。

纪律：
- 戳 1:1 取自 audio/timeline_fa.json 的真实字戳，禁按字数比例估算（forced-alignment.md）；
- **字幕文本不带标点**（2026-07-27 用户拍板：专业视频的字幕从不加标点）。断句处留一个
  全角空格做呼吸，句末不留任何符号；
- 每条 ≤ LIM 字（不含标点计），不跨句合并；相邻 <0.24s 直接对接防闪缝；
- 切分仍**用**标点（它是断句依据），只是不渲染出来。

用法: gen_captions.py <project_dir>
"""
import json, re, sys
from pathlib import Path

P = Path(sys.argv[1] if len(sys.argv) > 1 else "projects/china-h1-2026-econ")
LIM = 16
SENT_END = "。？！"
PAUSE = "，、；："
ALNUM = re.compile(r"[一-鿿A-Za-z0-9]")

tl = json.loads((P / "audio/timeline_fa.json").read_text(encoding="utf-8"))
lines = [l.strip() for l in (P / "audio/narration.txt").read_text(encoding="utf-8").splitlines() if l.strip()]
W = tl["words"]

# 1) 按标点切成片段，记下每片的首/末字在逐字轴上的索引
idx = 0
frags = []          # [display_text, first_char_idx, last_char_idx]
buf, disp = [], ""
for line in lines:
    for ch in line:
        if ALNUM.match(ch):
            buf.append(idx); idx += 1
        disp += ch
        if ch in (SENT_END + PAUSE) and buf:
            frags.append([disp.strip(), buf[0], buf[-1]]); buf, disp = [], ""
    if buf:
        frags.append([disp.strip(), buf[0], buf[-1]]); buf = []
    disp = ""
assert idx == len(W), (idx, len(W))

# 2) 合并短片段到 LIM 字以内——但不跨句末标点合并
n = lambda t: len(re.sub(r"[，。、；：？！]", "", t))
merged = []
for f in frags:
    prev = merged[-1] if merged else None
    if prev and prev[0][-1] not in SENT_END and n(prev[0]) + n(f[0]) <= LIM:
        prev[0] += f[0]; prev[2] = f[2]
    else:
        merged.append(f)

# 3) 渲染文本：句末标点删掉，句中停顿标点换成全角空格
def strip_punct(t: str) -> str:
    t = re.sub(f"[{SENT_END}]", "", t)
    t = re.sub(f"[{PAUSE}]", "　", t)
    return t.strip("　 ").strip()

caps = [{"text": strip_punct(t),
         "start": round(W[a]["t"][0], 3),
         "end": round(W[b]["t"][1] + 0.12, 3)} for t, a, b in merged]
for a, b in zip(caps, caps[1:]):
    if b["start"] - a["end"] < 0.24:
        a["end"] = b["start"]

out = P / "compose/assets/captions_data.js"
out.write_text("window.__captions = " + json.dumps(caps, ensure_ascii=False) + ";\n", encoding="utf-8")

bad = [c for c in caps if re.search(r"[，。、；：？！]", c["text"])]
assert not bad, f"字幕仍含标点: {bad}"
print(f"写出 {out}：{len(caps)} 条，最长 {max(len(c['text']) for c in caps)} 字，标点残留 0")
for c in caps[:3] + caps[-2:]:
    print(f'  {c["start"]:6.2f}-{c["end"]:6.2f}  {c["text"]}')
