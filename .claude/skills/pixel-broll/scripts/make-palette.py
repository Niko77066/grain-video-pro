#!/usr/bin/env python3
"""主调色板：把一组 hex 编成 ffmpeg paletteuse 能吃的 16×16 PNG + 人眼看的色卡。

一部片一张主调色板。全片所有像素静帧与所有像素 clip 都对同一张量化，
于是「跨镜头主色漂移」在生成之前就被物理锁死，而不是靠 compose 层调色补救。

用法:
  make-palette.py --hex 1a1c2c,5d275d,...  --out palette/master.png [--swatch palette/swatch.png]
  make-palette.py --json palette/master.json --out palette/master.png
      master.json = {"name": "...", "colors": ["#1a1c2c", ...]}
"""
import argparse
import json
import sys
from pathlib import Path

from PIL import Image

MIN_COLORS, MAX_COLORS = 4, 64


def parse_hex(items):
    out = []
    for raw in items:
        h = raw.strip().lstrip("#")
        if len(h) != 6 or any(c not in "0123456789abcdefABCDEF" for c in h):
            sys.exit(f"不是合法 hex: {raw!r}")
        out.append(tuple(int(h[i:i + 2], 16) for i in (0, 2, 4)))
    return out


def main():
    p = argparse.ArgumentParser()
    p.add_argument("--hex", help="逗号分隔的 hex 列表")
    p.add_argument("--json", type=Path, help="调色板 JSON（字段 colors[]）")
    p.add_argument("--out", type=Path, required=True, help="输出 16x16 palette PNG")
    p.add_argument("--swatch", type=Path, help="另出一张人眼看的色卡 PNG")
    a = p.parse_args()

    if a.json:
        colors = parse_hex(json.loads(a.json.read_text())["colors"])
    elif a.hex:
        colors = parse_hex(a.hex.split(","))
    else:
        sys.exit("要么 --hex 要么 --json")

    if len(set(colors)) != len(colors):
        sys.exit("调色板里有重复色——去重后再来")
    if not MIN_COLORS <= len(colors) <= MAX_COLORS:
        sys.exit(f"色数 {len(colors)} 越界（{MIN_COLORS}–{MAX_COLORS}）。"
                 "太少表达不了层次，太多就不是像素画了")

    # ffmpeg 的 palette 约定是 256 像素的 16×16 图。不足 256 用循环填满：
    # 重复项与原色完全相同，paletteuse 选谁都是同一个 RGB，不影响锁色。
    a.out.parent.mkdir(parents=True, exist_ok=True)
    im = Image.new("RGB", (16, 16))
    im.putdata([colors[i % len(colors)] for i in range(256)])
    im.save(a.out)

    if a.swatch:
        cell, cols = 96, min(8, len(colors))
        rows = (len(colors) + cols - 1) // cols
        sw = Image.new("RGB", (cols * cell, rows * cell), (0, 0, 0))
        for i, c in enumerate(colors):
            block = Image.new("RGB", (cell, cell), c)
            sw.paste(block, ((i % cols) * cell, (i // cols) * cell))
        a.swatch.parent.mkdir(parents=True, exist_ok=True)
        sw.save(a.swatch)

    print(f"{len(colors)} 色 → {a.out}" + (f" / 色卡 {a.swatch}" if a.swatch else ""))


if __name__ == "__main__":
    main()
