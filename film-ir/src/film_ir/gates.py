"""ir_validate：G1 门套件（DESIGN.md §3）。

纯代码、确定性、零 LLM（蓝图 §09 G1 口径）。error = 硬门；warn = 语义自查里
可代码判定的部分降级为提示（M0/M1 由人眼终审的项不假装能判）。

每个门自己判断所需数据是否在场，不在场即静默跳过——门按 from_stage 声明
"从哪个阶段起生效"，validate 时以 meta.status（或显式 --stage）为准。
"""

from __future__ import annotations

import json
from dataclasses import dataclass, asdict, field
from pathlib import Path

from . import contract as _contract
from .models import FilmIR, STAGES

EPS_SEAM = 0.06        # 相邻镜头缝隙/重叠容差（秒）
EPS_END = 0.5          # 首尾对齐音频总长容差（秒）
EPS_GROUP = 0.25       # 组时长 vs 成员镜头之和容差（秒）
GROUP_MAX_S = 15.0     # Seedance 单次生成上限
GROUP_MAX_SHOTS = 5
STATIC_RUN_MAX = 2     # 静态类连续镜头上限（幻灯片风险）
TRANSITIONS_MAX = 4    # 全片转场词汇上限（品味宪法）
VISUAL_CHANGE_MAX_S = 10.5  # 每 8–10s 一次视觉变化的可码判上界

_STAGE_INDEX = {s: i for i, s in enumerate(STAGES)}
_STAGE_INDEX["delivered"] = len(STAGES)


@dataclass
class Violation:
    gate: str
    severity: str          # error | warn
    path: str
    message: str
    evidence: str = ""

    def to_dict(self) -> dict:
        return asdict(self)


def _err(gate, path, message, evidence=""):
    return Violation(gate, "error", path, message, evidence)


def _warn(gate, path, message, evidence=""):
    return Violation(gate, "warn", path, message, evidence)


# ---------------------------------------------------------------- 各门

def refs_integrity(ir: FilmIR) -> list[Violation]:
    v: list[Violation] = []
    anchor_ids = {a.id for a in ir.anchors}
    shot_ids = {s.id for s in ir.shots}
    group_ids = {g.id for g in ir.shot_groups}
    section_ids = {s.id for s in ir.audio.timeline.sections} if ir.audio.timeline else None

    for s in ir.shots:
        for ref in s.anchor_refs:
            if ref not in anchor_ids:
                v.append(_err("refs", f"shots[{s.id}].anchor_refs",
                              f"锚点引用不存在: {ref}"))
        if s.group_ref and s.group_ref not in group_ids:
            v.append(_err("refs", f"shots[{s.id}].group_ref",
                          f"镜头组引用不存在: {s.group_ref}"))
        if s.voice_ref and section_ids is not None and s.voice_ref not in section_ids:
            v.append(_err("refs", f"shots[{s.id}].voice_ref",
                          f"音频分节引用不存在: {s.voice_ref}"))
    for g in ir.shot_groups:
        for sid in g.shots:
            if sid not in shot_ids:
                v.append(_err("refs", f"shot_groups[{g.id}].shots",
                              f"镜头引用不存在: {sid}"))
    for o in ir.overlays:
        for sid in (list(o.shot_range or ()) + list(o.shot_refs or ())):
            if sid not in shot_ids:
                v.append(_err("refs", f"overlays[{o.id}]",
                              f"镜头引用不存在: {sid}"))
        if not o.shot_range and not o.shot_refs and o.scope != "global":
            v.append(_warn("refs", f"overlays[{o.id}]",
                           "叠加层无 shot_range/shot_refs 也非 scope=global，无法定位"))
    return v


