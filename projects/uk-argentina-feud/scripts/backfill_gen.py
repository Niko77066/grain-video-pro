#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""回填某节 TTS 的 gen + status + ledger.costs + budget.spent。
用法: backfill_gen.py <sid> [wallclock_s] [speech_rate]"""
import json, sys

ROOT = "/Users/admin/kuleshov/.claude/worktrees/estee-lauder-night-video-7162e0/projects/uk-argentina-feud"
sid = sys.argv[1]
wall = float(sys.argv[2]) if len(sys.argv) > 2 else None
sr = int(sys.argv[3]) if len(sys.argv) > 3 else 0
UNIT = 0.00114  # $/s，samsung 口径反推；官方单价待核（DEBT）

tl = json.load(open(f"{ROOT}/audio/timeline_{sid}.json", encoding="utf-8"))
dur = tl["duration_s"]
d = json.load(open(f"{ROOT}/film.json", encoding="utf-8"))
sec = next(s for s in d["audio"]["voiceover"]["sections"] if s["id"] == sid)
cost = round(dur * UNIT, 4)

sec["status"] = "generated"
sec["gen"] = {
    "model": "seed-audio-1.0", "speech_rate": sr,
    "duration_actual_s": dur, "rate_cpm": round(len(sec["text"]) / dur * 60, 1),
    "file": f"audio/{sid}.mp3", "timeline": f"audio/timeline_{sid}.json",
    "payload": f"audio/payload_{sid}.json", "cost_usd": cost, "wallclock_s": wall,
}
costs = d["ledger"]["costs"]
cid = f"tts_{sid}"
costs[:] = [c for c in costs if c.get("id") != cid]
costs.append({"id": cid, "date": "2026-07-16", "stage": "audio",
              "item": f"TTS {sid}（seed-audio-1.0）", "billed_seconds": dur, "cost_usd": cost,
              "note": f"单价按 samsung ${UNIT}/s 反推估（官方单价待核 DEBT）；speech_rate={sr}"})
d["meta"]["budget"]["spent_usd"] = round(sum((c.get("cost_usd") or 0) for c in costs), 4)
json.dump(d, open(f"{ROOT}/film.json", "w", encoding="utf-8"), ensure_ascii=False, indent=2)
print(f"backfilled {sid}: status=generated dur={dur}s rate={sec['gen']['rate_cpm']}cpm cost=${cost} | spent_total=${d['meta']['budget']['spent_usd']}")
