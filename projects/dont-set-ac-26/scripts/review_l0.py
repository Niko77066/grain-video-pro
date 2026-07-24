#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""⑨ L0 手动仪器复检 final.mp4：时长/分辨率/帧率、黑帧、冻结帧、响度、回转写 vs 剧本。出示证据。"""
import json,subprocess,re,sys
V="projects/dont-set-ac-26/out/final.mp4"
def run(c): return subprocess.run(c,capture_output=True,text=True)
print("=== 1. 容器/流 ===")
r=run(["ffprobe","-v","error","-show_entries","format=duration:stream=codec_type,codec_name,width,height,r_frame_rate,channels,sample_rate","-of","json",V])
info=json.loads(r.stdout); dur=float(info["format"]["duration"])
for s in info["streams"]:
    if s["codec_type"]=="video": print(f"  video {s['codec_name']} {s['width']}x{s['height']} {s['r_frame_rate']}")
    if s["codec_type"]=="audio": print(f"  audio {s['codec_name']} {s.get('channels')}ch {s.get('sample_rate')}Hz")
print(f"  duration {dur:.2f}s (timeline 185.64 期望)")
print("=== 2. 黑帧 blackdetect(d=0.4) ===")
r=run(["ffmpeg","-i",V,"-vf","blackdetect=d=0.4:pic_th=0.98","-an","-f","null","-"])
bl=[l for l in r.stderr.splitlines() if "black_start" in l]
print("  黑帧段:",len(bl)); [print("   ",l.strip()) for l in bl[:8]]
print("=== 3. 冻结帧 freezedetect(n=-60dB,d=0.7) ===")
r=run(["ffmpeg","-i",V,"-vf","freezedetect=n=-60dB:d=0.7","-an","-f","null","-"])
fz=[l for l in r.stderr.splitlines() if "freeze_start" in l]
print("  冻结段:",len(fz)); [print("   ",l.strip()) for l in fz[:10]]
print("=== 4. 响度 loudnorm 测量 ===")
r=run(["ffmpeg","-i",V,"-af","loudnorm=I=-14:TP=-1.5:LRA=11:print_format=json","-f","null","-"])
m=re.search(r'\{[^{}]*"input_i"[^{}]*\}',r.stderr,re.S)
if m:
    j=json.loads(m.group(0)); print(f"  input_i {j.get('input_i')} LUFS | input_tp {j.get('input_tp')} dBTP | LRA {j.get('input_lra')}")
print("=== 5. 回转写 vs 剧本(独立whisper) ===")
try:
    import mlx_whisper
    r=mlx_whisper.transcribe(V,path_or_hf_repo="mlx-community/whisper-large-v3-turbo")
    hyp=re.sub(r"[^一-鿿A-Za-z0-9]","",r["text"])
    ref=re.sub(r"[^一-鿿A-Za-z0-9]","",json.load(open("projects/dont-set-ac-26/audio/spoken_text.json"))["full"])
    import difflib
    def canon(t): return re.sub(r"[0-9零一二三四五六七八九十百千万两]+","",t)
    ratio=difflib.SequenceMatcher(None,canon(ref),canon(hyp)).ratio()
    print(f"  去数字后字面相似 {ratio*100:.1f}% (≥95% 合格)")
except Exception as e:
    print("  whisper skip:",str(e)[:80])
print("DONE")
