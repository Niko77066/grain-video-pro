#!/usr/bin/env python3
"""成片实测层（P0-1，2026-07-21 升级计划）：从终渲 mp4 反向核验，不信任何自报字段。

由来：五片对照实验——Codex 把 13 个幻灯片镜头全标 static_class:false 绕过了
全部 IR 门（实际 75% 静态持有）。本脚本产出 evidence/render-metrics.json，
是 style.contract.render 门的唯一证据源；自报与实测矛盾时以实测为准。

测量口径：
- 静态持有 = 相邻采样帧（降采样灰度 + boxblur 压掉胶片颗粒）平均绝对差低于阈值，
  连续时长 ≥0.8s 的段；hold_ratio = 静态持有总时长 / 全片时长。
- 阈值默认值来自 2026-07-21 四片标定（Claude 打磨双片 vs Codex 翻车双片，见 --help 尾注）。
- 跨镜头主色漂移 = 逐镜 HSV 粗桶直方图两两全变差距离；drift_i = 第 i 镜到其余各镜
  的平均距离，max_drift 是全片最离群那一镜的 drift。这是"缝合层成立了没有"的
  第一个机器指标——此前只有 inviolable 自然语言 + G2 目检。

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

# ── 主色直方图分桶（粗桶即可：目的是比较镜头间的"世界"，不是取色）
HUE_BINS = 12             # 30° 一桶
SAT_BINS = 2              # 淡彩 / 浓彩，界 SAT_SPLIT
VAL_BINS = 2              # 暗 / 亮，界 VAL_SPLIT
NEUTRAL_BINS = 4          # 低饱和像素的色相无意义，单独按明度分桶
SAT_MIN = 0.15            # 低于此判无彩色，落 neutral 桶
SAT_SPLIT, VAL_SPLIT = 0.45, 0.5
CHROMA_BINS = HUE_BINS * SAT_BINS * VAL_BINS
PALETTE_BINS = CHROMA_BINS + NEUTRAL_BINS
# 色相是圆的，轻微调色会把像素整体挪一格——比较前沿色相轴做 3 抽头环形平滑，
# 让"同一世界里的小幅漂移"不被量化边界放大成大距离。
HUE_SMOOTH = (0.25, 0.5, 0.25)
OUTLIER_MAD_K = 3.0       # drift > median + max(K*MAD, FLOOR) 记为离群镜
OUTLIER_FLOOR = 0.06      # MAD 下限：视觉高度统一的片子不该因噪声被点名


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


# ------------------------------------------------------------ 跨镜头主色漂移

def color_frames(video: Path, sample_fps: float, width: int, src_w: int, src_h: int):
    """降采样彩色帧流（gray_frames 的同一抽帧路径，只是不丢色）。

    不做 boxblur：静态门要压颗粒才不会逐帧差永不为零，主色门只关心整片颜色分布，
    scale 本身已经在做面积平均。也不改灰度路径的采样参数——0.0015 阈值是标定过的。
    """
    h = max(2, round(src_h * width / src_w / 2) * 2)
    p = subprocess.run(
        [FFMPEG, "-loglevel", "error", "-i", str(video),
         "-vf", f"fps={sample_fps},scale={width}:{h},format=rgb24",
         "-f", "rawvideo", "-"],
        capture_output=True, check=True)
    buf = np.frombuffer(p.stdout, dtype=np.uint8)
    n = len(buf) // (width * h * 3)
    return buf[: n * width * h * 3].reshape(n, h, width, 3)


def rgb_to_hsv(rgb: np.ndarray):
    """(...,3) uint8 → (h, s, v) 三个 0..1 的 float32 数组。h 为色相角/360。"""
    x = rgb.astype(np.float32) / 255.0
    r, g, b = x[..., 0], x[..., 1], x[..., 2]
    mx, mn = x.max(-1), x.min(-1)
    d = mx - mn
    v = mx
    s = np.where(mx > 1e-6, d / np.maximum(mx, 1e-6), 0.0)
    h = np.zeros_like(mx)
    nz = d > 1e-6
    i = nz & (mx == r)      # 三分支的扇区偏移不同，按 max 通道归属依次填
    h[i] = ((g - b)[i] / d[i]) % 6.0
    i = nz & (mx == g) & ~(mx == r)
    h[i] = (b - r)[i] / d[i] + 2.0
    i = nz & (mx == b) & ~(mx == r) & ~(mx == g)
    h[i] = (r - g)[i] / d[i] + 4.0
    return h / 6.0, s, v


def palette_hist(h: np.ndarray, s: np.ndarray, v: np.ndarray) -> np.ndarray:
    """一批帧的 HSV → 归一化的 PALETTE_BINS 桶主色直方图。"""
    hb = np.minimum((h * HUE_BINS).astype(np.int32), HUE_BINS - 1)
    sb = (s >= SAT_SPLIT).astype(np.int32)
    vb = (v >= VAL_SPLIT).astype(np.int32)
    idx = (hb * SAT_BINS + sb) * VAL_BINS + vb
    neutral = s < SAT_MIN
    nvb = np.minimum((v * NEUTRAL_BINS).astype(np.int32), NEUTRAL_BINS - 1)
    idx = np.where(neutral, CHROMA_BINS + nvb, idx)
    counts = np.bincount(idx.ravel(), minlength=PALETTE_BINS).astype(np.float64)
    total = counts.sum()
    return counts / total if total else counts


def smooth_hue(hist: np.ndarray) -> np.ndarray:
    """沿色相轴环形平滑有彩色部分；neutral 桶原样保留（明度不是圆的）。"""
    grid = hist[:CHROMA_BINS].reshape(HUE_BINS, SAT_BINS * VAL_BINS)
    a, b, c = HUE_SMOOTH
    out = (a * np.roll(grid, 1, axis=0) + b * grid + c * np.roll(grid, -1, axis=0))
    return np.concatenate([out.ravel(), hist[CHROMA_BINS:]])


def hist_distance(p: np.ndarray, q: np.ndarray) -> float:
    """全变差距离 ∈[0,1]：需要在桶间搬运的像素占比。0=同分布，1=毫无交集。"""
    return float(0.5 * np.abs(p - q).sum())


def dominant(hist: np.ndarray, s_mean: float, v_mean: float) -> dict:
    """直方图 → 人读得懂的主色描述（用未平滑的原始桶，平滑只服务距离）。"""
    top = int(np.argmax(hist))
    out = {"share": round(float(hist[top]), 3),
           "neutral_share": round(float(hist[CHROMA_BINS:].sum()), 3),
           "mean_sat": round(s_mean, 3), "mean_val": round(v_mean, 3)}
    if top >= CHROMA_BINS:
        nvb = top - CHROMA_BINS
        out |= {"hue_deg": None,
                "band": f"neutral/v{nvb}",
                "value_center": round((nvb + 0.5) / NEUTRAL_BINS, 3)}
    else:
        vb = top % VAL_BINS
        sb = (top // VAL_BINS) % SAT_BINS
        hb = top // (SAT_BINS * VAL_BINS)
        out |= {"hue_deg": round((hb + 0.5) * 360.0 / HUE_BINS, 1),
                "band": f"{'vivid' if sb else 'muted'}/{'light' if vb else 'dark'}"}
    return out


def palette_metrics(video: Path, shots: list, sample_fps: float, width: int,
                    src_w: int, src_h: int) -> dict:
    """逐镜主色直方图 + 两两距离矩阵 + 全片漂移统计。

    drift_i = 第 i 镜到其余各镜的平均距离——"这一镜和全片其余部分是不是同一个
    世界"。max_drift 是全片最离群那一镜的 drift，即 render.palette_drift_max 门读的值。
    """
    frames = color_frames(video, sample_fps, width, src_w, src_h)
    if len(frames) == 0 or len(shots) < 2:
        return {"measurable": False,
                "reason": "帧流为空" if len(frames) == 0 else "镜头数 <2，跨镜头指标无定义"}

    centers = (np.arange(len(frames)) + 0.5) / sample_fps
    ids, hists, doms = [], [], []
    for s in shots:
        t0, t1 = s["t"]
        sel = np.flatnonzero((centers >= t0) & (centers < t1))
        if sel.size == 0:                              # 短于一个采样间隔的镜头取最近帧
            sel = np.array([int(np.clip(round((t0 + t1) / 2 * sample_fps - 0.5),
                                        0, len(frames) - 1))])
        hh, ss, vv = rgb_to_hsv(frames[sel])
        ids.append(s["id"])
        hists.append(palette_hist(hh, ss, vv))
        doms.append(dominant(hists[-1], float(ss.mean()), float(vv.mean()))
                    | {"id": s["id"], "frames": int(sel.size)})

    sm_hists = [smooth_hue(h) for h in hists]
    n = len(ids)
    matrix = [[0.0] * n for _ in range(n)]
    pairs = []
    for i in range(n):
        for j in range(i + 1, n):
            d = round(hist_distance(sm_hists[i], sm_hists[j]), 4)
            matrix[i][j] = matrix[j][i] = d
            pairs.append(d)

    drift = [round(sum(matrix[i]) / (n - 1), 4) for i in range(n)]
    med = float(np.median(drift))
    mad = float(np.median(np.abs(np.array(drift) - med)))
    cut = med + max(OUTLIER_MAD_K * mad, OUTLIER_FLOOR)
    order = sorted(range(n), key=lambda i: drift[i], reverse=True)

    return {
        "measurable": True,
        "shot_ids": ids,
        "max_drift": max(drift),
        "max_drift_shot": ids[int(np.argmax(drift))],
        "mean_pairwise_distance": round(float(np.mean(pairs)), 4),
        "pairwise_distance_var": round(float(np.var(pairs)), 5),
        "drift_median": round(med, 4),
        "outlier_cut": round(cut, 4),
        "outlier_shots": [{"id": ids[i], "drift": drift[i]}
                          for i in order if drift[i] > cut],
        "shot_drift": [{"id": ids[i], "drift": drift[i]} for i in order],
        "per_shot_dominant": doms,
        "pairwise_distance_matrix": matrix,
    }


def main() -> int:
    ap = argparse.ArgumentParser(
        description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="静态阈值标定（2026-07-21 四片）：0.0015 @ fps=4/width=160/boxblur=2:1——"
               "Codex hf 翻车片测 0.747（与其自报 75% 吻合）/ Claude hf 打磨片 0.619 / "
               "Claude 空调 0.303 / Codex ac-26c 0.422。改采样参数须重标。\n"
               "主色漂移标定（2026-07-27，同采样参数）：浣熊片（delivered）max_drift "
               "0.691 / 中国经济片 0.449（v2 加框版 0.539）。负对照——把另一部片未调色的"
               "镜头切进浣熊时间轴，肇事镜 0.691→0.974、其余 24 镜变动 <0.05。"
               "据此 pixel-chronicle 合同定 0.80（带宽 [0.72,0.88]）。")
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

    palette = palette_metrics(video, shots, args.fps, args.width,
                              info["width"], info["height"])

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
                     "min_hold_s": MIN_HOLD_S, "blur": "boxblur=2:1",
                     "palette_bins": f"hue{HUE_BINS}×sat{SAT_BINS}×val{VAL_BINS}"
                                     f"+neutral{NEUTRAL_BINS}",
                     "palette_sat_min": SAT_MIN,
                     "palette_distance": "total_variation, hue-smoothed",
                     "palette_outlier_rule":
                         f"drift > median + max({OUTLIER_MAD_K:g}*MAD, {OUTLIER_FLOOR})"},
        "static": {"segments": segs,
                   "hold_total_s": round(hold_total, 2),
                   "hold_ratio": round(hold_total / info["duration_s"], 3),
                   "per_shot": per_shot,
                   "mislabeled": mislabeled},
        "palette": palette,
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
                      "palette_max_drift": palette.get("max_drift"),
                      "palette_outliers": len(palette.get("outlier_shots") or []),
                      "video_elements": compose["video_elements"],
                      "mislabeled": len(mislabeled)}, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    sys.exit(main())
