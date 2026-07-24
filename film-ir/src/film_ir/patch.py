"""ir_patch：原子补丁组（DESIGN.md §1.2–1.4）。

安全性质全部按"语义 diff"强制，而不是按 op 路径字符串匹配——
无论 op 怎么写（整段 set、逐字段 set），最终新旧状态的对比说了算：

1. 门控字段变化必须带 revision（自动追加修订决策进 ledger）；
2. ledger 三数组只许追加（新数组必须以旧数组为前缀）；
3. 镜头状态转移合法性 + 留痕前置（qc_* 必须有 qc，generated 必须有 gen）。
"""

from __future__ import annotations

import copy
import json
import re
from dataclasses import dataclass, field
from datetime import date as _date

from .errors import (IRError, BAD_OP, GATED_FIELD, ILLEGAL_TRANSITION,
                     LEDGER_IMMUTABLE, NOT_FOUND)
from .store import validate_dict

# 门控字段（DESIGN.md §1.3）。audio.timeline 的条件门控见 _gated_prefixes()
GATED_ALWAYS = (
    "meta.commitment",
    "meta.budget.cap_usd",
    "meta.format",
    "meta.style_pack",
    "meta.aspect",
    "meta.pipeline_version",
)

# 镜头状态机（DESIGN.md §2.2）
SHOT_TRANSITIONS: dict[str, set[str]] = {
    "planned": {"sourced", "generated"},
    "sourced": {"generated", "qc_pass", "qc_fail", "redo"},
    "generated": {"qc_pass", "qc_fail", "redo"},
    "qc_fail": {"redo", "generated", "sourced"},
    "qc_pass": {"redo"},
    "redo": {"planned", "sourced", "generated"},
}

_MISSING = object()
_PATH_PART = re.compile(r"^(?P<key>[A-Za-z_][A-Za-z0-9_]*)(?:\[(?P<id>[^\]*?][^\]]*)\])?$")


@dataclass
class PatchResult:
    applied: int
    revision_decision_id: str | None = None
    changed_paths: list[str] = field(default_factory=list)


def _walk(data, path: str, *, create_leaf: bool = False):
    """返回 (parent_container, final_key)。final_key 是 dict 键或数组内 id 已解析的元素。

    只支持点路径 + [id]（补丁路径禁投影/过滤）。
    """
    parts = path.split(".")
    node = data
    for i, part in enumerate(parts):
        m = _PATH_PART.match(part.strip())
        if not m:
            raise IRError(BAD_OP, f"补丁路径片段不合法: {part!r}", path=path)
        key, id_ = m.group("key"), m.group("id")
        last = i == len(parts) - 1
        if not isinstance(node, dict):
            raise IRError(BAD_OP, f"路径中段不是对象: {'.'.join(parts[:i])}", path=path)
        if key not in node:
            if last and id_ is None and create_leaf:
                return node, key
            raise IRError(NOT_FOUND, f"路径不存在: {'.'.join(parts[:i + 1])}", path=path)
        if id_ is None:
            if last:
                return node, key
            node = node[key]
        else:
            arr = node[key]
            if not isinstance(arr, list):
                raise IRError(BAD_OP, f"{key} 不是数组，不能用 [id]", path=path)
            idx = next((j for j, x in enumerate(arr)
                        if isinstance(x, dict) and x.get("id") == id_), None)
            if idx is None:
                raise IRError(NOT_FOUND, f"id 不存在: {key}[{id_}]", path=path)
            if last:
                return arr, idx
            node = arr[idx]
    raise IRError(BAD_OP, f"空补丁路径", path=path)


def _get(data, dotted: str):
    node = data
    for part in dotted.split("."):
        if not isinstance(node, dict) or part not in node:
            return _MISSING
        node = node[part]
    return node


def _apply_one(data: dict, op: dict) -> str:
    kind = op.get("op")
    path = op.get("path")
    if not kind or not path:
        raise IRError(BAD_OP, f"op 需要 op 与 path 字段: {op}")
    if kind == "set":
        parent, key = _walk(data, path, create_leaf=True)
        parent[key] = copy.deepcopy(op.get("value"))
    elif kind == "append":
        parent, key = _walk(data, path)
        target = parent[key]
        if not isinstance(target, list):
            raise IRError(BAD_OP, f"append 目标不是数组: {path}", path=path)
        target.append(copy.deepcopy(op.get("value")))
    elif kind == "insert":
        parent, key = _walk(data, path)
        target = parent[key]
        if not isinstance(target, list):
            raise IRError(BAD_OP, f"insert 目标不是数组: {path}", path=path)
        value = copy.deepcopy(op.get("value"))
        anchor = op.get("after") or op.get("before")
        if anchor is None:
            target.insert(0 if op.get("before") is not None else len(target), value)
        else:
            idx = next((j for j, x in enumerate(target)
                        if isinstance(x, dict) and x.get("id") == anchor), None)
            if idx is None:
                raise IRError(NOT_FOUND, f"insert 锚 id 不存在: {anchor}", path=path)
            target.insert(idx + (1 if op.get("after") else 0), value)
    elif kind == "remove":
        parent, key = _walk(data, path)
        if isinstance(parent, list):
            parent.pop(key)
        else:
            del parent[key]
    else:
        raise IRError(BAD_OP, f"未知 op: {kind}（支持 set/append/insert/remove）")
    return path


