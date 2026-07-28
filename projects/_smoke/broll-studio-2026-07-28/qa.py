#!/usr/bin/env python3
"""六条 clip 的机器验收 + 汇总表 + 逐条 contact sheet。"""
import io
import json
import subprocess
import sys
from pathlib import Path

P = Path("projects/_smoke/broll-studio-2026-07-28")
ORDER = ["object-theatre", "technical-diagram", "clay-miniature",
         "felted-wool", "popup-book", "toy-world"]


def main():
    rows = []
    for pid in ORDER:
        clip = P / "shots" / f"{pid}_raw.mp4"
        if not clip.exists():
            rows.append((pid, "缺片", "—", "—", "—"))
            continue
        r = subprocess.run(
            ["python3", "tools/clip-qa.py", str(clip), "--expect-size", "720x1280",
             "--json", str(P / "evidence" / f"qa-{pid}.json"),
             "--contact", str(P / "evidence" / f"{pid}-contact.jpg")],
            capture_output=True, text=True)
        d = json.loads(r.stdout)
        c = d["checks"]
        rows.append((pid, d["verdict"], f"{d['spec']['duration_s']}s",
                     f"{d['spec']['width']}x{d['spec']['height']}",
                     f"{c['dead_tail']['tail_ratio']:.0%}"))

    print(f"{'profile':20}{'判定':8}{'时长':10}{'规格':12}尾段/全片运动量")
    for pid, v, dur, size, ratio in rows:
        mark = "✅" if v == "pass" else "❌"
        print(f"{pid:20}{mark} {v:5}{dur:10}{size:12}{ratio}")

    io.open(P / "evidence" / "summary.json", "w", encoding="utf-8").write(json.dumps(
        [{"profile": p, "verdict": v, "duration": d, "size": s, "tail_ratio": t}
         for p, v, d, s, t in rows], ensure_ascii=False, indent=2))
    return 0 if all(r[1] == "pass" for r in rows) else 1


if __name__ == "__main__":
    sys.exit(main())
