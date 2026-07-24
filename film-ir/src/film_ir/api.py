"""四动词 API 门面（DESIGN.md §1）。库调用方与 CLI 共用这一层。"""

from __future__ import annotations

from pathlib import Path

from .errors import IRError, CONFLICT
from .gates import run_gates
from .migrate import migrate
from .models import Commitment, FilmIR, Meta
from .patch import PatchResult, apply_patch
from .selectors import resolve
from .store import Project
from . import execute as _execute


def ir_read(project: str | Path, selector: str):
    ir = Project(project).load()
    return resolve(ir.dump(), selector)


def ir_patch(project: str | Path, ops: list[dict],
             revision: dict | None = None) -> dict:
    p = Project(project)
    with p.locked():
        ir = p.load()
        new_dict, result = apply_patch(ir.dump(), ops, revision)
        p.save_raw(new_dict)
    return {"ok": True, "applied": result.applied,
            "changed_paths": result.changed_paths,
            "revision_decision_id": result.revision_decision_id}


def ir_validate(project: str | Path, stage: str | None = None) -> dict:
    p = Project(project)
    return run_gates(p.load(), stage, project_dir=p.dir)


def ir_execute(project: str | Path, targets: list[str], *,
               dry_run: bool = False) -> dict:
    return _execute.execute(Project(project), targets, dry_run=dry_run)


def ir_new(project: str | Path, *, title: str, format: str = "",
           style_pack: str = "", duration_s: float = 60,
           tolerance_pct: float = 5, aspect: str = "16:9") -> dict:
    p = Project(project)
    if p.exists():
        raise IRError(CONFLICT, f"film.json 已存在: {p.file}",
                      hint="续跑请直接 read/patch；重开新片换目录")
    ir = FilmIR(meta=Meta(
        title=title, format=format, style_pack=style_pack, aspect=aspect,
        commitment=Commitment(type="", duration_s=duration_s,
                              tolerance_pct=tolerance_pct),
    ))
    p.dir.mkdir(parents=True, exist_ok=True)
    p.save(ir)
    return {"ok": True, "file": str(p.file)}


def ir_migrate(project: str | Path, *, write: bool = False) -> dict:
    p = Project(project)
    with p.locked():
        raw = p.load_raw()
        new_dict, log = migrate(raw)
        report = run_gates(FilmIR.model_validate(new_dict))
        if write:
            p.save_raw(new_dict)
    return {"ok": True, "written": write, "changes": log,
            "post_migration_gates": report}
