"""ir_migrate：M0 手写 film.json（五种方言）→ m1-v1 收编（DESIGN.md §2.4）。

方言语料：800v-thermal-runaway（voiceover 平铺、music.gen 字符串、seam 自由文本）、
samsung-health-ai-consent（overlays.range、source.group、provider heygen_avatar）、
estee-lauder-night（static_type、shot_ref/shot_refs/scope=all_shots、provider 变体）、
uk-argentina-feud（voiceover.engine 平铺、timeline 缺 duration_s、provider collage-broll-pixel、
ledger 条目无 id）、openai-78m-logs（anchors.gen 字符串、shots.qc 字符串、
edit.transitions 结构化条目、provider collage-broll、ledger 条目无 id）。

原则：只归一字段名与结构，不丢任何留痕——搬不动的键靠 extra=allow 原样保留。
"""

from __future__ import annotations

import copy
import re

from .models import SCHEMA_VERSION, STAGES
from .store import validate_dict

PROVIDER_MAP = {
    "image-motion": "image_motion",
    "heygen_avatar": "avatar",
    "stock_footage": "footage",
    "real_product_image": "footage",
    "collage-broll": "collage_broll",         # openai-78m 方言：拼贴 b-roll 混合通路
    "collage-broll-pixel": "collage_broll",   # uk-argentina 方言：同通路的像素改版（原名存 origin_provider）
}
ANCHOR_STATUS_MAP = {"captured": "acquired", "picked": "selected"}
_SEAM_PATTERNS = [
    (re.compile(r"^A|尾帧|续接|tail_relay"), "tail_relay"),
    (re.compile(r"^B|硬切|hard_cut"), "hard_cut"),
    (re.compile(r"^C|转场|擦除|transition|→MG|收尾"), "transition"),
]


def migrate(raw: dict) -> tuple[dict, list[str]]:
    """返回 (m1-v1 dict, 变更日志)。结尾全量 schema 校验，不过即抛。"""
    d = copy.deepcopy(raw)
    log: list[str] = []

    _meta(d, log)
    _voiceover(d, log)
    _music(d, log)
    _timeline(d, log)
    _anchors(d, log)
    _shots(d, log)
    _groups(d, log)
    _overlays(d, log)
    _edit(d, log)
    _ledger(d, log)

    validated = validate_dict(d)
    return validated.dump(), log


def _meta(d: dict, log: list[str]) -> None:
    meta = d.setdefault("meta", {})
    if meta.get("schema_version") != SCHEMA_VERSION:
        meta["schema_version"] = SCHEMA_VERSION
        log.append(f"meta.schema_version → {SCHEMA_VERSION}")
    # openai-78m 方言：no-lock 时长政策——commitment 只记 duration_actual_s，无 duration_s。
    # 不许让 schema 默认值 60 冒充承诺：no-lock 语义 = 承诺即音频自然时长。
    c = meta.get("commitment")
    if isinstance(c, dict) and "duration_s" not in c and isinstance(c.get("duration_actual_s"), (int, float)):
        c["duration_s"] = c["duration_actual_s"]
        log.append("meta.commitment.duration_s ← duration_actual_s（no-lock 方言：承诺=音频自然时长，原字段保留）")
    status = meta.get("status", "brief")
    if status not in (*STAGES, "delivered"):
        canonical = "delivered" if "deliver" in status else "brief"
        meta["status_original"] = status
        meta["status"] = canonical
        log.append(f"meta.status {status!r} → {canonical!r}（原值存 status_original）")


def _voiceover(d: dict, log: list[str]) -> None:
    vo = (d.get("audio") or {}).get("voiceover")
    if not isinstance(vo, dict):
        return
    # 800v 方言：生成留痕平铺在 voiceover 顶层
    if "gen" not in vo and "model" in vo:
        gen = {"model": vo.pop("model")}
        for src, dst in (("payload", "prompt_file"), ("gen_wallclock_s", "wallclock_s"),
                         ("duration_s", "duration_actual_s"), ("note", "note"),
                         ("response", "response"), ("format", "format"),
                         ("generated_once", "generated_once")):
            if src in vo:
                gen[dst] = vo.pop(src)
        if "voice_desc" in vo:
            vo["voice_profile"] = vo.pop("voice_desc")
        vo["gen"] = gen
        log.append("voiceover 平铺留痕 → gen 块（800v 方言）")
    # uk-argentina / openai 方言：engine + 参数平铺在 voiceover 顶层
    elif "gen" not in vo and "engine" in vo:
        gen = {"model": vo.pop("engine")}
        params = vo.pop("params") if isinstance(vo.get("params"), dict) else {}
        for k in ("voice", "speed", "emotion", "mode", "endpoint"):
            if k in vo:
                params[k] = vo.pop(k)
        if params:
            gen["params"] = params
        if "duration_actual_s" in vo:
            gen["duration_actual_s"] = vo.pop("duration_actual_s")
        vo["gen"] = gen
        log.append("voiceover 平铺留痕 → gen 块（engine 方言）")
    gen = vo.get("gen")
    _fix_gen(gen, "voiceover", log)
    if isinstance(gen, dict) and "voice_profile" in gen and "voice_profile" not in vo:
        vo["voice_profile"] = gen["voice_profile"]


