#!/usr/bin/env python3
"""G2 评委证据包生成器（P1-6，2026-07-21 升级计划）。

评委物理隔离的物质基础：只给"作品本身的证据"，不给创作过程上下文——
manifest 只含镜头 id/t/intent/framing/provider，不含 ledger 决策理由、不含 script 全文，
防评委被创作者的自我辩护说服（docs/film-ir-context-architecture.md §2.2）。

用法：
  python3 tools/judge/build_evidence_pack.py <project_dir> [--golden <golden项目dir>]
      [--out <输出dir，缺省 <project_dir>/evidence/judge-pack/>] [--video out/final.mp4]
"""

from __future__ import annotations

import argparse
import json
import math
import os
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path

FFMPEG = os.environ.get("FFMPEG", "ffmpeg")      # 走 PATH，可用环境变量覆盖（去本机硬编码）
FFPROBE = os.environ.get("FFPROBE", "ffprobe")
SHEET_INTERVAL_S = 2.0   # contact sheet 抽帧间隔
SHEET_COLS = 8
FRAME_W = 320            # tile 内单帧宽


def probe(video: Path) -> dict:
    out = subprocess.run(
        [FFPROBE, "-v", "error", "-print_format", "json",
         "-show_format", "-show_streams", str(video)],
        capture_output=True, text=True, check=True).stdout
    d = json.loads(out)
    v = next(s for s in d["streams"] if s["codec_type"] == "video")
    return {"duration_s": float(d["format"]["duration"]),
            "width": v["width"], "height": v["height"],
            "fps": eval(v["avg_frame_rate"]) if v.get("avg_frame_rate", "0/0") != "0/0" else None,
            "bit_rate": int(d["format"].get("bit_rate", 0))}


def contact_sheet(video: Path, out_png: Path, duration_s: float, offset_s: float = 0.0):
    """每 SHEET_INTERVAL_S 一帧 tile。offset_s>0 = 半步错位版（playbook §9.7 两轮抽帧）。
    本机 ffmpeg 无 drawtext（未编 freetype），时间码不烧帧上——
    用确定性格位映射代替：行优先，第 n 格（从 1 数）时间 = offset + (n-1)*间隔，
    映射写进 manifest.grid_time_map，评委 prompt 负责教会换算。"""
    n = max(1, math.floor((duration_s - offset_s) / SHEET_INTERVAL_S) + 1)
    rows = math.ceil(n / SHEET_COLS)
    vf = f"fps=1/{SHEET_INTERVAL_S},scale={FRAME_W}:-2,tile={SHEET_COLS}x{rows}"
    subprocess.run(
        [FFMPEG, "-y", "-loglevel", "error", "-ss", str(offset_s), "-i", str(video),
         "-vf", vf, "-frames:v", "1", "-q:v", "5", str(out_png)], check=True)


def shot_frames(video: Path, shots: list[dict], out_dir: Path) -> list[str]:
    out_dir.mkdir(parents=True, exist_ok=True)
    files = []
    for s in shots:
        mid = (s["t"][0] + s["t"][1]) / 2
        f = out_dir / f"{s['id']}_{mid:07.2f}s.jpg"
        subprocess.run(
            [FFMPEG, "-y", "-loglevel", "error", "-ss", str(mid), "-i", str(video),
             "-frames:v", "1", "-vf", "scale=640:-2", "-q:v", "4", str(f)], check=True)
        files.append(f.name)
    return files


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("project")
    ap.add_argument("--golden", help="Golden 样片项目目录（并排对照的关键输入）")
    ap.add_argument("--out")
    ap.add_argument("--video", default="out/final.mp4")
    args = ap.parse_args()

    pdir = Path(args.project)
    ir = json.loads((pdir / "film.json").read_text(encoding="utf-8"))
    video = (pdir / args.video) if not Path(args.video).is_absolute() else Path(args.video)
    if not video.is_file():
        print(f"找不到成片: {video}", file=sys.stderr)
        return 1
    out = Path(args.out) if args.out else pdir / "evidence" / "judge-pack"
    out.mkdir(parents=True, exist_ok=True)

    info = probe(video)
    contact_sheet(video, out / "contact-sheet.jpg", info["duration_s"], 0.0)
    contact_sheet(video, out / "contact-sheet-offset.jpg", info["duration_s"],
                  SHEET_INTERVAL_S / 2)

    shots = sorted(ir.get("shots", []), key=lambda s: s["t"][0])
    frame_files = shot_frames(video, shots, out / "frames")

    # 音轨抽出（audio node 给隔离 subagent 真听用；无音轨则该文件不生成，audio node 会如实缺证据）
    subprocess.run([FFMPEG, "-y", "-loglevel", "error", "-i", str(video), "-vn",
                    "-b:a", "96k", str(out / "audio.mp3")], check=False)

    golden_note = None
    if args.golden:
        gdir = Path(args.golden)
        gvideo = gdir / "out" / "final.mp4"
        if gvideo.is_file():
            ginfo = probe(gvideo)
            contact_sheet(gvideo, out / "golden-contact-sheet.jpg", ginfo["duration_s"])
            golden_note = gdir.name
        else:
            print(f"警告: Golden 成片不存在，跳过并排: {gvideo}", file=sys.stderr)

    # L0 报告：ffprobe + 已有的成片实测指标（若在）
    l0 = {"probe": info}
    rm = pdir / "evidence" / "render-metrics.json"
    if rm.is_file():
        l0["render_metrics"] = json.loads(rm.read_text(encoding="utf-8"))
    (out / "l0-report.json").write_text(
        json.dumps(l0, ensure_ascii=False, indent=2), encoding="utf-8")

    # 隔离 manifest：作品事实，零创作理由
    manifest = {
        "schema": "judge-pack@1",
        "generated_at": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "title": ir["meta"].get("title"),
        "style_pack": ir["meta"].get("style_pack"),
        "aspect": ir["meta"].get("aspect"),
        "duration_s": info["duration_s"],
        "video_file": str(video.resolve()),   # Gemini 原生视频评审用（不抽帧）
        "grid_time_map": {"cols": SHEET_COLS, "interval_s": SHEET_INTERVAL_S,
                          "offset_sheet_offset_s": SHEET_INTERVAL_S / 2,
                          "rule": "行优先；第 n 格(从1数)时间 = 偏移 + (n-1)*interval_s"},
        "golden": golden_note,
        "contract_amendments": ir["meta"].get("contract_amendments") or {},
        "shots": [{"id": s["id"], "t": s["t"], "intent": s.get("intent"),
                   "framing": s.get("framing"),
                   "provider": s.get("source", {}).get("provider")}
                  for s in shots],
        "frames": frame_files,
        "sections": [{"id": s.get("id"), "t": s.get("t"), "text": s.get("text", "")}
                     for s in (ir.get("audio", {}).get("timeline", {}).get("sections") or [])],
    }
    (out / "manifest.json").write_text(
        json.dumps(manifest, ensure_ascii=False, indent=2), encoding="utf-8")
    print(json.dumps({"ok": True, "pack": str(out), "shots": len(shots),
                      "frames": len(frame_files), "golden": golden_note},
                     ensure_ascii=False))
    return 0


if __name__ == "__main__":
    sys.exit(main())
