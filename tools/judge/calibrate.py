#!/usr/bin/env python3
"""评委校准（先校准后放权，m1-plan §7/22 验收项的量化工具）。

输入 CSV（UTF-8，带表头）：film,human_overall,judge_overall
（overall = 9 维均分或总分，人机口径一致即可；可另带 human_D1..D9/judge_D1..D9 列，忽略不报错）
输出：Spearman 秩相关 + 逐片对比表。放权判据由作者定（建议 ρ ≥ 0.7 才给否决权）。

用法：python3 tools/judge/calibrate.py <scores.csv>
"""

from __future__ import annotations

import csv
import sys


def spearman(xs: list[float], ys: list[float]) -> float:
    def ranks(v: list[float]) -> list[float]:
        order = sorted(range(len(v)), key=lambda i: v[i])
        r = [0.0] * len(v)
        i = 0
        while i < len(order):           # 并列取平均秩
            j = i
            while j + 1 < len(order) and v[order[j + 1]] == v[order[i]]:
                j += 1
            avg = (i + j) / 2 + 1
            for k in range(i, j + 1):
                r[order[k]] = avg
            i = j + 1
        return r
    rx, ry = ranks(xs), ranks(ys)
    n = len(xs)
    mx, my = sum(rx) / n, sum(ry) / n
    cov = sum((a - mx) * (b - my) for a, b in zip(rx, ry))
    vx = sum((a - mx) ** 2 for a in rx) ** 0.5
    vy = sum((b - my) ** 2 for b in ry) ** 0.5
    return cov / (vx * vy) if vx and vy else float("nan")


def main() -> int:
    if len(sys.argv) != 2:
        print(__doc__, file=sys.stderr)
        return 2
    rows = list(csv.DictReader(open(sys.argv[1], encoding="utf-8")))
    if len(rows) < 3:
        print(f"只有 {len(rows)} 片——样本太少，相关系数无意义（≥5 片再谈放权）",
              file=sys.stderr)
    hs = [float(r["human_overall"]) for r in rows]
    js = [float(r["judge_overall"]) for r in rows]
    rho = spearman(hs, js)
    print(f"{'片':32s} {'人工':>6s} {'评委':>6s} {'差':>6s}")
    for r, h, j in zip(rows, hs, js):
        print(f"{r['film']:32s} {h:6.2f} {j:6.2f} {j - h:+6.2f}")
    print(f"\nSpearman ρ = {rho:.3f}（n={len(rows)}）")
    print("放权参考：ρ ≥ 0.7 且无系统性放水（评委均分-人工均分 ≤ +0.3）才建议给否决权；"
          "此前评委分只并行记录。")
    return 0


if __name__ == "__main__":
    sys.exit(main())
