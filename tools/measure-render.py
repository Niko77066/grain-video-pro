#!/usr/bin/env python3
"""成片实测层（P0-1，2026-07-21 升级计划）：从终渲 mp4 反向核验，不信任何自报字段。

由来：五片对照实验——Codex 把 13 个幻灯片镜头全标 static_class:false 绕过了
全部 IR 门（实际 75% 静态持有）。本脚本产出 evidence/render-metrics.json，
是 style.contract.render 门的唯一证据源；自报与实测矛盾时以实测为准。

测量口径：
- 静态持有 = 相邻采样帧（降采样灰度 + boxblur 压掉胶片颗粒）平均绝对差低于阈值，
  连续时长 ≥0.8s 的段；hold_ratio = 静态持有总时长 / 全片时长。
- 阈值默认值来自 2026-07-21 四片标定（Claude 打磨双片 vs Codex 翻车双片，见 --help 尾注）。

用法：
  python3 tools/measure-render.py <project_dir> [--video out/final.mp4]
      [--out <evidence路径>] [--fps 4] [--width 160] [--static-threshold 0.0015]
"""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import re
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path

import numpy as np

FFMPEG = os.environ.get("FFMPEG", "ffmpeg")      # 走 PATH，可用环境变量覆盖（去本机硬编码）
FFPROBE = os.environ.get("FFPROBE", "ffprobe")
MIN_HOLD_S = 0.8          # 短于此的静止不算"持有"（正常剪辑呼吸）
SHOT_STATIC_RATIO = 0.7   # 镜头内持有占比超此判 measured_static


def probe(video: Path) -> dict:
    d = json.loads(subprocess.run(
        [FFPROBE, "-v", "error", "-print_format", "json",
         "-show_format", "-show_streams", str(video)],
        capture_output=True, text=True, check=True).stdout)
    v = next(s for s in d["streams"] if s["codec_type"] == "video")
    num, _, den = (v.get("avg_frame_rate") or "0/1").partition("/")
    return {"duration_s": float(d["format"]["duration"]),
            "width": int(v["width"]), "height": int(v["height"]),
            "fps": (float(num) / float(den)) if float(den or 1) else None,
            "bit_rate": int(d["format"].get("bit_rate", 0))}


def loudness_i(video: Path) -> float | None:
    err = subprocess.run(
        [FFMPEG, "-nostats", "-i", str(video), "-af", "ebur128", "-f", "null", "-"],
        capture_output=True, text=True).stderr
    m = re.findall(r"I:\s*(-?\d+(?:\.\d+)?)\s*LUFS", err)
    return float(m[-1]) if m else None


def gray_frames(video: Path, sample_fps: float, width: int, src_w: int, src_h: int):
    """降采样灰度帧流。boxblur 压颗粒——胶片颗粒会让逐帧差永不为零。"""
    h = max(2, round(src_h * width / src_w / 2) * 2)
    p = subprocess.run(
        [FFMPEG, "-loglevel", "error", "-i", str(video),
         "-vf", f"fps={sample_fps},scale={width}:{h},boxblur=2:1,format=gray",
         "-f", "rawvideo", "-"],
        capture_output=True, check=True)
    buf = np.frombuffer(p.stdout, dtype=np.uint8)
    n = len(buf) // (width * h)
    return buf[: n * width * h].reshape(n, h, width).astype(np.int16)


def static_segments(frames: np.ndarray, sample_fps: float, threshold: float):
    """返回 (segments, diffs)。segment = 连续静态帧对合并后 ≥MIN_HOLD_S 的区间。"""
    if len(frames) < 2:
        return [], []
    diffs = np.abs(np.diff(frames, axis=0)).mean(axis=(1, 2)) / 255.0
    静 = diffs < threshold
    dt = 1.0 / sample_fps
    segs, run_start = [], None
    for i, s in enumerate(list(静) + [False]):
        if s and run_start is None:
            run_start = i
        elif not s and run_start is not None:
            t0, t1 = run_start * dt, (i + 1) * dt   # 帧对 i 覆盖 [i*dt, (i+1)*dt]
            if t1 - t0 >= MIN_HOLD_S:
                segs.append({"t0": round(t0, 2), "t1": round(t1, 2),
                             "dur": round(t1 - t0, 2)})
            run_start = None
    return segs, diffs


def overlap(a0, a1, b0, b1) -> float:
    return max(0.0, min(a1, b1) - max(a0, b0))


