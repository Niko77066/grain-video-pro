#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""已知文本强制对齐（替代 whisper 转写戳）：wav2vec2-zh CTC + torchaudio.forced_align。
剧本每个字直接拿到真实音频戳，字幕/画面 cue 零漂移。
用法: forced_align.py <audio.mp3> <out_timeline.json>"""
import json, re, subprocess, sys, os
import torch, torchaudio
from transformers import Wav2Vec2ForCTC, Wav2Vec2Processor

ROOT = "/Users/admin/kuleshov/.claude/worktrees/estee-lauder-night-video-7162e0/projects/uk-argentina-feud"
MODEL = "jonatasgrosman/wav2vec2-large-xlsr-53-chinese-zh-cn"
audio_in, out_json = sys.argv[1], sys.argv[2]

# 1. 剧本全文 → 对齐目标字符序列（与 gen_captions 相同的 norm 规则）
d = json.load(open(f"{ROOT}/film.json", encoding="utf-8"))
full = "".join(s["text"] for s in d["audio"]["voiceover"]["sections"])
chars = [ch for ch in full if re.match(r"[一-鿿A-Za-z0-9]", ch)]
print(f"目标字符 {len(chars)}")

# 2. 音频 → 16k mono
wav16 = "/tmp/fa_16k.wav"
subprocess.run(["ffmpeg", "-y", "-i", audio_in, "-ar", "16000", "-ac", "1", wav16],
               check=True, capture_output=True)
wave, sr = torchaudio.load(wav16)
wave = wave[0]
dur = wave.shape[0] / sr
print(f"音频 {dur:.2f}s")

# 3. 模型 + 分块 emission（40s 块 / 5s 重叠，在重叠中点拼接避免边界撕裂）
proc = Wav2Vec2Processor.from_pretrained(MODEL)
model = Wav2Vec2ForCTC.from_pretrained(MODEL)
model.eval()
CHUNK, OVL = 40 * sr, 5 * sr
CORE = CHUNK - OVL          # 35s：各块核心区精确平铺，杜绝重复/缺失帧
FPS = sr / 320              # wav2vec2 帧率 50fps（帧距固定 20ms）
ems = []
k = 0
with torch.no_grad():
    while k * CORE < wave.shape[0]:
        s = k * CORE
        e = min(s + CHUNK, wave.shape[0])
        seg = wave[s:e]
        logits = model(seg.unsqueeze(0)).logits[0]  # (T,C)
        lp = torch.log_softmax(logits, dim=-1)
        seg_dur = (e - s) / sr
        core0 = (OVL / 2) / sr if k > 0 else 0.0
        core1 = seg_dur - ((OVL / 2) / sr if e < wave.shape[0] else 0.0)
        f0 = round(core0 * 50)
        f1 = min(lp.shape[0], round(core1 * 50))
        ems.append(lp[f0:f1])
        print(f"  chunk {s/sr:7.1f}-{e/sr:7.1f}s core [{s/sr+core0:.1f},{s/sr+core1:.1f}] -> {f1-f0} frames")
        if e >= wave.shape[0]:
            break
        k += 1
emission = torch.cat(ems, dim=0)
n_frames = emission.shape[0]
frame_dur = 0.02            # 固定帧距，不再用 dur/n_frames 均匀缩放
drift = abs(n_frames * frame_dur - dur)
print(f"emission {n_frames} frames vs 期望 {dur*50:.0f} (差 {drift:.2f}s，应 <0.1s/块数)")
assert drift < 0.5, "分块平铺仍有帧数偏差，禁止继续"

# 4. 目标 token id（OOV 字记下位置后插值）
vocab = proc.tokenizer.get_vocab()
blank = proc.tokenizer.pad_token_id
ids, keep_idx, oov = [], [], []
for i, ch in enumerate(chars):
    tid = vocab.get(ch, vocab.get(ch.upper(), None))
    if tid is None or tid == vocab.get(proc.tokenizer.unk_token):
        oov.append(i)
    else:
        ids.append(tid); keep_idx.append(i)
print(f"可对齐 {len(ids)} / OOV {len(oov)}: {[chars[i] for i in oov][:20]}")

targets = torch.tensor([ids], dtype=torch.int32)
aligned, scores = torchaudio.functional.forced_align(emission.unsqueeze(0), targets, blank=blank)
spans = torchaudio.functional.merge_tokens(aligned[0], scores[0], blank=blank)

t = [None] * len(chars)
for span, ci in zip(spans, keep_idx):
    t[ci] = [round(span.start * frame_dur, 3), round(span.end * frame_dur, 3)]
# OOV 插值
for i in oov:
    lo = next((t[j] for j in range(i - 1, -1, -1) if t[j]), [0.0, 0.0])
    hi = next((t[j] for j in range(i + 1, len(chars)) if t[j]), [dur, dur])
    t[i] = [lo[1], hi[0]]

words = [{"w": ch, "t": tt} for ch, tt in zip(chars, t)]
json.dump({"duration_s": round(dur, 2), "align": f"forced_align {MODEL}",
           "n_chars": len(chars), "words": words},
          open(out_json, "w", encoding="utf-8"), ensure_ascii=False)
print(f"写出 {out_json}")
for w in words[:6] + words[-4:]:
    print(" ", w["w"], w["t"])