def _music(d: dict, log: list[str]) -> None:
    music = (d.get("audio") or {}).get("music")
    if isinstance(music, dict):
        if isinstance(music.get("gen"), str):
            music["gen"] = {"model": "", "note": music["gen"]}
            log.append("music.gen 字符串 → gen 块（note 保留原文）")
        _fix_gen(music.get("gen"), "music", log)


def _timeline(d: dict, log: list[str]) -> None:
    """uk-argentina 方言：timeline 只记对齐方法与文件指针，缺 duration_s。

    只从**实测**音频时长回填（audio-first 铁律：真实时间戳，不按剧本估时）；
    找不到实测值就留空，让 schema 校验自己报——不猜。
    """
    audio = d.get("audio") or {}
    tl = audio.get("timeline")
    if not isinstance(tl, dict) or "duration_s" in tl:
        return
    vo = audio.get("voiceover") or {}
    gen = vo.get("gen") if isinstance(vo.get("gen"), dict) else {}
    for src, val in (("audio.voiceover.gen.duration_actual_s", gen.get("duration_actual_s")),
                     ("audio.voiceover.duration_actual_s", vo.get("duration_actual_s")),
                     ("audio.voiceover.duration_s", vo.get("duration_s"))):
        if isinstance(val, (int, float)):
            tl["duration_s"] = val
            tl["duration_s_source"] = f"迁移回填自 {src}（实测音频时长）"
            log.append(f"audio.timeline.duration_s ← {src}（{val}s，来源存 duration_s_source）")
            return


def _anchors(d: dict, log: list[str]) -> None:
    for a in d.get("anchors") or []:
        if "need" in a and "intent" not in a:
            a["intent"] = a.pop("need")
            log.append(f"anchors[{a.get('id')}].need → intent")
        st = a.get("status")
        if st in ANCHOR_STATUS_MAP:
            a["status"] = ANCHOR_STATUS_MAP[st]
            log.append(f"anchors[{a.get('id')}].status {st} → {a['status']}")
        if "picked_from" in a:
            note = a.get("note") or ""
            a["note"] = (note + f"；picked_from: {a.pop('picked_from')}").lstrip("；")
            log.append(f"anchors[{a.get('id')}].picked_from 并入 note")
        if isinstance(a.get("gen"), str):   # openai-78m 方言："模型, payload文件" 单行字符串
            a["gen"] = _gen_from_string(a["gen"])
            log.append(f"anchors[{a.get('id')}].gen 字符串 → gen 块（原文存 note）")
        _fix_gen(a.get("gen"), f"anchors[{a.get('id')}]", log)


def _shots(d: dict, log: list[str]) -> None:
    for s in d.get("shots") or []:
        sid = s.get("id")
        src = s.get("source") or {}
        prov = src.get("provider")
        if prov in PROVIDER_MAP:
            src["provider"] = PROVIDER_MAP[prov]
            src.setdefault("params", {})["origin_provider"] = prov
            log.append(f"shots[{sid}].source.provider {prov} → {src['provider']}")
        if "group" in src and not s.get("group_ref"):
            s["group_ref"] = src.pop("group")
            log.append(f"shots[{sid}].source.group → group_ref")
        if "static_type" in s and "static_class" not in s:
            s["static_class"] = bool(s.pop("static_type"))
            log.append(f"shots[{sid}].static_type → static_class")
        if isinstance(s.get("qc"), str):    # openai-78m 方言：qc 是一句人写结论
            s["qc"] = {"note": s["qc"]}
            log.append(f"shots[{sid}].qc 字符串 → {{note}} 块（原文保留）")
        if isinstance(s.get("gen"), str):
            s["gen"] = _gen_from_string(s["gen"])
            log.append(f"shots[{sid}].gen 字符串 → gen 块（原文存 note）")
        _fix_gen(s.get("gen"), f"shots[{sid}]", log)


def _groups(d: dict, log: list[str]) -> None:
    for g in d.get("shot_groups") or []:
        for key in ("seam_out", "seam_in"):
            val = g.get(key)
            if isinstance(val, str) and val not in ("tail_relay", "hard_cut", "transition", "none"):
                parsed = next((name for pat, name in _SEAM_PATTERNS if pat.search(val)), None)
                if parsed:
                    g[key] = parsed
                    note = g.get("seam_note") or ""
                    g["seam_note"] = (note + f"；{key}: {val}").lstrip("；")
                    log.append(f"shot_groups[{g.get('id')}].{key} 自由文本 → {parsed}（原文存 seam_note）")
        # 回填成员镜头的 group_ref
        shots_by_id = {s.get("id"): s for s in d.get("shots") or []}
        for sid in g.get("shots") or []:
            s = shots_by_id.get(sid)
            if s is not None and not s.get("group_ref"):
                s["group_ref"] = g.get("id")


