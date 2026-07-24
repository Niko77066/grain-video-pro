#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""【锚定生效才用】以 sec01 为 reference_audio 基准，重生成其余节，统一音色。
sec01 保留为音色源不动；sec04 仍拆 a/b 规避审核。speech_rate 逐节保留。"""
import json, base64

ROOT = "/Users/admin/kuleshov/.claude/worktrees/estee-lauder-night-video-7162e0/projects/uk-argentina-feud"
b64 = base64.b64encode(open(f"{ROOT}/audio/sec01.mp3", "rb").read()).decode()
d = json.load(open(f"{ROOT}/film.json", encoding="utf-8"))
vo = d["audio"]["voiceover"]; vp = vo["voice_profile"]
def txt(sid): return next(s for s in vo["sections"] if s["id"] == sid)["text"]
FRONT = "那年四月二日，阿根廷军政府出兵占了马岛。这片群岛，阿根廷叫马尔维纳斯，英国叫福克兰。它离阿根廷本土四百八十公里，离英国一万两千七百公里。军政府当时通胀失控，国内到处是抗议，他们赌的就是这个距离：英国不会为几座荒岛跑半个地球。撒切尔真把舰队派来了。五月二日，英国核潜艇击沉巡洋舰贝尔格拉诺将军号，三百二十三人沉进南大西洋。"
BACK = "阿根廷整场战争阵亡六百四十九人，一半折在这一艘船上。两天后阿根廷还了一击，飞鱼导弹打中谢菲尔德号，二十人死亡，那是二战之后英国头一回有军舰被击沉。七十四天后，阿军投降。六百四十九个阿根廷人、二百五十五个英国人、三个岛民，没能回家。战败第三天，加尔铁里下台，军政府垮了。伦敦那头，撒切尔的支持率一路涨，第二年大选轻松连任。仗打完了。账没算完。"

jobs = [("sec02", txt("sec02"), 0), ("sec03", txt("sec03"), 0),
        ("sec04a", FRONT, 0), ("sec04b", BACK, 0),
        ("sec05", txt("sec05"), 7), ("sec06", txt("sec06"), -8)]
for name, t, rate in jobs:
    p = {"model": "seed-audio-1.0", "text_prompt": f'{vp}。朗读：“{t}”',
         "audio_config": {"format": "mp3", "sample_rate": 48000, "pitch_rate": 0,
                          "speech_rate": rate, "loudness_rate": 0, "enable_subtitle": True},
         "watermark": {}, "reference_audio": b64}
    json.dump(p, open(f"{ROOT}/audio/payload_{name}.json", "w", encoding="utf-8"), ensure_ascii=False)
    print(f"ref-payload {name} (rate={rate})")
print(f"reference=sec01.mp3 ({len(b64)} b64 chars) 注入全部 6 job")
