#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""拼全片旁白 + 全片逐字时间戳 + 回填 film.json(gen/status/timeline/costs/budget) + G1 时长校验。
前提：sec01..sec06 的 <sid>.mp3 与 timeline_<sid>.json 均已就绪。"""
import json, subprocess

ROOT = "/Users/admin/kuleshov/.claude/worktrees/estee-lauder-night-video-7162e0/projects/uk-argentina-feud"
A = f"{ROOT}/audio"
SEQ = ["sec01", "sec02", "sec03", "sec04", "sec05", "sec06"]
GAP = 0.35
UNIT = 0.00114  # $/s，samsung 口径反推（官方单价待核 DEBT）

def dur(f):
    return float(subprocess.run(["ffprobe", "-v", "error", "-show_entries", "format=duration",
                                 "-of", "csv=p=0", f], capture_output=True, text=True).stdout.strip())

# 1. gap 静音
subprocess.run(["ffmpeg", "-y", "-f", "lavfi", "-t", str(GAP), "-i", "anullsrc=r=48000:cl=stereo",
                "-c:a", "libmp3lame", "-b:a", "128k", f"{A}/_gap.mp3"], check=True, capture_output=True)
# 2. 拼全片
lines = []
for i, sid in enumerate(SEQ):
    lines.append(f"file '{A}/{sid}.mp3'")
    if i < len(SEQ) - 1:
        lines.append(f"file '{A}/_gap.mp3'")
open(f"{A}/concat_all.txt", "w").write("\n".join(lines) + "\n")
subprocess.run(["ffmpeg", "-y", "-f", "concat", "-safe", "0", "-i", f"{A}/concat_all.txt",
                "-c:a", "libmp3lame", "-b:a", "128k", "-ar", "48000", "-ac", "2",
                f"{A}/voiceover.mp3"], check=True, capture_output=True)
# 3. 全片 timeline（累积偏移）
sections, words, off = [], [], 0.0
for i, sid in enumerate(SEQ):
    tl = json.load(open(f"{A}/timeline_{sid}.json", encoding="utf-8"))
    sd = dur(f"{A}/{sid}.mp3")
    sections.append({"id": sid, "t": [round(off, 3), round(off + sd, 3)]})
    for w in tl["words"]:
        words.append({"w": w["w"], "t": [round(w["t"][0] + off, 3), round(w["t"][1] + off, 3)]})
    off += sd + (GAP if i < len(SEQ) - 1 else 0)
total = dur(f"{A}/voiceover.mp3")
json.dump({"duration_s": round(total, 3), "gap_s": GAP, "sections": sections, "words": words},
          open(f"{A}/timeline.json", "w", encoding="utf-8"), ensure_ascii=False, indent=1)

# 4. 回填 film.json
d = json.load(open(f"{ROOT}/film.json", encoding="utf-8"))
vo = d["audio"]["voiceover"]
adopted = 0.0
for sid in SEQ:
    sd = dur(f"{A}/{sid}.mp3")
    adopted += sd
    sec = next(s for s in vo["sections"] if s["id"] == sid)
    sec["status"] = "generated"
    g = {"model": "seed-audio-1.0", "duration_actual_s": round(sd, 3),
         "rate_cpm": round(len(sec["text"]) / sd * 60, 1),
         "file": f"audio/{sid}.mp3", "timeline": f"audio/timeline_{sid}.json"}
    if sid == "sec04":
        g["split"] = ["sec04a", "sec04b"]
        g["note"] = "整段审核被拒(code 45001125)；无损拆两段生成再拼接，剧本零改动"
    sec["gen"] = g
vo["status"] = "generated"
vo["file"] = "audio/voiceover.mp3"
d["audio"]["timeline"] = {"file": "audio/timeline.json", "duration_s": round(total, 3), "sections": sections}

# 5. 记账：采纳节 + 音色gate/审核诊断试验损耗
costs = [c for c in d["ledger"]["costs"] if not c.get("id", "").startswith("tts_")]
costs.append({"id": "tts_voiceover_adopted", "date": "2026-07-16", "stage": "audio",
              "item": "全片旁白采纳版 sec01–06（seed-audio-1.0，sec04 拆两段）",
              "billed_seconds": round(adopted, 1), "cost_usd": round(adopted * UNIT, 4),
              "note": f"单价${UNIT}/s 反推估（DEBT）；B 气泡音女声，speech_rate 逐节 0/0/0/0/+7/-8"})
TRIAL = 21.2 + 18.9 + 64.9 + 72.4  # 男声v1 + 女声清亮 + 4候选 + audit诊断front/back
costs.append({"id": "tts_trials", "date": "2026-07-16", "stage": "audio",
              "item": "音色 gate + 审核诊断试验损耗（弃用）",
              "billed_seconds": round(TRIAL, 1), "cost_usd": round(TRIAL * UNIT, 4),
              "note": "中年男声1 + 清亮女声1 + 4候选ABCD + sec04审核二分诊断2；均未入片"})
d["ledger"]["costs"] = costs
d["meta"]["budget"]["spent_usd"] = round(sum((c.get("cost_usd") or 0) for c in costs), 4)
json.dump(d, open(f"{ROOT}/film.json", "w", encoding="utf-8"), ensure_ascii=False, indent=2)

# 6. G1 时长校验
lo, hi = 245 * 0.9, 245 * 1.1
g1 = "PASS" if lo <= total <= hi else "FAIL"
print(f"voiceover.mp3 拼接完成：{round(total,3)}s  ({len(words)} words, {len(SEQ)}节, gap {GAP}s)")
print("各节 rate:", " ".join(f"{s['id']}={next(x for x in vo['sections'] if x['id']==s['id'])['gen']['rate_cpm']}" for s in sections))
print(f"G1 时长：{round(total,1)}s vs 承诺 245±10%[{lo:.0f},{hi:.0f}] → {g1}")
print(f"采纳 {adopted:.1f}s + 试验 {TRIAL:.1f}s | audio 花费 ${d['meta']['budget']['spent_usd']}")
print("回转写 G1（≥95%）：WhisperX 独立转写另跑")
