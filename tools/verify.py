#!/usr/bin/env python3
"""`pixel` profile 专属码判：栅格 + 锁色。通用项（规格 / 死尾 / contact sheet）转给 tools/clip-qa.py。

由 `profiles/pixel.json` 的 `pipeline_extras.extra_checks` 声明调用——引擎照单执行，不认脚本名。

  ① 栅格 —— 每个 grid×grid 方块是否纯色（扩散模型的软像素 / 有损压缩的振铃都在这里现形）
  ② 锁色 —— 出现的颜色是否贴合主调色板（做旧色、模型自己长出来的脏色都在这里现形）

用法:
  verify.py clip.mp4  --palette p.png --grid 4 [--json out.json] [--contact sheet.jpg]
  verify.py still.png --palette p.png --grid 4
"""
import argparse
import importlib.util
import json
import subprocess
import sys
from pathlib import Path

from PIL import Image

SAMPLE_FRAMES = 6          # 抽帧数（全帧逐块扫太慢，均匀抽样足够定位问题）
GRID_FAIL_RATIO = 0.002    # 非纯色方块占比上限
# 锁色容差（每通道）：PNG 是 RGB 精确存储，容差 0。
# 视频哪怕 x264 无损也只是 YUV 空间无损——RGB→YUV420p→RGB 的取整会让通道漂 ±1~2。
# 这是编码的物理事实，不是调色板破了，所以按「贴合最近调色板项的距离」判，不按等值判。
STILL_TOL, VIDEO_TOL = 0, 3
VIDEO_EXT = (".mp4", ".mov", ".webm", ".mkv")


def load_clip_qa():
    """从仓库根加载 tools/clip-qa.py（文件名带连字符，不能直接 import）。"""
    here = Path(__file__).resolve()
    for d in here.parents:
        cand = d / "tools" / "clip-qa.py"
        if cand.exists():
            spec = importlib.util.spec_from_file_location("clip_qa", cand)
            mod = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(mod)
            return mod
    sys.exit("找不到 tools/clip-qa.py")


def palette_colors(path):
    return {c for _, c in Image.open(path).convert("RGB").getcolors(maxcolors=1 << 20)}


def snap_distance(color, allowed):
    """到最近调色板项的 Chebyshev 距离。"""
    return min(max(abs(a - b) for a, b in zip(color, ref)) for ref in allowed)


def check_image(im, grid, allowed, tol):
    """返回 (非纯色方块数, 总方块数, 超容差色列表, 最大贴合距离)"""
    im = im.convert("RGB")
    w, h = im.size
    px = im.load()
    bad = 0
    for by in range(0, h - h % grid, grid):
        for bx in range(0, w - w % grid, grid):
            c = px[bx, by]
            if any(px[bx + dx, by + dy] != c
                   for dy in range(grid) for dx in range(grid)):
                bad += 1
    used = {c for _, c in im.getcolors(maxcolors=1 << 20)}
    dists = {c: snap_distance(c, allowed) for c in used}
    stray = sorted(c for c, d in dists.items() if d > tol)
    return bad, (w // grid) * (h // grid), stray, max(dists.values(), default=0)


def main():
    p = argparse.ArgumentParser()
    p.add_argument("target", type=Path)
    p.add_argument("--palette", type=Path, required=True)
    p.add_argument("--grid", type=int, default=4)
    p.add_argument("--json", type=Path)
    p.add_argument("--contact", type=Path, help="video: 顺带出 contact sheet")
    a = p.parse_args()

    allowed = palette_colors(a.palette)
    is_video = a.target.suffix.lower() in VIDEO_EXT
    tol = VIDEO_TOL if is_video else STILL_TOL
    out = {"target": str(a.target), "grid": a.grid, "palette_size": len(allowed),
           "palette_tolerance": tol, "checks": {}, "verdict": "pass"}

    def mark(key, passed, detail, **extra):
        out["checks"][key] = {"pass": passed, "detail": detail, **extra}
        if not passed:
            out["verdict"] = "fail"

    if is_video:
        # 通用项先跑：规格 / 死尾 / contact sheet 由 tools/clip-qa.py 唯一实现
        generic, _ = load_clip_qa().run(a.target, contact=a.contact)
        out["spec"] = generic["spec"]
        out["checks"].update(generic["checks"])
        if generic["verdict"] == "fail":
            out["verdict"] = "fail"
        if "contact_sheet" in generic:
            out["contact_sheet"] = generic["contact_sheet"]

        w, h = generic["spec"]["width"], generic["spec"]["height"]
        if w % a.grid or h % a.grid:
            mark("grid_size", False, f"{w}x{h} 不是 grid={a.grid} 的整数倍")

        tmp = a.target.parent / f".{a.target.stem}_vfy_%02d.png"
        step = max(generic["spec"]["duration_s"] / (SAMPLE_FRAMES + 1), 0.1)
        subprocess.run(["ffmpeg", "-y", "-v", "error", "-i", str(a.target),
                        "-vf", f"fps=1/{step:.4f}", "-frames:v", str(SAMPLE_FRAMES),
                        str(tmp)], check=True)
        frames = sorted(a.target.parent.glob(f".{a.target.stem}_vfy_*.png"))
        worst_ratio, all_stray, worst_d = 0.0, set(), 0
        for f in frames:
            bad, total, stray, d = check_image(Image.open(f), a.grid, allowed, tol)
            worst_ratio = max(worst_ratio, bad / total if total else 1.0)
            worst_d = max(worst_d, d)
            all_stray |= set(stray)
            f.unlink()
        mark("grid", worst_ratio <= GRID_FAIL_RATIO,
             f"抽 {len(frames)} 帧，最差非纯色方块占比 {worst_ratio:.4%}",
             worst_ratio=round(worst_ratio, 6))
        stray_list, worst = sorted(all_stray), worst_d
    else:
        bad, total, stray_list, worst = check_image(
            Image.open(a.target), a.grid, allowed, tol)
        ratio = bad / total if total else 1.0
        mark("grid", ratio <= GRID_FAIL_RATIO,
             f"非纯色方块 {bad}/{total}（{ratio:.4%}）", ratio=round(ratio, 6))

    mark("palette", not stray_list,
         f"超容差({tol})色 {len(stray_list)} 种，最大贴合距离 {worst}"
         + (f"，例 {stray_list[:5]}" if stray_list else ""),
         stray_count=len(stray_list), worst_snap_distance=worst)

    print(json.dumps(out, ensure_ascii=False, indent=2))
    if a.json:
        a.json.parent.mkdir(parents=True, exist_ok=True)
        a.json.write_text(json.dumps(out, ensure_ascii=False, indent=2))
    return 0 if out["verdict"] == "pass" else 1


if __name__ == "__main__":
    sys.exit(main())
