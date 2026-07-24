#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""整条音轨(单次MiniMax)→ 48k + mlx-whisper 逐词对齐 → 新 timeline.json(音画同步基准)。"""
import json, subprocess, re

ROOT = "/Users/admin/kuleshov/.claude/worktrees/estee-lauder-night-video-7162e0/projects/uk-argentina-feud"
A = f"{ROOT}/audio"

# 1. 转 48k stereo，覆盖 voiceover.mp3 为新整条
subprocess.run(["ffmpeg", "-y", "-i", f"{A}/voiceover_full.mp3", "-ar", "48000", "-ac", "2",
                "-c:a", "libmp3lame", "-b:a", "128k", f"{A}/voiceover.mp3"], check=True, capture_output=True)
dur = float(subprocess.run(["ffprobe", "-v", "error", "-show_entries", "format=duration", "-of", "csv=p=0",
                            f"{A}/voiceover.mp3"], capture_output=True, text=True).stdout.strip())

# 2. mlx-whisper 逐词
import mlx_whisper
r = mlx_whisper.transcribe(f"{A}/voiceover.mp3", path_or_hf_repo="mlx-community/whisper-large-v3-turbo",
                           language="zh", word_timestamps=True)
words = []
for seg in r.get("segments", []):
    for w in seg.get("words", []):
        words.append({"w": w["word"].strip(), "t": [round(w["start"], 3), round(w["end"], 3)]})

# 3. 节区间：剧本6节累积字数比例 → words 边界（中文 whisper 近似逐字）
d = json.load(open(f"{ROOT}/film.json", encoding="utf-8"))
secs = d["audio"]["voiceover"]["sections"]
ref_lens = [len(re.sub(r'[^一-鿿A-Za-z0-9]', '', s["text"])) for s in secs]
total = sum(ref_lens)
N = len(words)
sections, cum, wi = [], 0, 0
for i, s in enumerate(secs):
    cum += ref_lens[i]
    end_wi = min(round(N * cum / total) - 1, N - 1)
    end_wi = max(end_wi, wi)
    st = words[wi]["t"][0] if wi < N else dur
    et = words[end_wi]["t"][1] if end_wi < N else dur
    sections.append({"id": s["id"], "t": [round(st, 2), round(et, 2)]})
    wi = end_wi + 1

json.dump({"duration_s": round(dur, 3), "engine": "minimax单次整条", "words": words, "sections": sections},
          open(f"{A}/timeline.json", "w", encoding="utf-8"), ensure_ascii=False, indent=1)
print(f"整条 {round(dur,2)}s | 逐词 {N} | 节区间:")
for s in sections:
    print(f"  {s['id']}: {s['t'][0]:>6.2f} – {s['t'][1]:>6.2f}s ({s['t'][1]-s['t'][0]:.1f}s)")
