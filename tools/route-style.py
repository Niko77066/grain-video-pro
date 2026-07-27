#!/usr/bin/env python3
"""route-style —— 风格包三层路由器（硬规则 + 打分 + 兜底）。

一句话原则：按「要让观众如何理解这条内容」路由，而不是只按「这是什么内容」路由。

三层输入：
  ① 内容类型   content_type          —— 缩小候选集，不单独决定风格包
  ② 表达目标   understanding_task / tone —— 理解任务是第一路由键，tone 是修正项
  ③ 受众与素材 audience / material / aspect / duration_s / sensitivity —— 硬规则的主要来源

三段逻辑：
  A. 硬规则排除：画幅、时长、必需素材、冲突素材、敏感题材。被排除的包给出理由，不静默丢弃。
  B. 能力卡打分：理解任务 > 内容类型 > 签名素材 > 语气/受众/节奏；avoid_when 命中扣分。
  C. 置信与兜底：给 Top 3 而不是硬选一个；最高分没命中理解任务、或分数不足 → 落兜底包。

用法：
  python3 tools/route-style.py --features f.json
  python3 tools/route-style.py --understanding-task verify_the_event --content-type breaking_news \\
      --aspect 9:16 --duration 30 --audience general --material readable_evidence --tone urgent,authoritative
  python3 tools/route-style.py --check          # 跑 styles/routing-cases.json 路由回归
  python3 tools/route-style.py --list           # 能力卡清单 + 理解任务覆盖矩阵（看空位）
  加 --json 输出机器可读结果（写进 ledger.decisions 用这个）。
"""

from __future__ import annotations

import argparse
import json
import sys
from dataclasses import dataclass, field
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
STYLES = REPO / "styles"
VOCAB_FILE = STYLES / "routing-vocab.json"
CASES_FILE = STYLES / "routing-cases.json"

CARD_SCHEMA = "style-capability@1"

# ------------------------------------------------------------------ 权重
W_TASK_PRIMARY = 45      # 理解任务是第一路由键，权重压过其它所有单项
W_TASK_SECONDARY = 22
W_CONTENT = 18
W_SIGNATURE_MATERIAL = 12
W_SIGNATURE_CAP = 24
W_PREFER = 4
W_PREFER_CAP = 12
W_TONE = 5
W_TONE_CAP = 15
W_AUDIENCE = 8
W_PACING = 6
W_AVOID = -30

# 画幅与时长是**适配成本**，不是准入门槛（2026-07-27 用户拍板）：包有原生格式
# （native_format，实证过的那一档），换画幅/换时长只扣分并输出「要改什么」，不排除。
W_FORMAT_ASPECT = -10
W_FORMAT_DUR_NEAR = -8     # 越出原生带宽但在 1.5× / 0.66× 之内
W_FORMAT_DUR_FAR = -18     # 越得更远（叙事骨架要重排，不只是收放）
FORMAT_STRETCH = 1.5       # near / far 的分界倍数

SCORE_MAX = (W_TASK_PRIMARY + W_CONTENT + W_SIGNATURE_CAP
             + W_PREFER_CAP + W_TONE_CAP + W_AUDIENCE + W_PACING)  # 128

FIT_HIGH = 60            # 高置信下限
FIT_MEDIUM = 45          # 中置信下限（低于此 → 兜底）
MARGIN_HIGH = 12         # 领先第二名不足这么多 → 降一档并标 tie


# ------------------------------------------------------------------ 词表

class VocabError(ValueError):
    pass


def load_vocab() -> dict:
    v = json.loads(VOCAB_FILE.read_text(encoding="utf-8"))
    if v.get("schema") != "routing-vocab@1":
        raise VocabError(f"{VOCAB_FILE} schema 不是 routing-vocab@1")
    return v


def _ordered_keys(vocab: dict, ns: str) -> list[str]:
    return [k for k in vocab[ns] if not k.startswith("_")]


def _keys(vocab: dict, ns: str) -> set[str]:
    return set(_ordered_keys(vocab, ns))


def _check_tags(tags, ns: str, vocab: dict, where: str) -> list[str]:
    allowed = _keys(vocab, ns)
    bad = [t for t in tags if t not in allowed]
    if bad:
        raise VocabError(
            f"{where}: 表外标签 {bad}（{ns} 合法值：{sorted(allowed)}）。"
            f"要新增标签就改 {VOCAB_FILE.relative_to(REPO)}，不许临时造词。")
    return list(tags)