def timeline_coverage(ir: FilmIR) -> list[Violation]:
    """镜头区间无缝隙、无重叠、首尾对齐音频总长（分镜自查第 1 项）。"""
    if not ir.shots or not ir.audio.timeline:
        return []
    v: list[Violation] = []
    shots = sorted(ir.shots, key=lambda s: s.t[0])
    if abs(shots[0].t[0]) > EPS_SEAM:
        v.append(_err("timeline.coverage", f"shots[{shots[0].id}].t",
                      f"首镜头未从 0 开始（{shots[0].t[0]:.2f}s）"))
    for prev, nxt in zip(shots, shots[1:]):
        delta = nxt.t[0] - prev.t[1]
        if delta > EPS_SEAM:
            v.append(_err("timeline.coverage", f"shots[{nxt.id}].t",
                          f"{prev.id} → {nxt.id} 之间有 {delta:.2f}s 缝隙"))
        elif delta < -EPS_SEAM:
            v.append(_err("timeline.coverage", f"shots[{nxt.id}].t",
                          f"{prev.id} 与 {nxt.id} 重叠 {-delta:.2f}s"))
    dur = ir.audio.timeline.duration_s
    tail = shots[-1].t[1]
    if abs(tail - dur) > EPS_END:
        v.append(_err("timeline.coverage", f"shots[{shots[-1].id}].t",
                      f"末镜头止于 {tail:.2f}s，音频总长 {dur:.2f}s（差 {abs(tail-dur):.2f}s）"))
    return v


def commitment_duration(ir: FilmIR) -> list[Violation]:
    """音频总长在承诺 ± tolerance 内（audio 阶段 G1 自查第 2 项）。"""
    tl = ir.audio.timeline
    if not tl:
        return []
    c = ir.meta.commitment
    lo = c.duration_s * (1 - c.tolerance_pct / 100)
    hi = c.duration_s * (1 + c.tolerance_pct / 100)
    if not (lo <= tl.duration_s <= hi):
        return [_err("timeline.commitment", "audio.timeline.duration_s",
                     f"音频 {tl.duration_s:.2f}s 超出承诺 {c.duration_s}s ± {c.tolerance_pct}%",
                     evidence=f"允许区间 [{lo:.2f}, {hi:.2f}]")]
    return []


def groups_arithmetic(ir: FilmIR) -> list[Violation]:
    """组划分算术：确定性校验，不赌模型细心（分镜自查第 7 项）。"""
    seedance_shots = [s for s in ir.shots if s.source.provider == "seedance"]
    if not seedance_shots:
        return []
    v: list[Violation] = []
    membership: dict[str, list[str]] = {}
    for g in ir.shot_groups:
        for sid in g.shots:
            membership.setdefault(sid, []).append(g.id)
    for s in seedance_shots:
        owners = membership.get(s.id, [])
        if len(owners) != 1:
            v.append(_err("groups.arithmetic", f"shots[{s.id}]",
                          f"seedance 镜头必须恰属一个组，实属 {len(owners)} 个",
                          evidence=str(owners)))
    shot_by_id = {s.id: s for s in ir.shots}
    for g in ir.shot_groups:
        if len(g.shots) > GROUP_MAX_SHOTS:
            v.append(_err("groups.arithmetic", f"shot_groups[{g.id}]",
                          f"组内 {len(g.shots)} 镜，超上限 {GROUP_MAX_SHOTS}"))
        member_sum = sum(shot_by_id[sid].t[1] - shot_by_id[sid].t[0]
                         for sid in g.shots if sid in shot_by_id)
        dur = g.duration_s if g.duration_s is not None else member_sum
        if dur > GROUP_MAX_S + EPS_GROUP:
            v.append(_err("groups.arithmetic", f"shot_groups[{g.id}]",
                          f"组时长 {dur:.2f}s 超 Seedance 单次上限 {GROUP_MAX_S}s"))
        if g.duration_s is not None and abs(g.duration_s - member_sum) > EPS_GROUP:
            v.append(_err("groups.arithmetic", f"shot_groups[{g.id}].duration_s",
                          f"组时长 {g.duration_s:.2f}s ≠ 成员镜头之和 {member_sum:.2f}s"))
    return v


def slides_risk(ir: FilmIR) -> list[Violation]:
    """静态类连续 > 2 镜 = 幻灯片化（反模式零容忍，分镜自查第 4 项）。"""
    v: list[Violation] = []
    run: list[str] = []
    for s in sorted(ir.shots, key=lambda x: x.t[0]):
        if s.static_class:
            run.append(s.id)
        else:
            if len(run) > STATIC_RUN_MAX:
                v.append(_err("slides.risk", f"shots[{run[0]}]",
                              f"静态类镜头连续 {len(run)} 个（上限 {STATIC_RUN_MAX}）",
                              evidence=" → ".join(run)))
            run = []
    if len(run) > STATIC_RUN_MAX:
        v.append(_err("slides.risk", f"shots[{run[0]}]",
                      f"静态类镜头连续 {len(run)} 个（上限 {STATIC_RUN_MAX}）",
                      evidence=" → ".join(run)))
    return v


