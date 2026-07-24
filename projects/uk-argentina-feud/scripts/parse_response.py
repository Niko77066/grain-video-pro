#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""解析 seed-audio 响应：base64→mp3、ffprobe 核实、subtitle→逐字时间戳。
用法: parse_response.py <section_id>"""
import json, sys, base64, subprocess

ROOT = "/Users/admin/kuleshov/.claude/worktrees/estee-lauder-night-video-7162e0/projects/uk-argentina-feud"
sid = sys.argv[1]
r = json.load(open(f"{ROOT}/audio/response_{sid}.json"))

mp3 = f"{ROOT}/audio/{sid}.mp3"
open(mp3, "wb").write(base64.b64decode(r["audio"]))

ff = subprocess.run(
    ["ffprobe", "-v", "error", "-show_entries", "format=duration,bit_rate",
     "-show_entries", "stream=codec_name,sample_rate,channels",
     "-of", "default=noprint_wrappers=1", mp3],
    capture_output=True, text=True).stdout.strip()

sub = r.get("subtitle", {}) or {}
sents = sub.get("sentences", [])
words, full = [], ""
for s in sents:
    full += s.get("text", "")
    for w in s.get("words", []):
        wt = w.get("text", "")
        st, et = w.get("start_time", 0) / 1000.0, w.get("end_time", 0) / 1000.0
        words.append({"w": wt, "t": [round(st, 3), round(et, 3)]})

dur = r.get("duration")
nchar = len("".join(w["w"] for w in words))
json.dump({"id": sid, "duration_s": dur, "text": full, "words": words},
          open(f"{ROOT}/audio/timeline_{sid}.json", "w", encoding="utf-8"),
          ensure_ascii=False, indent=1)

# 输入文本比对（sanity，非 G1；G1 用 WhisperX 独立转写）
d = json.load(open(f"{ROOT}/film.json", encoding="utf-8"))
src = next(s for s in d["audio"]["voiceover"]["sections"] if s["id"] == sid)["text"]
match = "OK" if full.replace("“","").replace("”","") == src.replace("“","").replace("”","") else "DIFF"

print(f"[{sid}] {mp3}")
print(f"  {ff.replace(chr(10),' | ')}")
print(f"  duration={dur}s  chars≈{nchar}  rate≈{round(nchar/dur*60,1)}字/分  subtitle_vs_src={match}")
print(f"  timeline_{sid}.json: {len(words)} words")
if match == "DIFF":
    print("  ⚠ subtitle文本≠输入（可能吞字/多字），G1 需重点看")
