#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""测多个 MiniMax 女声整条稳定性：各生成 sec03(~52s)分段声纹，选 min 最高。"""
import json, os, subprocess
try:
    from speechbrain.inference.speaker import SpeakerRecognition
except Exception:
    from speechbrain.pretrained import SpeakerRecognition
m = SpeakerRecognition.from_hparams(source="speechbrain/spkrec-ecapa-voxceleb", savedir="/tmp/spkrec-ecapa")

ROOT = "/Users/admin/kuleshov/.claude/worktrees/estee-lauder-night-video-7162e0/projects/uk-argentina-feud"
KEY = os.environ["MINIMAX_MUSIC_API_KEY"]; BASE = os.environ["MINIMAX_MUSIC_BASE_URL"]
d = json.load(open(f"{ROOT}/film.json", encoding="utf-8"))
sec03 = next(s["text"] for s in d["audio"]["voiceover"]["sections"] if s["id"] == "sec03")
VOICES = ["audiobook_female_1", "presenter_female", "female-yujie", "female-chengshu", "female-shaonv"]

def dur(f): return float(subprocess.run(["ffprobe","-v","error","-show_entries","format=duration","-of","csv=p=0",f],capture_output=True,text=True).stdout.strip())
def sim(a,b):
    s,_=m.verify_files(a,b); return round(float(s),3)

res={}
for v in VOICES:
    p={"model":"speech-2.8-hd","voice":v,"input":sec03,"response_format":"hex",
       "metadata":{"audio_setting":{"format":"mp3"},"voice_setting":{"speed":1.1,"vol":1,"pitch":0,"emotion":"neutral","english_normalization":True},"language_boost":"Chinese"}}
    json.dump(p,open("/tmp/vp.json","w",encoding="utf-8"),ensure_ascii=False)
    r=subprocess.run(["curl","-sS","-X","POST",f"{BASE}/audio/speech","-H",f"Authorization: Bearer {KEY}","-H","Content-Type: application/json","--data-binary","@/tmp/vp.json","-o",f"/tmp/vt_{v}.mp3"],capture_output=True)
    try:
        D=dur(f"/tmp/vt_{v}.mp3")
    except Exception as e:
        print(v,"gen FAIL",str(e)[:60]); continue
    pts=[(2,14),(D/2-6,D/2+6),(D-14,D-2)]
    for i,(s,e) in enumerate(pts):
        subprocess.run(["ffmpeg","-y","-ss",str(s),"-to",str(e),"-i",f"/tmp/vt_{v}.mp3","-ar","16000","-ac","1",f"/tmp/vs_{v}_{i}.wav"],capture_output=True)
    sims=[sim(f"/tmp/vs_{v}_0.wav",f"/tmp/vs_{v}_{i}.wav") for i in (1,2)]
    res[v]=min(sims)
    print(f"  {v}: {D:.0f}s, 段间 {sims}, min={min(sims)}")
if res:
    best=max(res,key=res.get)
    print("最稳音色:",best,"min=",res[best])
