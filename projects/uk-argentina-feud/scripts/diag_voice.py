#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""验证整条音轨 audiobook_female_1 是否音色漂移：分6段声纹 vs 段1。"""
import subprocess, os
try:
    from speechbrain.inference.speaker import SpeakerRecognition
except Exception:
    from speechbrain.pretrained import SpeakerRecognition
m = SpeakerRecognition.from_hparams(source="speechbrain/spkrec-ecapa-voxceleb", savedir="/tmp/spkrec-ecapa")
A = "/Users/admin/kuleshov/.claude/worktrees/estee-lauder-night-video-7162e0/projects/uk-argentina-feud/audio"
segs = [(2, 18), (40, 56), (85, 101), (125, 141), (165, 181), (215, 231)]
for i, (s, e) in enumerate(segs):
    subprocess.run(["ffmpeg", "-y", "-ss", str(s), "-to", str(e), "-i", f"{A}/voiceover.mp3",
                    "-ar", "16000", "-ac", "1", f"/tmp/seg{i}.wav"], capture_output=True, check=True)
def sim(a, b):
    sc, _ = m.verify_files(f"/tmp/seg{a}.wav", f"/tmp/seg{b}.wav"); return round(float(sc), 3)
vals = [sim(0, i) for i in range(1, 6)]
print("整条 audiobook_female_1 分段声纹 vs 段1(理论单次应≈1.0):")
for i, v in zip(range(1, 6), vals):
    print(f"  段1 vs 段{i+1}: {v}")
print(f"  min={min(vals)} mean={round(sum(vals)/len(vals),3)}")
print("判定:", "音色稳 ✓(>0.9)" if min(vals) > 0.9 else "整条内部仍漂移 ❌ → 需克隆音色或换voice")