# ------------------------------------------------------------------ 能力卡

@dataclass
class Card:
    id: str
    path: Path
    raw: dict

    @property
    def status(self) -> str:
        return self.raw.get("status", "candidate")

    @property
    def is_fallback(self) -> bool:
        return self.status == "fallback"

    @property
    def hard(self) -> dict:
        return self.raw.get("hard_rules", {}) or {}

    @property
    def native(self) -> dict:
        return self.raw.get("native_format", {}) or {}

    @property
    def materials(self) -> dict:
        return self.raw.get("material_requirements", {}) or {}

    def task(self, kind: str) -> list[str]:
        return (self.raw.get("understanding_task", {}) or {}).get(kind, []) or []


def load_cards(vocab: dict) -> list[Card]:
    cards: list[Card] = []
    missing: list[str] = []
    for d in sorted(STYLES.iterdir()):
        if not d.is_dir() or d.name.startswith("_"):
            continue
        f = d / "capability.json"
        if not f.is_file():
            missing.append(d.name)
            continue
        raw = json.loads(f.read_text(encoding="utf-8"))
        if raw.get("schema") != CARD_SCHEMA:
            raise VocabError(f"{f}: schema 不是 {CARD_SCHEMA}")
        if raw.get("id") != d.name:
            raise VocabError(f"{f}: id={raw.get('id')!r} 与目录名 {d.name!r} 不一致")
        cards.append(Card(id=d.name, path=f, raw=raw))
    if missing:
        raise VocabError(
            f"这些风格包没有 capability.json，路由器看不见它们：{missing}。"
            f"没有能力卡的包不许上线——补卡或移进 styles/_disabled/。")
    for c in cards:
        validate_card(c, vocab)
    return cards


def validate_card(c: Card, vocab: dict) -> None:
    w = f"{c.path.relative_to(REPO)}"
    r = c.raw
    if r.get("layer") not in _keys(vocab, "layer"):
        raise VocabError(f"{w}: layer={r.get('layer')!r} 不在词表")
    if r.get("status") not in _keys(vocab, "status"):
        raise VocabError(f"{w}: status={r.get('status')!r} 不在词表")
    _check_tags(c.task("primary"), "understanding_task", vocab, f"{w} understanding_task.primary")
    _check_tags(c.task("secondary"), "understanding_task", vocab, f"{w} understanding_task.secondary")
    _check_tags(r.get("applicable_content", []), "content_type", vocab, f"{w} applicable_content")
    _check_tags(r.get("audience", []), "audience", vocab, f"{w} audience")
    _check_tags(r.get("tone", []), "tone", vocab, f"{w} tone")
    _check_tags([r.get("pacing")], "pacing", vocab, f"{w} pacing")
    _check_tags(c.native.get("aspect", []), "aspect", vocab, f"{w} native_format.aspect")
    for grp in c.hard.get("requires_any", []):
        _check_tags(grp, "material", vocab, f"{w} hard_rules.requires_any")
    _check_tags(c.hard.get("excluded_material", []), "material", vocab, f"{w} hard_rules.excluded_material")
    _check_tags(c.hard.get("excluded_sensitivity", []), "sensitivity", vocab,
                f"{w} hard_rules.excluded_sensitivity")
    for k in ("signature", "prefers", "can_work_without"):
        _check_tags(c.materials.get(k, []), "material", vocab, f"{w} material_requirements.{k}")
    # avoid_when 跨命名空间：内容类型 / 语气 / 受众 / 素材 / 敏感度
    any_tag = set()
    for ns in ("content_type", "tone", "audience", "material", "sensitivity"):
        any_tag |= _keys(vocab, ns)
    bad = [t for t in r.get("avoid_when", []) if t not in any_tag]
    if bad:
        raise VocabError(f"{w} avoid_when: 表外标签 {bad}")
    dur = c.native.get("duration_s")
    if not (isinstance(dur, list) and len(dur) == 2 and dur[0] <= dur[1]):
        raise VocabError(f"{w} native_format.duration_s 必须是 [min, max]")
    for k in ("aspect", "duration_s"):
        if k in c.hard:
            raise VocabError(
                f"{w} hard_rules.{k}: 画幅与时长不是硬门（2026-07-27 拍板）——"
                f"挪到 native_format 并在 native_format.adaptation.{k} 写清换格式要改什么")
    adapt = c.native.get("adaptation", {}) or {}
    need = ("aspect", "duration_shorter", "duration_longer")
    if not c.is_fallback and not all(adapt.get(k) for k in need):
        raise VocabError(
            f"{w} native_format.adaptation 必须写齐 {need} 三条——"
            f"路由器把它原样打给 EP 当施工说明，缺了就等于静默降级")


