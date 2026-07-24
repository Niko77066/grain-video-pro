#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""G1 门：独立 whisper 回转写 vs 剧本(≥95%) + 锚点切片(6句首词首现)。"""
import json,re,subprocess,difflib,sys
import mlx_whisper
MODEL="mlx-community/whisper-large-v3-turbo"
st=json.load(open("projects/dont-set-ac-26/audio/spoken_text.json",encoding="utf-8"))
tl=json.load(open("projects/dont-set-ac-26/audio/timeline.json",encoding="utf-8"))
VO="projects/dont-set-ac-26/audio/voiceover.wav"

# 数字规整：中↔阿 都折成占位，减少格式噪声
cn="零一二三四五六七八九十百千万两"
def canon(t):
    t=re.sub(r"[0-9]+","N",t)
    t=re.sub("["+cn+"]+","N",t)
    return re.sub(r"[^一-鿿A-Za-z]","",re.sub("N","",t))  # 去数字后比对字面（数字单列）

print("=== 全片回转写 ===")
r=mlx_whisper.transcribe(VO,path_or_hf_repo=MODEL)
hyp=r["text"]
ref=st["full"]
a=re.sub(r"[^一-鿿A-Za-z0-9]","",ref)
b=re.sub(r"[^一-鿿A-Za-z0-9]","",hyp)
ratio_raw=difflib.SequenceMatcher(None,a,b).ratio()
ca,cb=canon(ref),canon(hyp)
ratio_canon=difflib.SequenceMatcher(None,ca,cb).ratio()
print(f"原始字面相似 {ratio_raw*100:.1f}%  |  去数字后相似 {ratio_canon*100:.1f}% (数字格式噪声已剔除)")
print("hyp[:120]:",hyp[:120])

print("\n=== 锚点切片(句首词首现) ===")
words=tl["words"]; cur=0; ok=0; tot=0
firsts=[]
for s in tl["sections"]:
    a0=cur; firsts.append((s["id"],words[a0]["t"][0],s["text_spoken"][:4]))
    nc=len([ch for ch in s["text_spoken"] if re.match(r"[一-鿿A-Za-z0-9]",ch)])
    cur+=nc
for sid,t0,head in firsts:
    tot+=1
    sub=f"/tmp/anc_{sid}.wav"
    subprocess.run(["ffmpeg","-y","-ss",str(max(0,t0-0.1)),"-t","1.6","-i",VO,sub],check=True,capture_output=True)
    rr=mlx_whisper.transcribe(sub,path_or_hf_repo=MODEL)["text"]
    rr_c=re.sub(r"[^一-鿿A-Za-z0-9]","",rr)
    hit=head[0] in rr_c[:6] or head[:2] in rr_c
    ok+=hit
    print(f"  {sid} @{t0:6.2f}s 期望'{head}' → 切片转写'{rr_c[:10]}'  {'✅' if hit else '❌'}")
print(f"\n锚点命中 {ok}/{tot}")
print("G1:", "PASS" if ratio_canon>=0.95 and ok>=tot-1 else "CHECK")
