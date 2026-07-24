#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""从 film.json 读某节，构建 seed-audio-1.0 请求 payload。
用法: make_payload.py <section_id> [speech_rate] [ref_audio_mp3]
旁白轨纪律：text_prompt 只含 声音档描述 + 朗读 + 文本；不写音效/音乐/多角色。"""
import json, sys, base64

ROOT = "/Users/admin/kuleshov/.claude/worktrees/estee-lauder-night-video-7162e0/projects/uk-argentina-feud"
P = f"{ROOT}/film.json"
sid = sys.argv[1]
speech_rate = int(sys.argv[2]) if len(sys.argv) > 2 else 0
ref_audio = sys.argv[3] if len(sys.argv) > 3 and sys.argv[3] not in ("", "-") else None

d = json.load(open(P, encoding="utf-8"))
vo = d["audio"]["voiceover"]
vp = vo["voice_profile"]
sec = next(s for s in vo["sections"] if s["id"] == sid)
text = sec["text"]

text_prompt = f'{vp}。朗读：“{text}”'
payload = {
    "model": "seed-audio-1.0",
    "text_prompt": text_prompt,
    "audio_config": {"format": "mp3", "sample_rate": 48000, "pitch_rate": 0,
                     "speech_rate": speech_rate, "loudness_rate": 0, "enable_subtitle": True},
    "watermark": {},
}
if ref_audio:
    b = base64.b64encode(open(ref_audio, "rb").read()).decode()
    payload["references"] = [{"audio_data": b, "type": "audio"}]

out = f"{ROOT}/audio/payload_{sid}.json"
json.dump(payload, open(out, "w", encoding="utf-8"), ensure_ascii=False)
print(f"wrote {out}")
print(f"  section={sid} chars={len(text)} text_prompt_chars={len(text_prompt)} speech_rate={speech_rate} ref={'yes' if ref_audio else 'no'}")