def edit_transitions(ir: FilmIR) -> list[Violation]:
    n = len(ir.edit.transitions)
    if n > TRANSITIONS_MAX:
        return [_err("edit.transitions", "edit.transitions",
                     f"转场词汇 {n} 种，超上限 {TRANSITIONS_MAX}（转场遮丑是心虚）",
                     evidence=", ".join(ir.edit.transitions))]
    return []


def baked_evidence(ir: FilmIR) -> list[Violation]:
    """烘焙型镜头 qc_pass 必须有产物与实测时长——出示证据，"我检查过了"不算数。"""
    v: list[Violation] = []
    for s in ir.shots:
        if s.source.provider in ("seedance", "avatar") and s.status == "qc_pass":
            if not s.gen or not s.gen.file:
                v.append(_err("baked.evidence", f"shots[{s.id}].gen",
                              "烘焙型镜头 qc_pass 但缺 gen.file 产物路径"))
            elif s.gen.duration_actual_s is None:
                v.append(_warn("baked.evidence", f"shots[{s.id}].gen.duration_actual_s",
                               "缺 ffprobe 实测时长（时长调和要用）"))
    return v


def budget_guard(ir: FilmIR) -> list[Violation]:
    b = ir.meta.budget
    if b.cap_usd is not None and b.spent_usd > b.cap_usd:
        return [_err("budget", "meta.budget",
                     f"已花 {b.spent_usd} 超上限 {b.cap_usd}（熔断口径，铁律 6）")]
    return []


def visual_change(ir: FilmIR) -> list[Violation]:
    return [_warn("visual.change", f"shots[{s.id}].t",
                  f"镜头长 {s.t[1] - s.t[0]:.1f}s（> {VISUAL_CHANGE_MAX_S}s 无视觉变化，"
                  "注意力租金按秒计）")
            for s in ir.shots if (s.t[1] - s.t[0]) > VISUAL_CHANGE_MAX_S]


def framing_repeat(ir: FilmIR) -> list[Violation]:
    v: list[Violation] = []
    run: list[str] = []
    prev = None
    for s in sorted(ir.shots, key=lambda x: x.t[0]):
        cur = (s.framing or "").strip()
        if cur and cur == prev:
            run.append(s.id)
            if len(run) == STATIC_RUN_MAX:  # 本镜 + 前两镜 = 连续 3 镜同 framing
                v.append(_warn("framing.repeat", f"shots[{s.id}].framing",
                               f"连续 >{STATIC_RUN_MAX} 镜同版式/景别: {cur}"))
        else:
            run = []
        prev = cur
    return v


def motion_word(ir: FilmIR) -> list[Violation]:
    return [_warn("intent.motion", f"shots[{s.id}].motion",
                  "seedance 镜头缺运镜词（每镜一个主动作 + 一个运镜）")
            for s in ir.shots
            if s.source.provider == "seedance" and not (s.motion or "").strip()]


def gen_traceability(ir: FilmIR) -> list[Violation]:
    """留痕完整性提示：无 model 名的 gen 块（多为迁移遗留）。"""
    v: list[Violation] = []
    gens = [(f"shots[{s.id}].gen", s.gen) for s in ir.shots] + \
           [(f"anchors[{a.id}].gen", a.gen) for a in ir.anchors]
    for path, g in gens:
        if g is not None and not g.model:
            v.append(_warn("gen.trace", path, "gen 留痕缺 model 名"))
    return v


# ---------------------------------------------------------------- 风格合同门（P0-2，2026-07-21）
# 这两道门看 IR 之外的世界：styles/<pack>/contract.json 与 evidence/render-metrics.json。
# 由来：五片对照实验——自报字段（static_class 等）可被无意或有意误标绕过上面所有门，
# 合同 + 成片实测是把"散文承诺"变成"不可绕过校验"的最小闭环。

