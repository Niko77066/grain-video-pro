#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""MiniMax 版收尾：统一格式→拼接→whisper 逐词对齐→timeline→声纹复验一致性→G1→回填。
前提：mm_sec01..mm_sec06.mp3 已生成。SEQ 若 sec04 拆分则改。"""
import json, subprocess, os

ROOT = "/Users/admin/kuleshov/.claude/worktrees/estee-lauder-night-video-7162e0/projects/uk-argentina-feud"
A = f"{ROOT}/audio"
SEQ = ["sec01", "sec02", "sec03", "sec04", "sec05", "sec06"]
GAP = 0.35
VOICE = "audiobook_female_1"; SPEED = 1.1

def dur(f):
    return float(subprocess.run(["ffprobe", "-v", "error", "-show_entries", "format=duration",
                                 "-of", "csv=p=0", f], capture_output=True, text=True).stdout.strip())

# 1. 统一 48k stereo（MiniMax 出 32k mono），落到 sec$sid.mp3
for sid in SEQ:
    subprocess.run(["ffmpeg", "-y", "-i", f"{A}/mm_{sid}.mp3", "-ar", "48000", "-ac", "2",
                    "-c:a", "libmp3lame", "-b:a", "128k", f"{A}/{sid}.mp3"], check=True, capture_output=True)

# 2. gap + 拼接
subprocess.run(["ffmpeg", "-y", "-f", "lavfi", "-t", str(GAP), "-i", "anullsrc=r=48000:cl=stereo",
                "-c:a", "libmp3lame", "-b:a", "128k", f"{A}/_gap.mp3"], check=True, capture_output=True)
lines = []
for i, sid in enumerate(SEQ):
    lines.append(f"file '{A}/{sid}.mp3'")
    if i < len(SEQ) - 1:
        lines.append(f"file '{A}/_gap.mp3'")
open(f"{A}/concat_all.txt", "w").write("\n".join(lines) + "\n")
subprocess.run(["ffmpeg", "-y", "-f", "concat", "-safe", "0", "-i", f"{A}/concat_all.txt",
                "-c:a", "libmp3lame", "-b:a", "128k", "-ar", "48000", "-ac", "2",
                f"{A}/voiceover.mp3"], check=True, capture_output=True)
total = dur(f"{A}/voiceover.mp3")

# 3. whisper 全片逐词对齐（MiniMax 不自带时间戳）
words = []
try:
    import mlx_whisper
    r = mlx_whisper.transcribe(f"{A}/voiceover.mp3", path_or_hf_repo="mlx-community/whisper-large-v3-turbo",
                               language="zh", word_timestamps=True)
    for seg in r.get("segments", []):
        for w in seg.get("words", []):
            words.append({"w": w["word"].strip(), "t": [round(w["start"], 3), round(w["end"], 3)]})
    align = f"mlx-whisper word-ts ({len(words)} words)"
except Exception as e:
    align = f"逐词对齐失败(DEBT): {str(e)[:80]}"

# 4. 分节区间（各节时长累积，精确）
sections, off = [], 0.0
for i, sid in enumerate(SEQ):
    sd = dur(f"{A}/{sid}.mp3")
    sections.append({"id": sid, "t": [round(off, 3), round(off + sd, 3)], "rate_cpm": None})
    off += sd + (GAP if i < len(SEQ) - 1 else 0)
json.dump({"duration_s": round(total, 3), "gap_s": GAP, "sections": sections, "words": words},
          open(f"{A}/timeline.json", "w", encoding="utf-8"), ensure_ascii=False, indent=1)

# 5. 声纹复验一致性（固定音色应高度一致）
consistency = "未测"
try:
    try:
        from speechbrain.inference.speaker import SpeakerRecognition
    except Exception:
        from speechbrain.pretrained import SpeakerRecognition
    model = SpeakerRecognition.from_hparams(source="speechbrain/spkrec-ecapa-voxceleb", savedir="/tmp/spkrec-ecapa")
    def towav(mp3):
        wav = mp3.replace(".mp3", ".16k.wav")
        if not os.path.exists(wav):
            subprocess.run(["ffmpeg", "-y", "-i", mp3, "-ar", "16000", "-ac", "1", wav], capture_output=True, check=True)
        return wav
    scores = []
    for sid in SEQ[1:]:
        s, _ = model.verify_files(towav(f"{A}/sec01.mp3"), towav(f"{A}/{sid}.mp3"))
        scores.append(round(float(s), 3))
    consistency = f"vs sec01: {dict(zip(SEQ[1:], scores))} | min={min(scores)}"
except Exception as e:
    consistency = f"复验失败: {str(e)[:80]}"

# 6. 回填 film.json
d = json.load(open(f"{ROOT}/film.json", encoding="utf-8"))
vo = d["audio"]["voiceover"]
vo["engine"] = "minimax speech-2.8-hd (new-api网关)"
vo["voice"] = VOICE
vo["speed"] = SPEED
vo["file"] = "audio/voiceover.mp3"
vo["status"] = "generated"
for i, sid in enumerate(SEQ):
    sd = dur(f"{A}/{sid}.mp3")
    sec = next(s for s in vo["sections"] if s["id"] == sid)
    sec["status"] = "generated"
    sec["gen"] = {"engine": "minimax speech-2.8-hd", "voice": VOICE, "speed": SPEED,
                  "duration_actual_s": round(sd, 3), "rate_cpm": round(len(sec["text"]) / sd * 60, 1),
                  "file": f"audio/{sid}.mp3"}
d["audio"]["timeline"] = {"file": "audio/timeline.json", "duration_s": round(total, 3), "sections": sections}
json.dump(d, open(f"{ROOT}/film.json", "w", encoding="utf-8"), ensure_ascii=False, indent=2)

lo, hi = 245 * 0.9, 245 * 1.1
print(f"voiceover.mp3: {round(total,3)}s | 对齐: {align}")
print("各节 rate:", " ".join(f"{s['id']}={next(x for x in vo['sections'] if x['id']==s['id'])['gen']['rate_cpm']}" for s in sections))
print(f"G1 时长: {round(total,1)}s vs [220,270] → {'PASS' if lo<=total<=hi else 'FAIL(可调 speed)'}")
print(f"音色一致性(声纹): {consistency}")
