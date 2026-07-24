#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""定位 sec04 内容审核触发段：前半/后半分别测。诊断用，不入片。"""
import json

ROOT = "/Users/admin/kuleshov/.claude/worktrees/estee-lauder-night-video-7162e0/projects/uk-argentina-feud"
d = json.load(open(f"{ROOT}/film.json", encoding="utf-8"))
vp = d["audio"]["voiceover"]["voice_profile"]

parts = {
    "front": "那年四月二日，阿根廷军政府出兵占了马岛。这片群岛，阿根廷叫马尔维纳斯，英国叫福克兰。它离阿根廷本土四百八十公里，离英国一万两千七百公里。军政府当时通胀失控，国内到处是抗议，他们赌的就是这个距离：英国不会为几座荒岛跑半个地球。撒切尔真把舰队派来了。五月二日，英国核潜艇击沉巡洋舰贝尔格拉诺将军号，三百二十三人沉进南大西洋。",
    "back": "阿根廷整场战争阵亡六百四十九人，一半折在这一艘船上。两天后阿根廷还了一击，飞鱼导弹打中谢菲尔德号，二十人死亡，那是二战之后英国头一回有军舰被击沉。七十四天后，阿军投降。六百四十九个阿根廷人、二百五十五个英国人、三个岛民，没能回家。战败第三天，加尔铁里下台，军政府垮了。伦敦那头，撒切尔的支持率一路涨，第二年大选轻松连任。仗打完了。账没算完。",
}
for k, t in parts.items():
    tp = f'{vp}。朗读：“{t}”'
    p = {"model": "seed-audio-1.0", "text_prompt": tp,
         "audio_config": {"format": "mp3", "sample_rate": 48000, "pitch_rate": 0,
                          "speech_rate": 0, "loudness_rate": 0, "enable_subtitle": False}, "watermark": {}}
    json.dump(p, open(f"{ROOT}/audio/payload_diag_{k}.json", "w", encoding="utf-8"), ensure_ascii=False)
    print(f"wrote diag_{k} ({len(t)} chars)")
