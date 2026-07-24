"""Provider adapters（去模型化 · 2026-07-24）：`plan()` 完整把 IR 条目译成 provider 请求方言，
`run()` 把真调用**委托宿主 harness**——外挂不持 provider key、不选模型。宿主的 provider 工具
执行请求后 `ir_patch` 回填 `gen.file` / `cost_usd` / `duration_actual_s` + `status=generated`。

与 tts.py（自带-key 直调，本地路径）的差异是刻意的：出图 / 视频 / 数字人 / 检索是"花钱且模型
相关"的动作，交宿主统一注入 key 与计费（无摩擦交付）；本层只沉淀值得留的、harness 无关的**翻译**。
委托态用镜头状态 `sourced`（请求已备好、待宿主执行）——宿主生成后转 `generated`（留痕前置：gen 已在）。
"""
from __future__ import annotations

import json
import re
import time
from pathlib import Path

from ..errors import IRError, RULE_ZERO
from ..models import FilmIR
from .base import Adapter, Plan, RunResult, Target


def _anchor_files(ir: FilmIR, refs: list[str]) -> list[dict]:
    """anchor_refs（"anchor:styleXX" 或 "aXX"）→ [{id, file, type}]；查无条目即拒（铁律 1）。"""
    out = []
    for r in refs:
        aid = r.split(":", 1)[1] if ":" in r else r
        a = next((x for x in ir.anchors if x.id == aid), None)
        if a is None:
            raise IRError(RULE_ZERO, f"anchor_refs 指向不存在的锚点: {r}",
                          hint="先在 anchors 阶段写入该锚点条目（先写 IR 再花钱）")
        out.append({"id": a.id, "file": a.file, "type": a.type})
    return out


def _shot(ir: FilmIR, sid: str):
    s = next((x for x in ir.shots if x.id == sid), None)
    if s is None:
        raise IRError(RULE_ZERO, f"IR 里没有镜头 {sid}")
    return s


def _next_dec_id(ir: FilmIR) -> str:
    mx = 0
    for d in ir.ledger.decisions:
        m = re.fullmatch(r"d(\d+)", str(d.id))
        if m:
            mx = max(mx, int(m.group(1)))
    return f"d{mx + 1:02d}"


def _delegate(target: Target, plan: Plan, project_dir: Path, ir: FilmIR, *,
              subdir: str) -> RunResult:
    """去模型化委托的统一回填：写请求文件 + gen(记录请求、无结果) + 置委托态 + 记 ledger 决策。"""
    (project_dir / subdir).mkdir(exist_ok=True)
    req_rel = f"{subdir}/{target.id}.request.json"
    (project_dir / req_rel).write_text(
        json.dumps(plan.requests, ensure_ascii=False, indent=2), encoding="utf-8")
    today = time.strftime("%Y-%m-%d")
    req = plan.requests[0] if len(plan.requests) == 1 else {"requests": plan.requests}
    gen = {"model": f"{target.provider} (delegated)", "params": req,
           "request_file": req_rel, "date": today,
           "note": "去模型化委托：宿主 provider 工具执行本请求后 ir_patch 回填 "
                   "file/cost_usd/duration_actual_s 并置 status=generated"}
    ops: list[dict] = [{"op": "append", "path": "ledger.decisions", "value": {
        "id": _next_dec_id(ir), "date": today, "stage": str(ir.meta.status),
        "decision": f"{target.raw} 请求已译好、交宿主 provider 工具执行",
        "why": "去模型化：外挂不持 provider key，真调用由宿主工具做（无摩擦交付）"}}]
    if target.kind == "shots":
        ops += [{"op": "set", "path": f"shots[{target.id}].gen", "value": gen},
                {"op": "set", "path": f"shots[{target.id}].status", "value": "sourced"}]
    elif target.kind == "shot_groups":
        g = next(x for x in ir.shot_groups if x.id == target.id)
        for sid in g.shots:
            ops += [{"op": "set", "path": f"shots[{sid}].gen", "value": gen},
                    {"op": "set", "path": f"shots[{sid}].status", "value": "sourced"}]
    elif target.kind == "anchors":
        ops.append({"op": "set", "path": f"anchors[{target.id}].gen", "value": gen})
        # 锚点无 sourced 态：保持 planned，宿主生成后置 generated
    return RunResult(ops=ops, artifacts=[str(project_dir / req_rel)],
                     summary=f"{target.provider} 请求已备好交宿主执行：{req_rel}")


class SeedanceAdapter(Adapter):
    name, mode = "seedance", "baked"
    MODEL = "doubao-seedance-2-0-260128"
    MAX_SHOT_S = 15

    def _shot_spec(self, ir: FilmIR, s) -> dict:
        refs = _anchor_files(ir, s.anchor_refs)
        p = s.source.params or {}
        spec = {"shot_id": s.id, "duration_s": round(s.t[1] - s.t[0], 2),
                "prompt": p.get("prompt") or f"{s.intent}. 运镜: {s.motion or '静置'}",
                "image_refs": [r["file"] for r in refs if r["file"]],
                "seed": p.get("seed")}
        kf = [r for r in refs if r["type"] == "keyframe"]
        if kf:
            spec["first_frame"] = kf[0]["file"]
            if len(kf) > 1:
                spec["last_frame"] = kf[1]["file"]
        return spec

    def plan(self, ir, target, project_dir):
        warnings = []
        if target.kind == "shot_groups":
            g = next(x for x in ir.shot_groups if x.id == target.id)
            shots = [_shot(ir, sid) for sid in g.shots]
            total = round(sum(s.t[1] - s.t[0] for s in shots), 2)
            if total > self.MAX_SHOT_S:
                warnings.append(f"组时长 {total}s 超 Seedance 单次上限 {self.MAX_SHOT_S}s")
            req = {"model": self.MODEL, "aspect": ir.meta.aspect, "group_id": g.id,
                   "duration_s": total, "seam_out": g.seam_out,
                   "multi_shot": [self._shot_spec(ir, s) for s in shots]}
            desc = f"Seedance 镜头组 {g.id}（{len(shots)} 镜多镜头语法，{total}s）→ 交宿主生成"
        else:
            s = _shot(ir, target.id)
            spec = self._shot_spec(ir, s)
            if spec["duration_s"] > self.MAX_SHOT_S:
                warnings.append(f"镜头 {s.id} {spec['duration_s']}s 超上限；应划入 shot_group 拆分")
            req = {"model": self.MODEL, "aspect": ir.meta.aspect, **spec}
            desc = f"Seedance 单镜 {s.id}（{spec['duration_s']}s）→ 交宿主生成"
        return Plan(target=target.raw, provider=self.name, description=desc,
                    requests=[req], warnings=warnings)

    def run(self, ir, target, plan, project_dir):
        return _delegate(target, plan, project_dir, ir, subdir="shots")