def _gated_prefixes(old: dict) -> list[str]:
    gated = list(GATED_ALWAYS)
    if old.get("shots"):
        gated.append("audio.timeline")  # 分镜落地后时钟不许静默改（音频先行铁律）
    return gated


def _jeq(a, b) -> bool:
    return json.dumps(a, sort_keys=True, ensure_ascii=False) == \
           json.dumps(b, sort_keys=True, ensure_ascii=False)


def _check_ledger_append_only(old: dict, new: dict) -> None:
    for name in ("decisions", "costs", "gates"):
        o = (old.get("ledger") or {}).get(name) or []
        n = (new.get("ledger") or {}).get(name) or []
        if len(n) < len(o) or not all(_jeq(a, b) for a, b in zip(o, n)):
            raise IRError(
                LEDGER_IMMUTABLE,
                f"ledger.{name} 只许追加，不许改写/删除既有条目",
                path=f"ledger.{name}",
                hint='修正历史 = 追加新条目并带 supersedes: "<旧id>"',
            )


def _check_shot_transitions(old: dict, new: dict) -> None:
    old_by_id = {s["id"]: s for s in old.get("shots") or [] if isinstance(s, dict)}
    for s in new.get("shots") or []:
        if not isinstance(s, dict):
            continue
        sid, ns = s.get("id"), s.get("status", "planned")
        o = old_by_id.get(sid)
        if o is None:
            if ns not in ("planned", "sourced"):
                raise IRError(ILLEGAL_TRANSITION,
                              f"新镜头 {sid} 只能以 planned/sourced 入场（当前 {ns}）",
                              path=f"shots[{sid}].status")
        else:
            os_ = o.get("status", "planned")
            if ns != os_ and ns not in SHOT_TRANSITIONS.get(os_, set()):
                raise IRError(ILLEGAL_TRANSITION,
                              f"镜头 {sid} 非法状态转移: {os_} → {ns}",
                              path=f"shots[{sid}].status",
                              hint=f"{os_} 只能转向 {sorted(SHOT_TRANSITIONS.get(os_, set()))}")
        # 留痕前置：状态先于证据是伪造留痕
        if ns in ("qc_pass", "qc_fail") and not s.get("qc"):
            raise IRError(ILLEGAL_TRANSITION,
                          f"镜头 {sid} 置 {ns} 前必须先写 qc 结果（留痕不可事后补）",
                          path=f"shots[{sid}].qc")
        if ns == "generated" and not s.get("gen"):
            raise IRError(ILLEGAL_TRANSITION,
                          f"镜头 {sid} 置 generated 前必须回填 gen 留痕",
                          path=f"shots[{sid}].gen")


def _next_decision_id(new: dict) -> str:
    mx = 0
    for d in (new.get("ledger") or {}).get("decisions") or []:
        m = re.fullmatch(r"d(\d+)", str(d.get("id", "")))
        if m:
            mx = max(mx, int(m.group(1)))
    return f"d{mx + 1:02d}"


def apply_patch(old: dict, ops: list[dict], revision: dict | None = None,
                today: str | None = None) -> tuple[dict, PatchResult]:
    """全组成功或全组不写。返回 (新 dict, 结果摘要)；调用方负责落盘。"""
    new = copy.deepcopy(old)
    changed = [_apply_one(new, op) for op in ops]

    # 1. 门控字段
    def _diff(a, b) -> bool:
        if a is _MISSING or b is _MISSING:
            return not (a is _MISSING and b is _MISSING)
        return not _jeq(a, b)

    gated_hits = [p for p in _gated_prefixes(old) if _diff(_get(old, p), _get(new, p))]
    decision_id = None
    if gated_hits:
        if not revision or not revision.get("reason"):
            raise IRError(
                GATED_FIELD,
                f"门控字段被改动: {', '.join(gated_hits)}",
                path=gated_hits[0],
                hint='带 revision（--revision "理由"）走正式修订，或另立项目',
            )
        decision_id = _next_decision_id(new)
        entry = {
            "id": decision_id,
            "stage": str(new.get("meta", {}).get("status", "")),
            "date": today or _date.today().isoformat(),
            "decision": f"修订门控字段: {', '.join(gated_hits)}",
            "why": revision["reason"],
        }
        if revision.get("supersedes"):
            entry["supersedes"] = revision["supersedes"]
        new.setdefault("ledger", {}).setdefault("decisions", []).append(entry)

    # 2. ledger 只追加
    _check_ledger_append_only(old, new)
    # 3. 镜头状态机
    _check_shot_transitions(old, new)
    # 4. 全量 schema（不过则整组丢弃）
    validated = validate_dict(new)

    return validated.dump(), PatchResult(applied=len(ops),
                                         revision_decision_id=decision_id,
                                         changed_paths=changed)
