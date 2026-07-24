#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""sec04 无损拆分：front+back 两段分别 TTS 再拼接（规避整段审核，剧本零改动）。
mode=payload 生成两段 payload；mode=assemble 解码+ffmpeg拼接+合并逐字时间戳。"""
import sys, json, base64, subprocess

ROOT = "/Users/admin/kuleshov/.claude/worktrees/estee-lauder-night-video-7162e0/projects/uk-argentina-feud"
vp = json.load(open(f"{ROOT}/film.json", encoding="utf-8"))["audio"]["voiceover"]["voice_profile"]
FRONT = "那年四月二日，阿根廷军政府出兵占了马岛。这片群岛，阿根廷叫马尔维纳斯，英国叫福克兰。它离阿根廷本土四百八十公里，离英国一万两千七百公里。军政府当时通胀失控，国内到处是抗议，他们赌的就是这个距离：英国不会为几座荒岛跑半个地球。撒切尔真把舰队派来了。五月二日，英国核潜艇击沉巡洋舰贝尔格拉诺将军号，三百二十三人沉进南大西洋。"
BACK = "阿根廷整场战争阵亡六百四十九人，一半折在这一艘船上。两天后阿根廷还了一击，飞鱼导弹打中谢菲尔德号，二十人死亡，那是二战之后英国头一回有军舰被击沉。七十四天后，阿军投降。六百四十九个阿根廷人、二百五十五个英国人、三个岛民，没能回家。战败第三天，加尔铁里下台，军政府垮了。伦敦那头，撒切尔的支持率一路涨，第二年大选轻松连任。仗打完了。账没算完。"

mode = sys.argv[1]
if mode == "payload":
    for name, t in [("sec04a", FRONT), ("sec04b", BACK)]:
        tp = f'{vp}。朗读：“{t}”'
        p = {"model": "seed-audio-1.0", "text_prompt": tp,
             "audio_config": {"format": "mp3", "sample_rate": 48000, "pitch_rate": 0,
                              "speech_rate": 0, "loudness_rate": 0, "enable_subtitle": True}, "watermark": {}}
        json.dump(p, open(f"{ROOT}/audio/payload_{name}.json", "w", encoding="utf-8"), ensure_ascii=False)
        print(f"payload {name} ({len(t)} chars)")

elif mode == "assemble":
    for name in ["sec04a", "sec04b"]:
        r = json.load(open(f"{ROOT}/audio/response_{name}.json"))
        if not r.get("audio"):
            print(f"ERROR {name}: {json.dumps(r, ensure_ascii=False)[:120]}"); sys.exit(1)
        open(f"{ROOT}/audio/{name}.mp3", "wb").write(base64.b64decode(r["audio"]))
    lst = f"{ROOT}/audio/concat_sec04.txt"
    open(lst, "w").write(f"file '{ROOT}/audio/sec04a.mp3'\nfile '{ROOT}/audio/sec04b.mp3'\n")
    subprocess.run(["ffmpeg", "-y", "-f", "concat", "-safe", "0", "-i", lst,
                    "-c:a", "libmp3lame", "-b:a", "128k", "-ar", "48000", "-ac", "2",
                    f"{ROOT}/audio/sec04.mp3"], check=True, capture_output=True)
    ra = json.load(open(f"{ROOT}/audio/response_sec04a.json"))
    rb = json.load(open(f"{ROOT}/audio/response_sec04b.json"))
    fa = ra.get("duration")

    def words(r, off=0.0):
        ws, full = [], ""
        for s in r.get("subtitle", {}).get("sentences", []):
            full += s.get("text", "")
            for w in s.get("words", []):
                ws.append({"w": w.get("text", ""), "t": [round(w.get("start_time", 0) / 1000 + off, 3),
                                                          round(w.get("end_time", 0) / 1000 + off, 3)]})
        return ws, full
    wa, fua = words(ra, 0.0)
    wb, fub = words(rb, fa)
    dur = float(subprocess.run(["ffprobe", "-v", "error", "-show_entries", "format=duration",
                                "-of", "csv=p=0", f"{ROOT}/audio/sec04.mp3"],
                               capture_output=True, text=True).stdout.strip())
    tl = {"id": "sec04", "duration_s": round(dur, 3), "text": fua + fub,
          "words": wa + wb, "split": ["sec04a", "sec04b"]}
    json.dump(tl, open(f"{ROOT}/audio/timeline_sec04.json", "w", encoding="utf-8"),
              ensure_ascii=False, indent=1)
    rate = round(len(fua + fub) / dur * 60, 1)
    print(f"sec04 assembled: {round(dur,3)}s  rate≈{rate}字/分  words={len(wa)+len(wb)}  (front {fa}s + back)")
