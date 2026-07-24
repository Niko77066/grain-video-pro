#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""构建 MiniMax speech-2.8-hd 请求体（new-api 网关, OpenAI 兼容 /audio/speech）。
用法: mm_payload.py <section_id> <voice_id> [speed] [emotion]"""
import json, sys

ROOT = "/Users/admin/kuleshov/.claude/worktrees/estee-lauder-night-video-7162e0/projects/uk-argentina-feud"
sid = sys.argv[1]
voice = sys.argv[2]
speed = float(sys.argv[3]) if len(sys.argv) > 3 else 1.0
emotion = sys.argv[4] if len(sys.argv) > 4 else "neutral"

d = json.load(open(f"{ROOT}/film.json", encoding="utf-8"))
text = next(s for s in d["audio"]["voiceover"]["sections"] if s["id"] == sid)["text"]

p = {"model": "speech-2.8-hd", "voice": voice, "input": text, "response_format": "hex",
     "metadata": {"audio_setting": {"format": "mp3"},
                  "voice_setting": {"speed": speed, "vol": 1, "pitch": 0,
                                    "emotion": emotion, "english_normalization": True},
                  "language_boost": "Chinese"}}
json.dump(p, open(f"{ROOT}/audio/mm_payload_{sid}.json", "w", encoding="utf-8"), ensure_ascii=False)
print(f"mm payload {sid}: voice={voice} speed={speed} emotion={emotion} chars={len(text)}")