# ------------------------------------------------------------------ 输入

@dataclass
class Features:
    topic: str = ""
    content_type: str = "other"
    understanding_task: str = "unknown"
    tone: list[str] = field(default_factory=list)
    audience: list[str] = field(default_factory=list)
    material: list[str] = field(default_factory=list)
    sensitivity: str = "none"
    aspect: str = ""
    duration_s: float | None = None
    pacing: str = ""

    @property
    def derived_pacing(self) -> str:
        if self.pacing:
            return self.pacing
        if self.duration_s is None:
            return ""
        if self.duration_s <= 45:
            return "fast"
        if self.duration_s <= 150:
            return "medium"
        return "slow"

    def active_tags(self) -> set[str]:
        t = {self.content_type, *self.tone, *self.audience, *self.material}
        if self.sensitivity and self.sensitivity != "none":
            t.add(self.sensitivity)
        return t


def _as_list(v) -> list[str]:
    if v is None:
        return []
    if isinstance(v, str):
        return [x.strip() for x in v.split(",") if x.strip()]
    return list(v)


def parse_features(d: dict, vocab: dict) -> Features:
    f = Features(
        topic=d.get("topic", "") or "",
        content_type=d.get("content_type") or "other",
        understanding_task=d.get("understanding_task") or "unknown",
        tone=_as_list(d.get("tone")),
        audience=_as_list(d.get("audience")),
        material=_as_list(d.get("material")),
        sensitivity=d.get("sensitivity") or "none",
        aspect=d.get("aspect") or "",
        duration_s=d.get("duration_s"),
        pacing=d.get("pacing") or "",
    )
    where = "路由输入"
    _check_tags([f.content_type], "content_type", vocab, where)
    _check_tags([f.understanding_task], "understanding_task", vocab, where)
    _check_tags(f.tone, "tone", vocab, where)
    _check_tags(f.audience, "audience", vocab, where)
    _check_tags(f.material, "material", vocab, where)
    _check_tags([f.sensitivity], "sensitivity", vocab, where)
    if f.aspect:
        _check_tags([f.aspect], "aspect", vocab, where)
    if f.pacing:
        _check_tags([f.pacing], "pacing", vocab, where)
    if "presenter_wanted" in f.material and "presenter_declined" in f.material:
        raise VocabError("路由输入: presenter_wanted 与 presenter_declined 互斥，只能给一个")
    return f


# ------------------------------------------------------------------ A. 硬规则

def hard_gate(c: Card, f: Features) -> list[str]:
    """返回排除理由列表；空列表 = 通过。

    只有「配方本身不成立」的条件进这里：必需素材、冲突素材、敏感题材。
    画幅与时长**不在这里**——它们是适配成本，走 format_cost()。
    """
    out: list[str] = []
    h = c.hard
    have = set(f.material)
    for grp in h.get("requires_any", []):
        if not (have & set(grp)):
            out.append(f"缺必需素材：{' 或 '.join(grp)} 至少要有一项")
    for m in h.get("excluded_material", []):
        if m in have:
            out.append(f"素材条件冲突：{m}")
    if f.sensitivity in h.get("excluded_sensitivity", []):
        out.append(f"敏感题材不适用：{f.sensitivity}")
    return out


