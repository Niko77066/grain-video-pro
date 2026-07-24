"""ir_execute 框架：Rule Zero 写入层强制 + provider 分发 + 统一回填。

一切生成动作必须对应 IR 里已存在的条目（铁律 1）——target 查无条目即拒绝，
这不是提示词礼貌，是代码拒绝。
"""

from __future__ import annotations

from pathlib import Path

from ..errors import IRError, BAD_OP, NOT_FOUND, RULE_ZERO, ENGINE_FAILURE
from ..models import FilmIR
from ..patch import apply_patch
from ..store import Project
from .base import Adapter, Plan, RunResult, Target
from .hyperframes import HyperframesAdapter
from .providers import (AvatarAdapter, CollageBrollAdapter, FootageAdapter,
                        ImageMotionAdapter, SeedanceAdapter)
from .tts import TTSAdapter

REGISTRY: dict[str, Adapter] = {a.name: a for a in (
    TTSAdapter(), HyperframesAdapter(),
    SeedanceAdapter(), CollageBrollAdapter(), ImageMotionAdapter(),
    AvatarAdapter(), FootageAdapter(),
)}


def resolve_target(ir: FilmIR, raw: str) -> Target:
    """Rule Zero：先查 IR 条目，再谈执行。"""
    if raw == "compose":
        return Target(raw=raw, kind="compose", id=None, provider="hyperframes")
    if raw == "audio.voiceover":
        if ir.audio.voiceover is None:
            raise IRError(RULE_ZERO, "IR 里没有 audio.voiceover 条目，不许调 TTS",
                          path="audio.voiceover",
                          hint="先 ir_patch 写入 voiceover 条目（含 text_prompt_file）")
        return Target(raw=raw, kind="audio.voiceover", id=None, provider="tts")
    if "." in raw:
        kind, id_ = raw.split(".", 1)
        if kind == "shots":
            shot = next((s for s in ir.shots if s.id == id_), None)
            if shot is None:
                raise IRError(RULE_ZERO, f"IR 里没有镜头 {id_}，不许生成",
                              path=f"shots[{id_}]",
                              hint="先在 storyboard 阶段写入镜头条目（先写 IR，再花钱）")
            return Target(raw=raw, kind="shots", id=id_, provider=shot.source.provider)
        if kind == "shot_groups":
            g = next((x for x in ir.shot_groups if x.id == id_), None)
            if g is None:
                raise IRError(RULE_ZERO, f"IR 里没有镜头组 {id_}，不许生成",
                              path=f"shot_groups[{id_}]")
            return Target(raw=raw, kind="shot_groups", id=id_, provider=g.provider)
        if kind == "anchors":
            a = next((x for x in ir.anchors if x.id == id_), None)
            if a is None:
                raise IRError(RULE_ZERO, f"IR 里没有锚点 {id_}，不许生成",
                              path=f"anchors[{id_}]")
            return Target(raw=raw, kind="anchors", id=id_, provider="image_motion")
    raise IRError(BAD_OP, f"不认识的执行目标: {raw!r}",
                  hint="支持 shots.<id> / shot_groups.<id> / anchors.<id> / audio.voiceover / compose")


def _adapter_for(target: Target) -> Adapter:
    ad = REGISTRY.get(target.provider)
    if ad is None:
        raise IRError(NOT_FOUND, f"未注册的 provider: {target.provider}")
    return ad


def _budget_fuse(ir: FilmIR) -> None:
    b = ir.meta.budget
    if b.cap_usd is not None and b.spent_usd >= b.cap_usd:
        raise IRError(ENGINE_FAILURE,
                      f"预算熔断：已花 {b.spent_usd} ≥ 上限 {b.cap_usd}（铁律 6）",
                      path="meta.budget",
                      hint="加预算走门控字段修订（--revision），或砍内容")


def execute(project: Project, targets: list[str], *, dry_run: bool = False) -> dict:
    """按 target 逐个执行；每个 target 成功即落盘（半途失败不吞掉已完成的留痕）。"""
    results = []
    with project.locked():
        for raw in targets:
            ir = project.load()          # 每个 target 都读最新状态
            target = resolve_target(ir, raw)
            adapter = _adapter_for(target)
            plan = adapter.plan(ir, target, project.dir)
            if dry_run:
                results.append({"target": raw, "provider": target.provider,
                                "plan": plan.__dict__, "dry_run": True})
                continue
            _budget_fuse(ir)
            run: RunResult = adapter.run(ir, target, plan, project.dir)
            if run.ops:
                new_dict, _ = apply_patch(ir.dump(), run.ops)
                project.save_raw(new_dict)
            results.append({"target": raw, "provider": target.provider,
                            "summary": run.summary, "artifacts": run.artifacts,
                            "ops_applied": len(run.ops)})
    return {"ok": True, "results": results}
