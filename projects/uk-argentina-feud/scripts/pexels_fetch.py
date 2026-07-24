#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Pexels 检索下载真实视频空镜(代替文字卡)。下载到 compose/assets/broll/。"""
import json, os, urllib.request, urllib.parse

KEY = os.environ["PEXELS_API_KEY"]
ROOT = "/Users/admin/kuleshov/.claude/worktrees/estee-lauder-night-video-7162e0/projects/uk-argentina-feud"
OUT = f"{ROOT}/compose/assets/broll"
os.makedirs(OUT, exist_ok=True)

NEEDS = {
    "ocean":    "atlantic ocean big waves aerial",
    "ba_city":  "buenos aires aerial city",
    "port":     "cargo ship port loading",
    "london":   "london street city grey",
    "sea_grey": "rough grey stormy sea",
    "stadium":  "soccer stadium crowd night",
    "fans":     "crowd celebrating flags cheering",
    "airport":  "airport arrivals people walking",
}
for name, q in NEEDS.items():
    try:
        url = f"https://api.pexels.com/videos/search?query={urllib.parse.quote(q)}&per_page=6&orientation=landscape&size=medium"
        req = urllib.request.Request(url, headers={"Authorization": KEY, "User-Agent": "Mozilla/5.0"})
        d = json.load(urllib.request.urlopen(req, timeout=30))
        got = False
        for v in d.get("videos", []):
            if not (5 <= v["duration"] <= 45):
                continue
            hd = [f for f in v["video_files"] if f.get("quality") == "hd" and f.get("width", 0) >= 1280 and f.get("width", 0) <= 2560]
            if hd:
                link = sorted(hd, key=lambda f: f["width"])[0]["link"]
                import subprocess
                subprocess.run(["curl", "-sS", "-A", "Mozilla/5.0", "-e", "https://www.pexels.com/",
                                "-L", link, "-o", f"{OUT}/{name}.mp4"], check=True, timeout=180)
                print(f"{name}: id{v['id']} {v['duration']}s {hd[0]['width']}w ✓")
                got = True
                break
        if not got:
            print(f"{name}: 无合适素材")
    except Exception as e:
        print(f"{name}: ERR {str(e)[:60]}")
print("PEXELS_FETCH_DONE")