def format_cost(c: Card, f: Features) -> tuple[int, list[dict]]:
    """画幅/时长偏离原生格式的代价。返回 (扣分, 适配说明列表)。

    不排除任何包——输出的 adaptation 文本是给 EP 的施工说明：
    换格式要改什么版式、砍/加什么结构。EP 必须把它记进 ledger.decisions。
    """
    penalty = 0
    adapt: list[dict] = []
    nat = c.native
    notes = nat.get("adaptation", {}) or {}

    aspects = nat.get("aspect", [])
    if f.aspect and aspects and f.aspect not in aspects:
        penalty += W_FORMAT_ASPECT
        adapt.append({
            "field": "aspect",
            "native": aspects,
            "requested": f.aspect,
            "cost": W_FORMAT_ASPECT,
            "todo": notes.get("aspect", "（能力卡未写换画幅的施工说明——补上）"),
        })

    lo, hi = nat.get("duration_s", [0, 10 ** 6])
    if f.duration_s is not None and not (lo <= f.duration_s <= hi):
        if f.duration_s < lo:
            far = f.duration_s < lo / FORMAT_STRETCH
            direction = f"短于原生下限 {lo:g}s"
            note = notes.get("duration_shorter")
        else:
            far = f.duration_s > hi * FORMAT_STRETCH
            direction = f"长于原生上限 {hi:g}s"
            note = notes.get("duration_longer")
        cost = W_FORMAT_DUR_FAR if far else W_FORMAT_DUR_NEAR
        penalty += cost
        adapt.append({
            "field": "duration_s",
            "native": [lo, hi],
            "requested": f.duration_s,
            "cost": cost,
            "degree": "far" if far else "near",
            "todo": (f"{direction}（{'重排叙事骨架' if far else '收放章节'}）："
                     + (note or "（能力卡未写变时长的施工说明——补上）")),
        })
    return penalty, adapt


# ------------------------------------------------------------------ B. 打分

@dataclass
class Scored:
    card: Card
    score: int
    fit: int
    task_hit: str            # primary | secondary | ""
    matched: list[str]
    missed: list[str]
    penalties: list[str]
    adaptations: list[dict] = field(default_factory=list)


def score_card(c: Card, f: Features) -> Scored:
    s = 0
    matched: list[str] = []
    missed: list[str] = []
    penalties: list[str] = []

    task_hit = ""
    if f.understanding_task != "unknown":
        if f.understanding_task in c.task("primary"):
            s += W_TASK_PRIMARY
            task_hit = "primary"
            matched.append(f"理解任务·主位「{f.understanding_task}」")
        elif f.understanding_task in c.task("secondary"):
            s += W_TASK_SECONDARY
            task_hit = "secondary"
            matched.append(f"理解任务·次位「{f.understanding_task}」")
        else:
            missed.append(f"不承担理解任务「{f.understanding_task}」")
    else:
        missed.append("理解任务未判定")

    if f.content_type in c.raw.get("applicable_content", []):
        s += W_CONTENT
        matched.append(f"内容类型 {f.content_type}")
    else:
        missed.append(f"内容类型 {f.content_type} 不在适用清单")

    have = set(f.material)
    sig = [m for m in c.materials.get("signature", []) if m in have]
    if sig:
        s += min(len(sig) * W_SIGNATURE_MATERIAL, W_SIGNATURE_CAP)
        matched.append("签名素材 " + "+".join(sig))
    sig_missing = [m for m in c.materials.get("signature", []) if m not in have]
    if sig_missing:
        missed.append("无签名素材 " + "/".join(sig_missing))

    pref = [m for m in c.materials.get("prefers", []) if m in have]
    if pref:
        s += min(len(pref) * W_PREFER, W_PREFER_CAP)
        matched.append("加分素材 " + "+".join(pref))

    tones = [t for t in f.tone if t in c.raw.get("tone", [])]
    if tones:
        s += min(len(tones) * W_TONE, W_TONE_CAP)
        matched.append("语气 " + "+".join(tones))

    if any(a in c.raw.get("audience", []) for a in f.audience):
        s += W_AUDIENCE
        matched.append("受众 " + "+".join(f.audience))
    elif f.audience:
        missed.append("受众 " + "+".join(f.audience) + " 不在适用清单")

    dp = f.derived_pacing
    if dp and dp == c.raw.get("pacing"):
        s += W_PACING
        matched.append(f"节奏 {dp}")
    elif dp:
        missed.append(f"节奏 {dp} ≠ 本包 {c.raw.get('pacing')}")

    for t in c.raw.get("avoid_when", []):
        if t in f.active_tags():
            s += W_AVOID
            penalties.append(f"avoid_when 命中 {t}")

    fcost, adaptations = format_cost(c, f)
    s += fcost
    for a in adaptations:
        penalties.append(
            f"格式适配 {a['field']}：原生 {a['native']} → 要 {a['requested']}（{a['cost']}）")

    fit = round(100 * max(s, 0) / SCORE_MAX)
    return Scored(card=c, score=s, fit=fit, task_hit=task_hit,
                  matched=matched, missed=missed, penalties=penalties,
                  adaptations=adaptations)


