#!/usr/bin/env python3
"""批次级总览三张图。八套生成型材质语言通用——**多条一起做时必出**。

为什么要批次级：逐条 QA 只看得见「这一条成不成立」，看不见批次级问题——
一批里三条都从半满的场起手、五条的尾帧全都和确认静帧差一截、
两条的组装节奏明显比其他条快一截。这三张图是专治这类问题的：

  ① omni-contact-sheet-all   每条逐秒抽帧，一条一行 → 看**组装进程**是否铺满
  ② video-first-frame-all    每条的**实际首帧** → 验真的从该 profile 的首帧规则起手
  ③ end-frame-comparison-all 确认静帧 ‖ 视频末帧，一条一行 → 看尾帧是否兑现锚点

原来这三条只写在 collage 链的 SKILL.md 里（且只是一行 ffmpeg 片段）。
它跟材质无关，是「一批 clip 交付得好不好」的通用问题，因此升进引擎，只留一份实现。

用法:
  clip-batch-sheets.py --out-dir evidence/ --clips a.mp4 b.mp4 [--stills a.png b.png]
                       [--names s01 s02] [--width 180]
  # 只给 clips 出 ①②；同时给 stills 才出 ③（两者按顺序一一对应）
退出码 0=三张（或可出的那几张）都生成成功。
"""
import argparse
import json
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

FALLBACK_WIDTH = 180       # 竖屏缩略宽；横屏自动用 2 倍
SECONDS_PER_ROW_CAP = 10   # 一行最多抽这么多帧，防长片把图拉爆


def probe(path):
    r = subprocess.run(
        ["ffprobe", "-v", "error", "-select_streams", "v:0",
         "-show_entries", "stream=width,height", "-show_entries", "format=duration",
         "-of", "json", str(path)], capture_output=True, text=True)
    if r.returncode:
        sys.exit(f"ffprobe 失败：{path}\n{r.stderr[-500:]}")
    d = json.loads(r.stdout)
    s = d["streams"][0]
    return s["width"], s["height"], float(d["format"]["duration"])


def ff(args):
    r = subprocess.run(["ffmpeg", "-y", "-v", "error", *map(str, args)],
                       capture_output=True, text=True)
    if r.returncode:
        sys.exit(f"ffmpeg 失败：\n$ ffmpeg {' '.join(map(str, args))}\n{r.stderr[-800:]}")


def thumb_size(w, h, width):
    tw = width if h >= w else width * 2
    return tw, round(tw * h / w / 2) * 2


def row_contact(clip, dst, width):
    """一条 clip 逐秒抽帧拼成一行。"""
    w, h, dur = probe(clip)
    tw, th = thumb_size(w, h, width)
    n = max(2, min(SECONDS_PER_ROW_CAP, int(round(dur))))
    ff(["-i", clip, "-vf", f"fps={n}/{dur:.3f},scale={tw}:{th},tile={n}x1",
        "-frames:v", "1", dst])


def first_frame(clip, dst, width):
    w, h, _ = probe(clip)
    tw, th = thumb_size(w, h, width)
    ff(["-i", clip, "-vf", f"scale={tw}:{th}", "-frames:v", "1", dst])


def last_frame(clip, dst, width):
    w, h, dur = probe(clip)
    tw, th = thumb_size(w, h, width)
    ff(["-sseof", "-0.2", "-i", clip, "-vf", f"scale={tw}:{th}",
        "-frames:v", "1", "-update", "1", dst])


def still_thumb(still, ref_clip, dst, width):
    w, h, _ = probe(ref_clip)
    tw, th = thumb_size(w, h, width)
    ff(["-i", still, "-vf", f"scale={tw}:{th}:force_original_aspect_ratio=increase,"
        f"crop={tw}:{th}", "-frames:v", "1", "-update", "1", dst])


def stack(paths, dst, direction):
    """direction: v 竖排（一条一行）/ h 横排（并排）。"""
    if len(paths) == 1:
        shutil.copyfile(paths[0], dst)
        return
    args = []
    for p in paths:
        args += ["-i", str(p)]
    ff([*args, "-filter_complex",
        f"{''.join(f'[{i}:v]' for i in range(len(paths)))}"
        f"{'vstack' if direction == 'v' else 'hstack'}=inputs={len(paths)}",
        "-frames:v", "1", "-update", "1", dst])


def main():
    p = argparse.ArgumentParser()
    p.add_argument("--clips", nargs="+", required=True, type=Path)
    p.add_argument("--stills", nargs="*", default=[], type=Path,
                   help="逐条确认过的锚点静帧，顺序与 --clips 一一对应；给了才出 ③")
    p.add_argument("--names", nargs="*", default=[], help="仅用于报告里指名，不影响出图")
    p.add_argument("--out-dir", required=True, type=Path)
    p.add_argument("--width", type=int, default=FALLBACK_WIDTH)
    a = p.parse_args()

    for c in a.clips:
        if not c.exists():
            sys.exit(f"clip 不存在：{c}")
    if a.stills and len(a.stills) != len(a.clips):
        sys.exit(f"--stills 有 {len(a.stills)} 个但 --clips 有 {len(a.clips)} 个，"
                 f"必须一一对应（③ 是逐条并排比对）")
    a.out_dir.mkdir(parents=True, exist_ok=True)
    names = a.names or [c.stem for c in a.clips]
    made = {}

    with tempfile.TemporaryDirectory() as td:
        td = Path(td)

        rows = []
        for i, c in enumerate(a.clips):
            r = td / f"row{i:02d}.png"
            row_contact(c, r, a.width)
            rows.append(r)
        dst = a.out_dir / "omni-contact-sheet-all.jpg"
        stack(rows, dst, "v")
        made["omni-contact-sheet-all"] = dst

        firsts = []
        for i, c in enumerate(a.clips):
            f = td / f"first{i:02d}.png"
            first_frame(c, f, a.width)
            firsts.append(f)
        dst = a.out_dir / "video-first-frame-all.jpg"
        stack(firsts, dst, "h")
        made["video-first-frame-all"] = dst

        if a.stills:
            pairs = []
            for i, (c, s) in enumerate(zip(a.clips, a.stills)):
                if not s.exists():
                    sys.exit(f"静帧不存在：{s}")
                sthumb, lthumb = td / f"s{i:02d}.png", td / f"l{i:02d}.png"
                still_thumb(s, c, sthumb, a.width)
                last_frame(c, lthumb, a.width)
                pair = td / f"pair{i:02d}.png"
                stack([sthumb, lthumb], pair, "h")
                pairs.append(pair)
            dst = a.out_dir / "end-frame-comparison-all.jpg"
            stack(pairs, dst, "v")
            made["end-frame-comparison-all"] = dst

    print(f"批次 {len(a.clips)} 条：{'、'.join(names)}")
    for k, v in made.items():
        print(f"  → {v}")
    if "end-frame-comparison-all" not in made:
        print("  ℹ️ 没给 --stills，跳过 ③（尾帧≈确认静帧那一项就没有机器证据，人眼自己比）")
    print("\n人眼看这三张各查什么：")
    print("  ① 组装是否铺满全片（前段做完、后段长 hold = 死尾，与 clip-qa 的判红互为证据）")
    print("  ② 每条是否真的按本 profile 的 first_frame 规则起手（`broll-profile.py plan <id>` 看规则）")
    print("  ③ 尾帧是否兑现确认过的静帧（轻微细节漂移不影响语义即通过，不为此重跑）")
    return 0


if __name__ == "__main__":
    sys.exit(main())
