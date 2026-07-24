"""HyperFrames adapter：确定性合成（引擎知识包 hyperframes.md 的代码化）。

G1 硬门在此层强制：lint 不过禁 render（不是提醒，是拒绝执行）。
render 一律 --docker（帧级复现，golden-set 基线口径）。
"""

from __future__ import annotations

import subprocess
import time
from pathlib import Path

from ..errors import IRError, ENGINE_FAILURE, RULE_ZERO
from ..models import FilmIR
from .base import Adapter, Plan, RunResult, Target

LINT_CMD = ["npx", "hyperframes", "lint"]
RENDER_CMD = ["npx", "hyperframes", "render", "--docker"]
TAIL = 2000  # 报错回带的输出尾部长度


class HyperframesAdapter(Adapter):
    name = "hyperframes"
    mode = "declarative"

    def _compose_dir(self, project_dir: Path) -> Path:
        d = project_dir / "compose"
        if not d.is_dir():
            raise IRError(RULE_ZERO, f"compose/ 目录不存在: {d}",
                          hint="声明型镜头与叠加层先写成 composition，再执行 compose")
        return d

    def plan(self, ir: FilmIR, target: Target, project_dir: Path) -> Plan:
        self._compose_dir(project_dir)
        return Plan(target=target.raw, provider=self.name,
                    description="lint → （过门才）render --docker",
                    requests=[{"cmd": " ".join(LINT_CMD)}, {"cmd": " ".join(RENDER_CMD)}],
                    est_cost_usd=0.0)

    def run(self, ir: FilmIR, target: Target, plan: Plan, project_dir: Path) -> RunResult:
        cwd = self._compose_dir(project_dir)
        today = time.strftime("%Y-%m-%d")

        lint = subprocess.run(LINT_CMD, cwd=cwd, capture_output=True, text=True)
        lint_out = (lint.stdout + lint.stderr)[-TAIL:]
        if lint.returncode != 0:
            raise IRError(ENGINE_FAILURE, "hyperframes lint 不过，禁 render（G1 硬门）",
                          hint=lint_out)

        t0 = time.monotonic()
        render = subprocess.run(RENDER_CMD, cwd=cwd, capture_output=True, text=True)
        wallclock = round(time.monotonic() - t0, 1)
        render_out = (render.stdout + render.stderr)[-TAIL:]
        if render.returncode != 0:
            raise IRError(ENGINE_FAILURE, "hyperframes render 失败", hint=render_out)

        artifacts = sorted(str(p) for p in (project_dir / "out").glob("*.mp4")) \
            if (project_dir / "out").is_dir() else []
        gate_id = f"g{len(ir.ledger.gates) + 1:02d}"
        ops = [{"op": "append", "path": "ledger.gates", "value": {
            "id": gate_id, "stage": "compose", "date": today,
            "check": "hyperframes lint → render --docker",
            "result": "pass",
            "evidence": f"lint 0 error；render {wallclock}s；产物 {artifacts or '见 render 输出'}",
        }}]
        return RunResult(ops=ops, artifacts=artifacts,
                         summary=f"lint 过门，render 完成（{wallclock}s）")
