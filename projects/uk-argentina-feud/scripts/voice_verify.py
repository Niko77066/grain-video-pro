#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""声纹比对：验证 reference_audio 锚定是否生效 + 量化当前 6 节音色漂移。
speechbrain ECAPA speaker verification，分数越高越像同一说话人。"""
import json, base64, subprocess, os

ROOT = "/Users/admin/kuleshov/.claude/worktrees/estee-lauder-night-video-7162e0/projects/uk-argentina-feud"
A = f"{ROOT}/audio"

try:
    from speechbrain.inference.speaker import SpeakerRecognition
except Exception:
    from speechbrain.pretrained import SpeakerRecognition
model = SpeakerRecognition.from_hparams(source="speechbrain/spkrec-ecapa-voxceleb",
                                        savedir="/tmp/spkrec-ecapa")

def towav(mp3):
    wav = mp3.replace(".mp3", ".16k.wav")
    if not os.path.exists(wav):
        subprocess.run(["ffmpeg", "-y", "-i", mp3, "-ar", "16000", "-ac", "1", wav],
                       capture_output=True, check=True)
    return wav

def sim(a, b):
    score, _ = model.verify_files(towav(a), towav(b))
    return round(float(score), 3)

# 解码 probe3
r = json.load(open(f"{A}/response_probe3.json"))
if r.get("audio"):
    open(f"{A}/probe3.mp3", "wb").write(base64.b64decode(r["audio"]))

print("=== reference_audio 锚定是否生效（sec01 为参考基准）===")
base = sim(f"{A}/sec01.mp3", f"{A}/sec02.mp3")
prb = sim(f"{A}/sec01.mp3", f"{A}/probe3.mp3")
print(f"  sec01 vs sec02  (原/无参考) : {base}")
print(f"  sec01 vs probe3 (reference_audio=sec01) : {prb}")
print(f"  → 提升 {round(prb-base,3)}  判定：{'锚定生效 ✅' if prb-base>0.1 else '未生效/存疑 ❌'}")

print("=== 当前 6 节音色漂移矩阵（vs sec01，<0.25 通常判不同说话人）===")
for s in ["sec02", "sec03", "sec04", "sec05", "sec06"]:
    print(f"  sec01 vs {s}: {sim(f'{A}/sec01.mp3', f'{A}/{s}.mp3')}")