# ------------------------------------------------------------------ C. 路由

def route(f: Features, cards: list[Card]) -> dict:
    fallbacks = [c for c in cards if c.is_fallback]
    contenders = [c for c in cards if not c.is_fallback]
    if not fallbacks:
        raise VocabError("styles/ 下没有 status=fallback 的兜底包——路由没有下限保底，拒绝出结果")
    fb = fallbacks[0]

    excluded, survivors = [], []
    for c in contenders:
        reasons = hard_gate(c, f)
        if reasons:
            excluded.append({"id": c.id, "reasons": reasons})
        else:
            survivors.append(score_card(c, f))
    survivors.sort(key=lambda x: (-x.score, x.card.id))

    top = survivors[0] if survivors else None
    runner = survivors[1] if len(survivors) > 1 else None
    margin = (top.fit - runner.fit) if (top and runner) else (100 if top else 0)
    lead = (f"领先第二名 {runner.card.id} {margin} 分" if runner
            else "是唯一配方成立的专用包")

    # 空位：这个理解任务全仓库没有包认领（连被硬规则排掉的都不认领）
    gap = None
    if f.understanding_task != "unknown":
        claimers = [c.id for c in contenders if f.understanding_task in c.task("primary")]
        if not claimers:
            gap = (f"理解任务「{f.understanding_task}」当前无包认领（空位）——"
                   f"落兜底包出片，并把这条记进 routing.md §7 空位表")

    tie = bool(top and runner and margin < MARGIN_HIGH)

    if top is None:
        confidence, reason = "low", "所有专用包的配方前提都不成立（见 excluded）"
    elif not top.task_hit:
        confidence = "low"
        reason = (f"最高分 {top.card.id} 没有承担理解任务"
                  f"「{f.understanding_task}」——按一句话原则，这不算命中")
    elif top.fit < FIT_MEDIUM:
        confidence, reason = "low", f"最高分 {top.card.id} 契合度仅 {top.fit}，低于 {FIT_MEDIUM}"
    elif top.fit < FIT_HIGH or tie or top.adaptations:
        confidence = "medium"
        if tie:
            tail = f"，仅领先 {runner.card.id} {margin} 分"
        elif top.adaptations:
            tail = ("，且要做格式适配（"
                    + "、".join(a["field"] for a in top.adaptations) + "）——适配项必须记 ledger")
        else:
            tail = "，未到高置信线"
        reason = f"{top.card.id} 契合度 {top.fit}{tail}"
    else:
        confidence, reason = "high", f"{top.card.id} 契合度 {top.fit}，{lead}"

    use_fallback = confidence == "low"
    chosen = fb.id if use_fallback else top.card.id
    chosen_card = fb if use_fallback else top.card

    ranked = [{
        "id": s.card.id,
        "status": s.card.status,
        "layer": s.card.raw.get("layer"),
        "positioning": s.card.raw.get("positioning"),
        "score": s.score,
        "fit": s.fit,
        "task_hit": s.task_hit,
        "matched": s.matched,
        "missed": s.missed,
        "penalties": s.penalties,
        "adaptations": s.adaptations,
    } for s in survivors[:3]]

    adaptations = [] if use_fallback else top.adaptations
    if use_fallback:
        why = f"落兜底包 {fb.id}：{reason}。兜底保下限，不承担用户可感知的风格承诺。"
    else:
        why = f"选 {chosen}（{chosen_card.raw.get('positioning')}）：{'；'.join(top.matched[:3])}。{reason}。"

    return {
        "schema": "style-routing@1",
        "input": {
            "topic": f.topic,
            "content_type": f.content_type,
            "understanding_task": f.understanding_task,
            "tone": f.tone,
            "audience": f.audience,
            "material": f.material,
            "sensitivity": f.sensitivity,
            "aspect": f.aspect,
            "duration_s": f.duration_s,
            "pacing_derived": f.derived_pacing,
        },
        "recommendation": {
            "narrative_base": chosen,
            "visual_skin": None,
            "layer": chosen_card.raw.get("layer"),
            "status": chosen_card.status,
            "confidence": confidence,
            "fallback_used": use_fallback,
            "tie": tie,
            "adaptations": adaptations,
            "reason": why,
        },
        "ranked": ranked,
        "fallback": {"id": fb.id, "role": "兜底（不参与竞争打分）"},
        "excluded": excluded,
        "gap": gap,
    }


