#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""音色 gate 第三轮：4 个气质拉开的年轻女声候选，同句同语速，只变音色。
用风格标签（磁性/气泡音/温柔讲述/知性清冷）拉开差异；均守冷静克制零表演腔。"""
import json

ROOT = "/Users/admin/kuleshov/.claude/worktrees/estee-lauder-night-video-7162e0/projects/uk-argentina-feud"
d = json.load(open(f"{ROOT}/film.json", encoding="utf-8"))
text = next(s for s in d["audio"]["voiceover"]["sections"] if s["id"] == "sec01")["text"]

cands = {
    "A": ("磁性电台", "一位中文年轻女性讲述者，二十多岁，声音偏低、带磁性，像深夜情感电台主播那样娓娓道来，冷静克制、平实零表演腔，语速明快偏快"),
    "B": ("气泡音个性", "一位中文年轻女性讲述者，二十多岁，声音清亮里带一点气泡音的轻微沙质感，慵懒而自然、有记忆点，冷静克制、平实零表演腔，语速明快偏快"),
    "C": ("温柔讲述", "一位中文年轻女性讲述者，二十多岁，声音温柔、像给朋友讲故事一样娓娓道来，克制不煽情、零表演腔，语速明快偏快"),
    "D": ("知性清冷", "一位中文年轻女性讲述者，二十出头，声音清亮、知性、干净并带一点清冷疏离感，冷静克制、平实零表演腔，语速明快偏快"),
}
for k, (label, vp) in cands.items():
    tp = f'{vp}。朗读：“{text}”'
    payload = {"model": "seed-audio-1.0", "text_prompt": tp,
               "audio_config": {"format": "mp3", "sample_rate": 48000, "pitch_rate": 0,
                                "speech_rate": 20, "loudness_rate": 0, "enable_subtitle": False},
               "watermark": {}}
    json.dump(payload, open(f"{ROOT}/audio/payload_cand_{k}.json", "w", encoding="utf-8"), ensure_ascii=False)
    print(f"cand {k} [{label}] payload written ({len(tp)} chars)")