class CollageBrollAdapter(SeedanceAdapter):
    """拼贴 b-roll：GPT-Image 半调纸拼贴静帧 → Seedance 首尾帧 assemble（同 Seedance 通路的方言变体）。"""
    name = "collage_broll"

    def plan(self, ir, target, project_dir):
        plan = super().plan(ir, target, project_dir)
        for req in plan.requests:
            req["assembly"] = "collage_first_last_frame"
            req["constraints"] = "无文字/数字/logo（要文字走 HyperFrames 叠层）；从空色场组装"
        plan.description = plan.description.replace("Seedance", "拼贴 b-roll（Seedance 首尾帧组装）")
        return plan


class ImageMotionAdapter(Adapter):
    name, mode = "image_motion", "declarative"
    MODEL = "gpt-image-2"

    def plan(self, ir, target, project_dir):
        if target.kind == "anchors":
            a = next(x for x in ir.anchors if x.id == target.id)
            req = {"model": self.MODEL, "anchor_id": a.id, "type": a.type,
                   "prompt": a.intent or a.type, "aspect": a.aspect or ir.meta.aspect}
            return Plan(target=target.raw, provider=self.name, requests=[req],
                        description=f"GPT-Image 锚点 {a.id}（{a.type}）→ 交宿主生成")
        s = _shot(ir, target.id)   # 声明型镜头：compose 阶段用锚点 + Ken Burns 渲染，无外部生成
        return Plan(target=target.raw, provider=self.name,
                    description=f"声明型 image_motion 镜 {s.id}：compose 渲染（Ken Burns/视差），无单独生成步",
                    requests=[{"kind": "declarative", "anchor_refs": s.anchor_refs,
                               "motion": s.motion or "ken_burns"}])

    def run(self, ir, target, plan, project_dir):
        if target.kind == "anchors":
            return _delegate(target, plan, project_dir, ir, subdir="anchors")
        return RunResult(   # 声明型：不外部生成，标 sourced（源=锚点已定），compose 渲染
            ops=[{"op": "set", "path": f"shots[{target.id}].status", "value": "sourced"}],
            artifacts=[],
            summary=f"{target.id} 声明型（image_motion）：compose 阶段渲染，无外部生成")


class AvatarAdapter(Adapter):
    name, mode = "avatar", "baked"
    MODEL = "fal-ai/heygen/avatar4/image-to-video"

    def plan(self, ir, target, project_dir):
        s = _shot(ir, target.id)
        refs = _anchor_files(ir, s.anchor_refs)
        portrait = next((r for r in refs if r["type"] == "avatar_portrait"), None)
        warnings = []
        if portrait is None:
            warnings.append("缺 avatar_portrait 锚点——数字人镜必须挂形象锚点")
        audio = ir.audio.voiceover.file if (ir.audio.voiceover and ir.audio.voiceover.file) else None
        if not audio:
            warnings.append("缺音频（数字人时长=音频时长，须音频先行）")
        req = {"model": self.MODEL, "aspect_ratio": ir.meta.aspect,
               "portrait": portrait["file"] if portrait else None,
               "audio_file": audio, "voice_ref": s.voice_ref,
               "note": "分节切片由宿主按 voice_ref 区间做"}
        return Plan(target=target.raw, provider=self.name, requests=[req], warnings=warnings,
                    description=f"数字人 {s.id}（HeyGen Avatar4，时长=音频）→ 交宿主生成")

    def run(self, ir, target, plan, project_dir):
        return _delegate(target, plan, project_dir, ir, subdir="shots")


class FootageAdapter(Adapter):
    name, mode = "footage", "baked"
    TIERS = ("pexels", "pixabay", "archive_org", "wikimedia", "apihub")

    def plan(self, ir, target, project_dir):
        s = _shot(ir, target.id)
        p = s.source.params or {}
        tier = p.get("tier") or ("apihub" if "新闻" in (s.intent or "") else "pexels")
        warnings = [] if tier in self.TIERS else [f"未知素材层 {tier!r}"]
        req = {"query": p.get("query") or s.intent, "tier": tier,
               "duration_s": round(s.t[1] - s.t[0], 2),
               "license_required": True, "max_broadcast_risk_s": 3,
               "dedup": "一素材全片一次"}
        return Plan(target=target.raw, provider=self.name, requests=[req], warnings=warnings,
                    description=f"检索素材 {s.id}（{tier} 层，license 硬门）→ 交宿主检索+下载")

    def run(self, ir, target, plan, project_dir):
        return _delegate(target, plan, project_dir, ir, subdir="shots")
