#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""已知文本强制对齐：wav2vec2-zh CTC + torchaudio.forced_align（剧本 1:1 真实戳，零估算）。
改编自 uk-argentina-feud/scripts/forced_align.py（v5 分块平铺修复保留）。
用法: forced_align.py <audio> <spoken_text.json> <out_timeline.json>"""
import json, re, subprocess, sys
import torch, torchaudio
from transformers import Wav2Vec2ForCTC, Wav2Vec2Processor

MODEL = "jonatasgrosman/wav2vec2-large-xlsr-53-chinese-zh-cn"
audio_in, spoken_json, out_json = sys.argv[1], sys.argv[2], sys.argv[3]

st = json.load(open(spoken_json, encoding="utf-8"))
full = st["full"]
chars = [ch for ch in full if re.match(r"[一-鿿A-Za-z0-9]", ch)]
print(f"目标字符 {len(chars)}")

wav16 = "/tmp/fa_ac26_16k.wav"
subprocess.run(["ffmpeg","-y","-i",audio_in,"-ar","16000","-ac","1",wav16], check=True, capture_output=True)
wave, sr = torchaudio.load(wav16); wave = wave[0]
dur = wave.shape[0]/sr; print(f"音频 {dur:.2f}s")

proc = Wav2Vec2Processor.from_pretrained(MODEL)
model = Wav2Vec2ForCTC.from_pretrained(MODEL); model.eval()
CHUNK, OVL = 40*sr, 5*sr; CORE = CHUNK-OVL
ems=[]; k=0
with torch.no_grad():
    while k*CORE < wave.shape[0]:
        s=k*CORE; e=min(s+CHUNK, wave.shape[0]); seg=wave[s:e]
        lp=torch.log_softmax(model(seg.unsqueeze(0)).logits[0],dim=-1)
        seg_dur=(e-s)/sr
        core0=(OVL/2)/sr if k>0 else 0.0
        core1=seg_dur-((OVL/2)/sr if e<wave.shape[0] else 0.0)
        f0=round(core0*50); f1=min(lp.shape[0],round(core1*50))
        ems.append(lp[f0:f1])
        if e>=wave.shape[0]: break
        k+=1
emission=torch.cat(ems,dim=0); n_frames=emission.shape[0]; frame_dur=0.02
drift=abs(n_frames*frame_dur-dur); print(f"emission {n_frames} frames vs 期望 {dur*50:.0f} (差 {drift:.2f}s)")
assert drift<0.5, "分块平铺帧数偏差过大，禁止继续"

vocab=proc.tokenizer.get_vocab(); blank=proc.tokenizer.pad_token_id
ids=[];keep=[];oov=[]
for i,ch in enumerate(chars):
    tid=vocab.get(ch,vocab.get(ch.upper(),None))
    if tid is None or tid==vocab.get(proc.tokenizer.unk_token): oov.append(i)
    else: ids.append(tid);keep.append(i)
print(f"可对齐 {len(ids)} / OOV {len(oov)}: {[chars[i] for i in oov][:20]}")
targets=torch.tensor([ids],dtype=torch.int32)
aligned,scores=torchaudio.functional.forced_align(emission.unsqueeze(0),targets,blank=blank)
spans=torchaudio.functional.merge_tokens(aligned[0],scores[0],blank=blank)
t=[None]*len(chars)
for span,ci in zip(spans,keep): t[ci]=[round(span.start*frame_dur,3),round(span.end*frame_dur,3)]
for i in oov:
    lo=next((t[j] for j in range(i-1,-1,-1) if t[j]),[0.0,0.0])
    hi=next((t[j] for j in range(i+1,len(chars)) if t[j]),[dur,dur])
    t[i]=[lo[1],hi[0]]
words=[{"w":ch,"t":tt} for ch,tt in zip(chars,t)]
json.dump({"duration_s":round(dur,2),"align":f"forced_align {MODEL}","n_chars":len(chars),"words":words},
          open(out_json,"w",encoding="utf-8"),ensure_ascii=False)
print(f"写出 {out_json}")
for w in words[:6]+words[-4:]: print(" ",w["w"],w["t"])
