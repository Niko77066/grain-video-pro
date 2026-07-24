#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""G1 回转写：独立转写 voiceover.mp3，与剧本比对字级相似度（不用 TTS 自带字幕自证）。"""
import json, re, difflib

ROOT = "/Users/admin/kuleshov/.claude/worktrees/estee-lauder-night-video-7162e0/projects/uk-argentina-feud"
def norm(s):
    return re.sub(r"[^一-鿿A-Za-z0-9]", "", s)

d = json.load(open(f"{ROOT}/film.json", encoding="utf-8"))
ref = "".join(s["text"] for s in d["audio"]["voiceover"]["sections"])

hyp = None
try:
    import mlx_whisper
    r = mlx_whisper.transcribe(f"{ROOT}/audio/voiceover.mp3",
                               path_or_hf_repo="mlx-community/whisper-large-v3-turbo", language="zh")
    hyp = r["text"]; engine = "mlx-whisper large-v3-turbo"
except Exception as e:
    print("mlx failed, fallback faster-whisper:", str(e)[:100])
    from faster_whisper import WhisperModel
    m = WhisperModel("medium", device="cpu", compute_type="int8")
    segs, _ = m.transcribe(f"{ROOT}/audio/voiceover.mp3", language="zh")
    hyp = "".join(s.text for s in segs); engine = "faster-whisper medium"

open(f"{ROOT}/audio/transcript.txt", "w", encoding="utf-8").write(hyp)
R, H = norm(ref), norm(hyp)
sm = difflib.SequenceMatcher(None, R, H)
print(f"engine: {engine}")
print(f"REF {len(R)}字 | HYP {len(H)}字 | 字级相似度 {sm.ratio()*100:.2f}%")
print("差异块（注：whisper 常把『一八〇六』转成『1806』，属转写差异非吞字，需人工研判）：")
n = 0
for op, i1, i2, j1, j2 in sm.get_opcodes():
    if op != "equal" and n < 25:
        print(f"  [{op}] 剧本『{R[i1:i2]}』↔ 转写『{H[j1:j2]}』"); n += 1
