"""adapter 契约（DESIGN.md §4）。

adapter 不碰 film.json——产物回填、成本追加、状态转移由框架统一走 ir_patch，
所有写入不变量（状态机/留痕前置/ledger 只追加）自动生效。

禁静默降级（铁律 5）在执行层的形状：失败即结构化报错返回，adapter 内部
不自动换 provider、不自动改参数重试——重试与降级是调用方带着人的裁决做的事。
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from pathlib import Path

from ..models import FilmIR


@dataclass
class Target:
    raw: str            # 如 "shots.s03" / "audio.voiceover" / "compose"
    kind: str           # shots | shot_groups | anchors | audio.voiceover | compose
    id: str | None      # 实体 id（compose / audio.voiceover 为 None）
    provider: str


@dataclass
class Plan:
    target: str
    provider: str
    description: str
    requests: list[dict] = field(default_factory=list)   # 已脱敏（不含密钥）
    est_cost_usd: float | None = None
    warnings: list[str] = field(default_factory=list)


@dataclass
class RunResult:
    """框架把 ops 走 ir_patch 落盘；artifacts 仅作汇报。"""
    ops: list[dict]
    artifacts: list[str] = field(default_factory=list)
    summary: str = ""


class Adapter(ABC):
    name: str = ""
    mode: str = ""      # baked | declarative | audio

    @abstractmethod
    def plan(self, ir: FilmIR, target: Target, project_dir: Path) -> Plan: ...

    @abstractmethod
    def run(self, ir: FilmIR, target: Target, plan: Plan, project_dir: Path) -> RunResult: ...


def load_env(repo_root: Path) -> dict[str, str]:
    """读仓库根 .env（gitignored）。只解析 KEY=VALUE 行；值不回显进任何输出。"""
    env: dict[str, str] = {}
    f = repo_root / ".env"
    if not f.is_file():
        return env
    for line in f.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        if line.startswith("export "):
            line = line[len("export "):]
        k, v = line.split("=", 1)
        env[k.strip()] = v.strip().strip("'\"")
    return env


def find_repo_root(start: Path) -> Path:
    """从项目目录向上找仓库根（.env / .git 所在层）。"""
    p = start.resolve()
    for cand in (p, *p.parents):
        if (cand / ".env").is_file() or (cand / ".git").exists():
            return cand
    return start