DECLARED_GRAPHICS = ("hyperframes", "image_motion")  # 声明型图形 provider（幻灯片语法口径）
MISLABEL_ERROR_MIN = 3      # 自报/实测矛盾镜头数达此值升 error（1–2 镜留给实测误判余地）
EVIDENCE_STALE_S = 2.0      # 证据视频时长 vs 音频总长的漂移容忍


@dataclass
class GateContext:
    project_dir: Path | None = None


def _load_contract(ir: FilmIR, ctx: GateContext | None):
    if ctx is None or ctx.project_dir is None:
        return None, {}
    c = _contract.load_contract(ir.meta.style_pack, Path(ctx.project_dir))
    amendments = getattr(ir.meta, "contract_amendments", None) or {}
    return c, amendments


def _eff(c: dict, dotted: str, amendments: dict, v: list[Violation]) -> float | None:
    """取合同生效值；带宽内调整降 warn 提示（可见性），越界记 error 并退回原值。"""
    r = _contract.effective(c, dotted, amendments)
    if r is None:
        return None
    if r.out_of_bounds:
        v.append(_err("style.contract.amend", f"meta.contract_amendments[{dotted}]",
                      f"合同修改越出带宽，视为违约（越界值不生效）: {dotted} → {r.requested}",
                      evidence=f"带宽 {(_contract._leaf(c, dotted) or {}).get('amend')}"))
    elif r.amended:
        v.append(_warn("style.contract.amend", f"meta.contract_amendments[{dotted}]",
                       f"合同带宽内调整生效: {dotted} = {r.value}（原值 "
                       f"{(_contract._leaf(c, dotted) or {}).get('value')}，应有 ledger 修订理由）"))
    return r.value


def _shot_dur(s) -> float:
    return s.t[1] - s.t[0]