# ------------------------------------------------------------------ 输出

def render_text(res: dict) -> str:
    L: list[str] = []
    i = res["input"]
    L.append(f"输入：{i['topic'] or '(未命名)'}")
    L.append(f"  ① 内容类型 {i['content_type']}")
    L.append(f"  ② 理解任务 {i['understanding_task']} / 语气 {'+'.join(i['tone']) or '—'}")
    dur = f"{i['duration_s']:g}s" if i["duration_s"] is not None else "时长未定"
    L.append(f"  ③ 受众 {'+'.join(i['audience']) or '—'} · {i['aspect'] or '画幅未定'} · {dur}"
             f" · 节奏 {i['pacing_derived'] or '—'} · 敏感度 {i['sensitivity']}")
    L.append(f"  素材 {'+'.join(i['material']) or '（未声明）'}")
    L.append("")
    r = res["recommendation"]
    flag = " [兜底]" if r["fallback_used"] else (" [并列]" if r["tie"] else "")
    L.append(f"→ 推荐：{r['narrative_base']}（{r['status']}，置信 {r['confidence']}）{flag}")
    L.append(f"  {r['reason']}")
    if r["adaptations"]:
        L.append("")
        L.append("  格式适配（不是拦截，是施工说明——原样记进 ledger.decisions）：")
        for a in r["adaptations"]:
            L.append(f"   · {a['field']}：原生 {a['native']} → 本片 {a['requested']}")
            L.append(f"     {a['todo']}")
    L.append("")
    if res["ranked"]:
        L.append("候选（Top 3，按契合度）：")
        for n, c in enumerate(res["ranked"], 1):
            L.append(f"  {n}. {c['id']:<22} fit {c['fit']:>3}  {c['positioning']}")
            if c["matched"]:
                L.append(f"     命中 {'；'.join(c['matched'])}")
            if c["missed"]:
                L.append(f"     未中 {'；'.join(c['missed'])}")
            if c["penalties"]:
                L.append(f"     扣分 {'；'.join(c['penalties'])}")
    else:
        L.append("候选：无（专用包全部被硬规则排除）")
    L.append(f"  兜底 {res['fallback']['id']}（{res['fallback']['role']}）")
    if res["excluded"]:
        L.append("")
        L.append("配方前提不成立（硬规则排除，与画幅/时长无关）：")
        for e in res["excluded"]:
            L.append(f"  ✗ {e['id']}：{'；'.join(e['reasons'])}")
    if res["gap"]:
        L.append("")
        L.append(f"⚠ 空位：{res['gap']}")
    return "\n".join(L)


def render_list(cards: list[Card], vocab: dict) -> str:
    L = ["风格包能力卡：", ""]
    for c in sorted(cards, key=lambda x: (x.is_fallback, x.id)):
        h, n = c.hard, c.native
        L.append(f"  {c.id}  [{c.raw.get('layer')} · {c.status}]  {c.raw.get('positioning')}")
        L.append(f"    理解任务 主{c.task('primary') or '—'} 次{c.task('secondary') or '—'}")
        L.append(f"    硬规则   必需{h.get('requires_any') or '—'} 排斥{h.get('excluded_material') or '—'}")
        L.append(f"    原生格式 画幅{n.get('aspect')} 时长{n.get('duration_s')}"
                 f"（偏离只扣分 + 出施工说明，不排除）")
        L.append("")
    L.append("理解任务覆盖矩阵（空位 = 未来该补的包）：")
    for task in _ordered_keys(vocab, "understanding_task"):
        if task == "unknown":
            continue
        prim = [c.id for c in cards if task in c.task("primary")]
        sec = [c.id for c in cards if task in c.task("secondary")]
        mark = "✓" if prim else "✗ 空位"
        L.append(f"  {mark:<7} {task:<26} 主：{'/'.join(prim) or '—':<28} 次：{'/'.join(sec) or '—'}")
    return "\n".join(L)