def _overlays(d: dict, log: list[str]) -> None:
    for o in d.get("overlays") or []:
        oid = o.get("id")
        if "range" in o and "shot_range" not in o:
            r = o.pop("range")
            if isinstance(r, list) and len(r) == 1:
                r = [r[0], r[0]]
            o["shot_range"] = r
            log.append(f"overlays[{oid}].range → shot_range")
        if "shot_ref" in o and "shot_range" not in o:
            ref = o.pop("shot_ref")
            o["shot_range"] = [ref, ref]
            log.append(f"overlays[{oid}].shot_ref → shot_range")
        if o.get("scope") in ("all_shots", "all"):
            o["scope"] = "global"
            log.append(f"overlays[{oid}].scope → global")
        if "provider" in o and "source" not in o:
            o["source"] = o.pop("provider")
        if "spec" in o and "intent" not in o:
            o["intent"] = o["spec"]


def _edit(d: dict, log: list[str]) -> None:
    """openai-78m 方言：transitions 条目是 {type, usage} 结构化对象。

    归一为 uk-argentina 同款 "类型（用法）" 字符串（G1 转场词汇门按条目计数），
    原结构化条目原样存 transitions_detail。
    """
    edit = d.get("edit")
    if not isinstance(edit, dict):
        return
    trans = edit.get("transitions")
    if not (isinstance(trans, list) and any(isinstance(t, dict) for t in trans)):
        return
    edit.setdefault("transitions_detail", copy.deepcopy(trans))
    flat = []
    for t in trans:
        if isinstance(t, dict):
            label = str(t.get("type") or t.get("name") or t)
            if t.get("usage"):
                label += f"（{t['usage']}）"
            flat.append(label)
        else:
            flat.append(t)
    edit["transitions"] = flat
    log.append("edit.transitions 结构化条目 → 字符串（原文存 transitions_detail）")


def _ledger(d: dict, log: list[str]) -> None:
    ledger = d.get("ledger") or {}
    # uk-argentina / openai-78m 方言：ledger 条目无 id → 按序补机器 id（不动其余任何字段）
    for key, prefix in (("decisions", "dec"), ("costs", "cost"), ("gates", "gate")):
        items = ledger.get(key) or []
        existing = {it.get("id") for it in items if isinstance(it, dict) and it.get("id")}
        filled = 0
        for i, it in enumerate(items, 1):
            if not isinstance(it, dict) or it.get("id"):
                continue
            cand = f"{prefix}{i:02d}"
            while cand in existing:
                cand += "x"
            it["id"] = cand
            existing.add(cand)
            filled += 1
        if filled:
            log.append(f"ledger.{key} {filled} 条缺 id → 按序补 {prefix}NN")
    for c in ledger.get("costs") or []:
        if "req_id" in c and "request_id" not in c:
            c["request_id"] = c.pop("req_id")
            log.append(f"costs[{c.get('id')}].req_id → request_id")
        if "usd_est" in c and "cost_usd" not in c:
            c["cost_usd"] = c["usd_est"]
            log.append(f"costs[{c.get('id')}].usd_est → cost_usd（原键保留）")
    for dec in ledger.get("decisions") or []:
        if "reason" in dec and "why" not in dec:
            dec["why"] = dec.pop("reason")
            log.append(f"decisions[{dec.get('id')}].reason → why")
    for g in ledger.get("gates") or []:
        if "gate" in g and "check" not in g:
            g["check"] = g.pop("gate")
            log.append(f"gates[{g.get('id')}].gate → check")


def _gen_from_string(s: str) -> dict:
    """gen 单行字符串收编：能确定解析的（"模型, payload.json"）拆出 model/prompt_file，
    其余只进 note——原文永远整句保留，不猜。"""
    parts = [p.strip() for p in s.split(",", 1)]
    if len(parts) == 2 and parts[1].endswith(".json"):
        return {"model": parts[0], "prompt_file": parts[1], "note": s}
    return {"model": "", "note": s}


def _fix_gen(gen, owner: str, log: list[str]) -> None:
    if not isinstance(gen, dict):
        return
    if "model" not in gen and "engine" in gen:   # uk-argentina 方言：镜头 gen 用 engine 记模型名
        gen["model"] = gen.pop("engine")
        log.append(f"{owner}.gen.engine → model")
    if isinstance(gen.get("wallclock_s"), list):   # 多 take 数组（samsung 方言）
        takes = gen["wallclock_s"]
        gen["wallclock_s_each"] = takes
        gen["wallclock_s"] = round(sum(x for x in takes if isinstance(x, (int, float))), 1)
        log.append(f"{owner}.gen.wallclock_s 多 take 数组 → 求和（原值存 wallclock_s_each）")
    if "duration_probe_s" in gen and "duration_actual_s" not in gen:
        gen["duration_actual_s"] = gen["duration_probe_s"]
