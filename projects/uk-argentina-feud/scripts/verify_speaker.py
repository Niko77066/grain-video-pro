#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""坐实 speaker 字段是否真锁定音色：spk_a(指定预置ID) vs sec02原(B描述) 声纹差异。
差异大=speaker生效(真换音色)；几乎相同=又被吞（无效）。"""
import json, base64, subprocess, os

ROOT = "/Users/admin/kuleshov/.claude/worktrees/estee-lauder-night-video-7162e0/projects/uk-argentina-feud"
A = f"{ROOT}/audio"
r = json.load(open(f"{A}/response_spk.json"))
open(f"{A}/spk_a.mp3", "wb").write(base64.b64decode(r["audio"]))  # speaker=思思, sec02文本

try:
    from speechbrain.inference.speaker import SpeakerRecognition
except Exception:
    from speechbrain.pretrained import SpeakerRecognition
model = SpeakerRecognition.from_hparams(source="speechbrain/spkrec-ecapa-voxceleb", savedir="/tmp/spkrec-ecapa")

def towav(mp3):
    wav = mp3.replace(".mp3", ".16k.wav")
    if not os.path.exists(wav):
        subprocess.run(["ffmpeg", "-y", "-i", mp3, "-ar", "16000", "-ac", "1", wav], capture_output=True, check=True)
    return wav
def sim(a, b):
    s, _ = model.verify_files(towav(a), towav(b)); return round(float(s), 3)

s_spk_vs_b = sim(f"{A}/spk_a.mp3", f"{A}/sec02.mp3")   # 思思 vs B(同为sec02文本)
s_b_internal = sim(f"{A}/sec01.mp3", f"{A}/sec03.mp3")  # B内部两节参照
print(f"spk_a(预置思思) vs sec02原(B描述): {s_spk_vs_b}")
print(f"B内部参照 sec01 vs sec03        : {s_b_internal}")
print(f"判定：{'speaker 生效 ✅（真换了音色，可用于零漂移）' if s_spk_vs_b < s_b_internal - 0.15 else 'speaker 疑似被吞 ❌（音色没变）'}")
