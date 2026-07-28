#!/usr/bin/env python3
"""像素归一：把 GPT-Image-2 静帧 / Seedance clip 压到真实像素栅格 + 主调色板。

这是 `pixel` profile 的技术脊柱（由 `pipeline_extras.post_still` / `post_video` 声明）。
扩散模型给不出真像素——它给的是「像素味的软图」：
栅格漂移、抗锯齿边、上万种颜色。归一层把它按物理办法钉回去：

  面积降采样到逻辑分辨率 → 对主调色板量化 → 最近邻整数倍放大

三步都是确定性的。归一之后，「一个逻辑像素 = 输出图上一个 N×N 纯色方块」
和「全片只用主调色板里的颜色」都是可被 verify.py 验证的事实，不是形容词。

抖动默认关：ordered dither 的网点纹理会被读成半调/纸颗粒——那正是 `pixel` 要和
`collage` 划清界限的东西。

用法:
  pixelize.py still  --in a.png --out b.png --palette p.png --size 1280x720 --grid 4
  pixelize.py video  --in a.mp4 --out b.mp4 --palette p.png --size 1280x720 --grid 4 [--step-fps 12]
  pixelize.py frames --in small.png --out big.png --size 1920x1080 --grid 6   # 已量化图纯放大（出首尾帧用）
"""
import argparse
import shlex
import subprocess
import sys
from pathlib import Path

# 抖动：默认关。ordered dither 的网点纹理会被读成半调/纸颗粒——
# 那正是本 skill 要和拼贴风划清界限的东西。渐变实在压不住时才开 bayer。
DITHERS = ("none", "bayer:bayer_scale=2", "bayer:bayer_scale=3",
           "bayer:bayer_scale=4", "bayer:bayer_scale=5")


def parse_size(s):
    try:
        w, h = (int(x) for x in s.lower().split("x"))
    except ValueError:
        sys.exit(f"--size 要写成 宽x高，收到 {s!r}")
    return w, h


def logical(size, grid):
    w, h = size
    if w % grid or h % grid:
        sys.exit(f"{w}x{h} 不是 grid={grid} 的整数倍——非整数倍放大会把栅格糊掉。"
                 f"改 grid 或改 size（16:9 常用 1280x720/grid4、1920x1080/grid6）")
    return w // grid, h // grid


def run(cmd):
    print("$", " ".join(shlex.quote(c) for c in cmd))
    r = subprocess.run(cmd, capture_output=True, text=True)
    if r.returncode:
        sys.exit(r.stderr[-2000:] or f"ffmpeg 退出码 {r.returncode}")


def main():
    p = argparse.ArgumentParser()
    p.add_argument("mode", choices=("still", "video", "frames"))
    p.add_argument("--in", dest="src", type=Path, required=True)
    p.add_argument("--out", dest="dst", type=Path, required=True)
    p.add_argument("--palette", type=Path, help="主调色板 PNG（still/video 必填）")
    p.add_argument("--size", required=True, help="输出尺寸，如 1280x720")
    p.add_argument("--grid", type=int, default=4, help="一个逻辑像素占几个输出像素（默认 4）")
    p.add_argument("--dither", default="none", choices=DITHERS)
    p.add_argument("--step-fps", type=float, default=12.0,
                   help="video: 逐帧动画拍数（默认 12fps 即 24fps 下的 on 2s）；0=不抽帧")
    p.add_argument("--out-fps", type=float, default=24.0, help="video: 容器帧率")
    p.add_argument("--crf", type=int, default=0,
                   help="video: x264 crf，默认 0(无损)。有损压缩会在方块边缘长出振铃，"
                        "把 32 色打回上千色——中间产物别省这点体积")
    a = p.parse_args()

    if not a.src.exists():
        sys.exit(f"输入不存在: {a.src}")
    size = parse_size(a.size)
    lw, lh = logical(size, a.grid)
    a.dst.parent.mkdir(parents=True, exist_ok=True)

    if a.mode == "frames":
        # 已经量化过的小图（或同调色板的图）纯最近邻放大，不重新量化、不再抖动。
        run(["ffmpeg", "-y", "-i", str(a.src), "-vf",
             f"format=rgb24,scale={size[0]}:{size[1]}:flags=neighbor",
             "-pix_fmt", "rgb24", "-update", "1", str(a.dst)])
    elif a.mode == "still":
        if not a.palette:
            sys.exit("still 模式必须 --palette")
        run(["ffmpeg", "-y", "-i", str(a.src), "-i", str(a.palette), "-lavfi",
             f"[0:v]scale={lw}:{lh}:flags=area,format=rgb24[s];"
             f"[s][1:v]paletteuse=dither={a.dither}[q];"
             f"[q]format=rgb24,scale={size[0]}:{size[1]}:flags=neighbor",
             "-pix_fmt", "rgb24", "-update", "1", str(a.dst)])
    else:
        if not a.palette:
            sys.exit("video 模式必须 --palette")
        pre = f"fps={a.step_fps}," if a.step_fps else ""
        run(["ffmpeg", "-y", "-i", str(a.src), "-i", str(a.palette), "-filter_complex",
             f"[0:v]{pre}scale={lw}:{lh}:flags=area,format=rgb24[s];"
             f"[s][1:v]paletteuse=dither={a.dither}[q];"
             f"[q]format=rgb24,scale={size[0]}:{size[1]}:flags=neighbor,fps={a.out_fps}",
             # -g 12 / -sc_threshold 0：挂进 HyperFrames <video> 后 seek 不冻帧（seedance.md）
             "-c:v", "libx264", "-preset", "slow", "-crf", str(a.crf),
             "-pix_fmt", "yuv420p", "-g", "12", "-keyint_min", "12",
             "-sc_threshold", "0", "-an", str(a.dst)])

    print(f"→ {a.dst}（逻辑 {lw}x{lh} · grid {a.grid} · 输出 {size[0]}x{size[1]}）")


if __name__ == "__main__":
    main()