def style_contract_plan(ir: FilmIR, ctx: GateContext | None = None) -> list[Violation]:
    """storyboard 起：按 IR 声明预检风格合同——挡在花钱之前。"""
    c, amendments = _load_contract(ir, ctx)
    if c is None:
        return []
    v: list[Violation] = []
    for k in _contract.unknown_amendments(c, amendments):
        v.append(_err("style.contract.amend", f"meta.contract_amendments[{k}]",
                      f"修改指向不存在/不可调的合同条目: {k}"))
    plan = c.get("plan") or {}
    shots = sorted(ir.shots, key=lambda s: s.t[0])
    total = ir.audio.timeline.duration_s if ir.audio.timeline else None

    # 声部在场性（case-file 形）：provider 独占声部按 provider 计，
    # 共享 provider 的声部按 shots[].source.params.voice 声明计——无声明降 warn。
    voices = plan.get("voices") or {}
    any_declared = any((s.source.params or {}).get("voice") for s in shots)
    for name, spec in voices.items():
        min_shots = _eff(c, f"plan.voices.{name}.min_shots", amendments, v)
        if min_shots is None:
            continue
        if spec.get("declared_as"):
            if not any_declared:
                v.append(_warn("style.contract.plan", "shots[].source.params.voice",
                               f"声部『{name}』未声明（全片无 voice 标记），在场性未校验"
                               "——m1-v2 起 storyboard 必填"))
                continue
            n = sum(1 for s in shots
                    if (s.source.params or {}).get("voice") == spec["declared_as"])
        else:
            n = sum(1 for s in shots if s.source.provider in (spec.get("providers") or ()))
        if n < min_shots:
            v.append(_err("style.contract.plan", f"plan.voices.{name}",
                          f"声部『{name}』{n} 镜 < 下限 {min_shots:g}——声部不可删除，"
                          f"这是风格包立身之本（{spec.get('role', '')}）"))

    # provider 时长份额（pixel-chronicle 形）
    if total and plan.get("provider_share"):
        by_provider: dict[str, float] = {}
        for s in shots:
            by_provider[s.source.provider] = by_provider.get(s.source.provider, 0) + _shot_dur(s)
        for prov, band in (plan["provider_share"] or {}).items():
            if not isinstance(band, dict):   # "_footage_note" 类说明字段
                continue
            share = by_provider.get(prov, 0) / total
            lo = _eff(c, f"plan.provider_share.{prov}.min", amendments, v) if "min" in band else None
            hi = _eff(c, f"plan.provider_share.{prov}.max", amendments, v) if "max" in band else None
            if lo is not None and share < lo:
                v.append(_err("style.contract.plan", f"plan.provider_share.{prov}",
                              f"{prov} 声明份额 {share:.0%} < 下限 {lo:.0%}"))
            if hi is not None and share > hi:
                v.append(_err("style.contract.plan", f"plan.provider_share.{prov}",
                              f"{prov} 声明份额 {share:.0%} > 上限 {hi:.0%}"))

    # trait 份额（可跨 provider 重叠；分母=音频总长，见合同 denominators）
    traits = plan.get("traits") or {}
    if total and traits:
        if "pixel_narrative" in traits:
            # 显式标记 true 计入；未标记的 seedance 镜默认计入（声部表：像素叙事主力）
            dur = sum(_shot_dur(s) for s in shots
                      if (s.source.params or {}).get("pixel_narrative") is True
                      or ("pixel_narrative" not in (s.source.params or {})
                          and s.source.provider == "seedance"))
            share_min = _eff(c, "plan.traits.pixel_narrative.share_min", amendments, v)
            if share_min is not None and dur / total < share_min:
                v.append(_err("style.contract.plan", "plan.traits.pixel_narrative",
                              f"像素叙事份额 {dur / total:.0%} < 下限 {share_min:.0%}"
                              "——像素是叙事主体不是表层 LUT（纸纹+配色+褪色不算）"))
        if "ai_nonpixel_stylization" in traits:
            flagged = [s for s in shots if "ai_stylized" in (s.source.params or {})]
            if not flagged:
                v.append(_warn("style.contract.plan", "shots[].source.params.ai_stylized",
                               "ai_nonpixel_stylization 无声明，跳过校验（m1-v2 起必声明）"))
            else:
                dur = sum(_shot_dur(s) for s in flagged
                          if (s.source.params or {}).get("ai_stylized") is True)
                share_max = _eff(c, "plan.traits.ai_nonpixel_stylization.share_max",
                                 amendments, v)
                if share_max is not None and dur / total > share_max:
                    v.append(_err("style.contract.plan", "plan.traits.ai_nonpixel_stylization",
                                  f"AI 风格化非像素份额 {dur / total:.0%} > 上限 {share_max:.0%}"))

    # 声明型图形连续时长（MG 段与实拍段交替的可码判投影）
    if plan.get("graphics_run_max_s"):
        run_max = _eff(c, "plan.graphics_run_max_s", amendments, v)
        if run_max is not None:
            run_dur, run_ids = 0.0, []
            for s in shots + [None]:
                if s is not None and s.source.provider in DECLARED_GRAPHICS:
                    run_dur += _shot_dur(s)
                    run_ids.append(s.id)
                    continue
                if run_dur > run_max:
                    v.append(_err("style.contract.plan", f"shots[{run_ids[0]}]",
                                  f"声明型图形连续 {run_dur:.1f}s > 上限 {run_max:g}s"
                                  f"（{len(run_ids)} 镜）", evidence=" → ".join(run_ids)))
                run_dur, run_ids = 0.0, []
    return v