def main() -> int:
    ap = argparse.ArgumentParser(
        description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="阈值标定（2026-07-21 四片）：0.0015 @ fps=4/width=160/boxblur=2:1——"
               "Codex hf 翻车片测 0.747（与其自报 75% 吻合）/ Claude hf 打磨片 0.619 / "
               "Claude 空调 0.303 / Codex ac-26c 0.422。改采样参数须重标。")
    ap.add_argument("project")
    ap.add_argument("--video", default="out/final.mp4")
    ap.add_argument("--out")
    ap.add_argument("--fps", type=float, default=4.0)
    ap.add_argument("--width", type=int, default=160)
    ap.add_argument("--static-threshold", type=float, default=0.0015)
    args = ap.parse_args()

    pdir = Path(args.project)
    ir = json.loads((pdir / "film.json").read_text(encoding="utf-8"))
    video = Path(args.video) if Path(args.video).is_absolute() else pdir / args.video
    if not video.is_file():
        print(f"找不到成片: {video}", file=sys.stderr)
        return 1

    info = probe(video)
    frames = gray_frames(video, args.fps, args.width, info["width"], info["height"])
    segs, _ = static_segments(frames, args.fps, args.static_threshold)
    hold_total = sum(s["dur"] for s in segs)

    shots = sorted(ir.get("shots", []), key=lambda s: s["t"][0])
    per_shot, mislabeled = [], []
    for s in shots:
        t0, t1 = s["t"]
        hold = sum(overlap(t0, t1, g["t0"], g["t1"]) for g in segs)
        dur = t1 - t0
        entry = {"id": s["id"], "duration_s": round(dur, 2),
                 "static_hold_s": round(hold, 2),
                 "static_hold_ratio": round(hold / dur, 3) if dur else 0,
                 "measured_static": bool(dur and hold / dur > SHOT_STATIC_RATIO)}
        per_shot.append(entry)
        if entry["measured_static"] and not s.get("static_class", False):
            mislabeled.append(s["id"])

    compose_html = pdir / "compose" / "index.html"
    compose = {"video_elements": None, "clip_elements": None}
    if compose_html.is_file():
        html = compose_html.read_text(encoding="utf-8", errors="replace")
        compose = {"video_elements": len(re.findall(r"<video\b", html)),
                   "clip_elements": len(re.findall(r'class="[^"]*\bclip\b', html))}

    total_declared = {}
    audio_dur = ((ir.get("audio") or {}).get("timeline") or {}).get("duration_s")
    for s in shots:
        prov = (s.get("source") or {}).get("provider", "?")
        total_declared[prov] = total_declared.get(prov, 0) + (s["t"][1] - s["t"][0])
    share_base = audio_dur or info["duration_s"]
    providers_share = {k: round(v / share_base, 3) for k, v in total_declared.items()}

    metrics = {
        "schema": "render-metrics@1",
        "generated_at": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "video": {"file": str(video),
                  "sha256": hashlib.sha256(video.read_bytes()).hexdigest(),
                  "duration_s": round(info["duration_s"], 3),
                  "width": info["width"], "height": info["height"],
                  "fps": info["fps"], "bit_rate": info["bit_rate"]},
        "loudness_i_lufs": loudness_i(video),
        "settings": {"sample_fps": args.fps, "width": args.width,
                     "static_threshold": args.static_threshold,
                     "min_hold_s": MIN_HOLD_S, "blur": "boxblur=2:1"},
        "static": {"segments": segs,
                   "hold_total_s": round(hold_total, 2),
                   "hold_ratio": round(hold_total / info["duration_s"], 3),
                   "per_shot": per_shot,
                   "mislabeled": mislabeled},
        "compose": compose,
        "providers_declared_share": providers_share,
        "ir": {"audio_duration_s": audio_dur,
               "duration_delta_s": round(info["duration_s"] - audio_dur, 2)
               if audio_dur else None},
    }
    out = Path(args.out) if args.out else pdir / "evidence" / "render-metrics.json"
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(metrics, ensure_ascii=False, indent=2), encoding="utf-8")
    print(json.dumps({"ok": True, "out": str(out),
                      "hold_ratio": metrics["static"]["hold_ratio"],
                      "video_elements": compose["video_elements"],
                      "mislabeled": len(mislabeled)}, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    sys.exit(main())
