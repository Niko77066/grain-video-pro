#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""探针：测 v3/tts/create 是否认参考音频字段。以 sec01 为参考，重合成 sec02，试 3 种格式。"""
import json, base64

ROOT = "/Users/admin/kuleshov/.claude/worktrees/estee-lauder-night-video-7162e0/projects/uk-argentina-feud"
b64 = base64.b64encode(open(f"{ROOT}/audio/sec01.mp3", "rb").read()).decode()
d = json.load(open(f"{ROOT}/film.json", encoding="utf-8"))
vo = d["audio"]["voiceover"]
vp = vo["voice_profile"]
t01 = next(s for s in vo["sections"] if s["id"] == "sec01")["text"]
t02 = next(s for s in vo["sections"] if s["id"] == "sec02")["text"]

base = {"model": "seed-audio-1.0", "text_prompt": f'{vp}。朗读：“{t02}”',
        "audio_config": {"format": "mp3", "sample_rate": 48000, "pitch_rate": 0,
                         "speech_rate": 0, "loudness_rate": 0, "enable_subtitle": True}, "watermark": {}}

p1 = dict(base); p1["reference_audio"] = {"audio": b64, "text": t01}
p2 = dict(base); p2["references"] = [{"audio": b64, "text": t01}]
p3 = dict(base); p3["reference_audio"] = b64  # 裸 base64

for name, p in [("probe1", p1), ("probe2", p2), ("probe3", p3)]:
    json.dump(p, open(f"{ROOT}/audio/payload_{name}.json", "w", encoding="utf-8"), ensure_ascii=False)
print(f"probe1=reference_audio对象(audio+text)  probe2=references数组  probe3=reference_audio裸b64 | ref音频b64={len(b64)}字符")