def style_contract_render(ir: FilmIR, ctx: GateContext | None = None) -> list[Violation]:
    """review 起：按成片实测证据终检合同——自报与实测矛盾时以实测为准。"""
    c, amendments = _load_contract(ir, ctx)
    if c is None or not c.get("render"):
        return []
    v: list[Violation] = []
    ev_file = Path(ctx.project_dir) / "evidence" / "render-metrics.json"
    if not ev_file.is_file():
        # 已出厂的历史片降 warn（证据可事后补测）；在产片是硬门
        make = _warn if ir.meta.status == "delivered" else _err
        return [make("style.contract.render", "evidence/render-metrics.json",
                     "缺成片实测证据——先跑 tools/measure-render.py <project>")]
    ev = json.loads(ev_file.read_text(encoding="utf-8"))

    static = ev.get("static") or {}
    hold = static.get("hold_ratio")
    hold_max = _eff(c, "render.static_hold_ratio_max", amendments, v)
    if hold is not None and hold_max is not None and hold > hold_max:
        v.append(_err("style.contract.render", "evidence.static.hold_ratio",
                      f"实测静态持有 {hold:.0%} > 上限 {hold_max:.0%}（幻灯片化，实测口径）",
                      evidence=f"hold_total_s={static.get('hold_total_s')}"))

    n_video = (ev.get("compose") or {}).get("video_elements")
    video_min = _eff(c, "render.min_video_elements", amendments, v)
    if n_video is not None and video_min is not None and n_video < video_min:
        v.append(_err("style.contract.render", "evidence.compose.video_elements",
                      f"compose 内 <video> 共 {n_video} 个 < 下限 {video_min:g}"
                      "——烘焙声部无物理存在"))

    # 自报 static_class=false 但实测判静的镜头（Goodhart 的直接解毒剂）
    measured = {p.get("id"): p for p in static.get("per_shot") or []}
    mislabeled = [s.id for s in ir.shots
                  if not s.static_class and measured.get(s.id, {}).get("measured_static")]
    if mislabeled:
        make = _err if len(mislabeled) >= MISLABEL_ERROR_MIN else _warn
        v.append(make("style.contract.render", "shots[].static_class",
                      f"{len(mislabeled)} 镜自报 static_class=false 但实测判静——以实测为准",
                      evidence=" ".join(mislabeled)))

    ev_dur = (ev.get("video") or {}).get("duration_s")
    if ev_dur is not None and ir.audio.timeline and \
            abs(ev_dur - ir.audio.timeline.duration_s) > EVIDENCE_STALE_S:
        v.append(_warn("style.contract.render", "evidence.video.duration_s",
                       f"证据视频时长 {ev_dur:.1f}s 与音频总长 "
                       f"{ir.audio.timeline.duration_s:.1f}s 差 >{EVIDENCE_STALE_S}s"
                       "——证据可能过期，重跑 measure-render"))
    return v


# ---------------------------------------------------------------- 注册表

# (gate_fn, 生效起点阶段)
REGISTRY: list[tuple] = [
    (refs_integrity, "brief"),
    (budget_guard, "brief"),
    (gen_traceability, "brief"),
    (commitment_duration, "audio"),
    (timeline_coverage, "storyboard"),
    (groups_arithmetic, "storyboard"),
    (slides_risk, "storyboard"),
    (visual_change, "storyboard"),
    (framing_repeat, "storyboard"),
    (motion_word, "storyboard"),
    (baked_evidence, "motion"),
    (edit_transitions, "compose"),
]

# 需要 GateContext（合同文件 / 成片证据）的门——无 project_dir 时静默跳过
CONTEXT_REGISTRY: list[tuple] = [
    (style_contract_plan, "storyboard"),
    (style_contract_render, "review"),
]


def run_gates(ir: FilmIR, stage: str | None = None,
              project_dir: str | Path | None = None) -> dict:
    """跑 G1 套件。stage 缺省用 meta.status——"验到目前为止该满足的一切"。"""
    stage = stage or ir.meta.status
    idx = _STAGE_INDEX.get(stage)
    if idx is None:
        idx = len(STAGES)
    violations: list[Violation] = []
    ran: list[str] = []
    for fn, from_stage in REGISTRY:
        if _STAGE_INDEX[from_stage] <= idx:
            ran.append(fn.__name__)
            violations.extend(fn(ir))
    ctx = GateContext(project_dir=Path(project_dir)) if project_dir else None
    if ctx is not None:
        for fn, from_stage in CONTEXT_REGISTRY:
            if _STAGE_INDEX[from_stage] <= idx:
                ran.append(fn.__name__)
                violations.extend(fn(ir, ctx))
    errors = [x for x in violations if x.severity == "error"]
    warns = [x for x in violations if x.severity == "warn"]
    return {
        "ok": not errors,
        "stage": stage,
        "gates_ran": ran,
        "errors": len(errors),
        "warnings": len(warns),
        "violations": [x.to_dict() for x in violations],
    }