# ------------------------------------------------------------------ 回归

def run_check(cards: list[Card], vocab: dict) -> int:
    if not CASES_FILE.is_file():
        print(f"缺 {CASES_FILE.relative_to(REPO)}", file=sys.stderr)
        return 2
    data = json.loads(CASES_FILE.read_text(encoding="utf-8"))
    cases = data.get("cases", [])
    fails = 0
    for case in cases:
        f = parse_features(case["features"], vocab)
        res = route(f, cards)
        got = res["recommendation"]["narrative_base"]
        got_conf = res["recommendation"]["confidence"]
        want = case["expect"]["narrative_base"]
        want_conf = case["expect"].get("confidence")
        want_gap = case["expect"].get("gap")
        want_tie = case["expect"].get("tie")
        bad = []
        if got != want:
            bad.append(f"包 want={want} got={got}")
        if want_conf and got_conf != want_conf:
            bad.append(f"置信 want={want_conf} got={got_conf}")
        if want_gap is not None and bool(res["gap"]) != bool(want_gap):
            bad.append(f"空位 want={bool(want_gap)} got={bool(res['gap'])}")
        if want_tie is not None and bool(res["recommendation"]["tie"]) != bool(want_tie):
            bad.append(f"并列 want={bool(want_tie)} got={res['recommendation']['tie']}")
        want_adapt = case["expect"].get("adaptations")
        if want_adapt is not None:
            got_adapt = sorted(a["field"] for a in res["recommendation"]["adaptations"])
            if got_adapt != sorted(want_adapt):
                bad.append(f"格式适配 want={sorted(want_adapt)} got={got_adapt}")
        if bad:
            fails += 1
            print(f"FAIL {case['id']} — {case['features'].get('topic','')}")
            for b in bad:
                print(f"     {b}")
            print(f"     {res['recommendation']['reason']}")
        else:
            ad = ",".join(a["field"] for a in res["recommendation"]["adaptations"])
            print(f"ok   {case['id']:<10} → {got:<22} ({got_conf})"
                  + (f"  [适配 {ad}]" if ad else "")
                  + ("  [空位]" if res["gap"] else ""))
    print(f"\n{len(cases) - fails}/{len(cases)} 通过")
    return 1 if fails else 0


# ------------------------------------------------------------------ CLI

def main(argv=None) -> int:
    p = argparse.ArgumentParser(description="风格包三层路由（硬规则 + 打分 + 兜底）")
    p.add_argument("--features", type=Path, help="路由输入 JSON 文件")
    p.add_argument("--topic", default="")
    p.add_argument("--content-type", dest="content_type")
    p.add_argument("--understanding-task", dest="understanding_task")
    p.add_argument("--tone")
    p.add_argument("--audience")
    p.add_argument("--material")
    p.add_argument("--sensitivity")
    p.add_argument("--aspect")
    p.add_argument("--duration", dest="duration_s", type=float)
    p.add_argument("--pacing")
    p.add_argument("--json", action="store_true", help="输出 JSON（写 ledger.decisions 用这个）")
    p.add_argument("--check", action="store_true", help="跑 styles/routing-cases.json 回归")
    p.add_argument("--list", action="store_true", help="列能力卡与理解任务覆盖矩阵")
    a = p.parse_args(argv)

    try:
        vocab = load_vocab()
        cards = load_cards(vocab)
    except VocabError as e:
        print(f"能力卡/词表错误：{e}", file=sys.stderr)
        return 2

    if a.check:
        return run_check(cards, vocab)
    if a.list:
        print(render_list(cards, vocab))
        return 0

    d: dict = {}
    if a.features:
        d = json.loads(a.features.read_text(encoding="utf-8"))
    for k in ("topic", "content_type", "understanding_task", "tone", "audience",
              "material", "sensitivity", "aspect", "duration_s", "pacing"):
        v = getattr(a, k, None)
        if v not in (None, ""):
            d[k] = v
    if not d:
        p.print_help()
        return 2

    try:
        f = parse_features(d, vocab)
        res = route(f, cards)
    except VocabError as e:
        print(f"输入错误：{e}", file=sys.stderr)
        return 2

    print(json.dumps(res, ensure_ascii=False, indent=2) if a.json else render_text(res))
    return 0


if __name__ == "__main__":
    sys.exit(main())
