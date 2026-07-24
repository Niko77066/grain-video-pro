"""选择器（DESIGN.md §1.1，刻意小）。

    meta.status                # 点路径
    shots[s03].gen             # id 寻址（id-keyed 数组一律用 id）
    shots[*].status            # 投影
    shots[?status=qc_fail]     # 等值过滤

在 dict（FilmIR.dump() 产物）上求值。
"""

from __future__ import annotations

import re
from dataclasses import dataclass

from .errors import IRError, BAD_SELECTOR, NOT_FOUND

_TOKEN = re.compile(r"""
    (?P<key>[A-Za-z_][A-Za-z0-9_]*)
    (?:\[(?P<bracket>[^\]]+)\])?
""", re.VERBOSE)


@dataclass
class Step:
    key: str
    by_id: str | None = None      # [some_id]
    all: bool = False             # [*]
    filt: tuple[str, str] | None = None  # [?field=value]


def parse(selector: str) -> list[Step]:
    steps: list[Step] = []
    for part in selector.split("."):
        m = _TOKEN.fullmatch(part.strip())
        if not m:
            raise IRError(BAD_SELECTOR, f"选择器片段不合法: {part!r}", path=selector)
        step = Step(key=m.group("key"))
        b = m.group("bracket")
        if b is not None:
            b = b.strip()
            if b == "*":
                step.all = True
            elif b.startswith("?"):
                if "=" not in b:
                    raise IRError(BAD_SELECTOR, f"过滤器需要 field=value: {part!r}", path=selector)
                field, value = b[1:].split("=", 1)
                step.filt = (field.strip(), value.strip())
            else:
                step.by_id = b
        steps.append(step)
    if not steps:
        raise IRError(BAD_SELECTOR, "空选择器")
    return steps


def _index_by_id(arr: list, id_: str, path: str):
    for item in arr:
        if isinstance(item, dict) and item.get("id") == id_:
            return item
    raise IRError(NOT_FOUND, f"id 不存在: {path}[{id_}]", path=path)


def resolve(data: dict, selector: str):
    """求值。投影/过滤后续以列表继续。"""
    steps = parse(selector)
    current: list = [data]      # 始终维护候选集合；fan 表示是否已进入投影语义
    fan = False
    trail = ""
    for step in steps:
        trail = f"{trail}.{step.key}" if trail else step.key
        nxt = []
        for node in current:
            if not isinstance(node, dict) or step.key not in node:
                raise IRError(NOT_FOUND, f"路径不存在: {trail}", path=trail)
            val = node[step.key]
            if step.by_id is not None:
                if not isinstance(val, list):
                    raise IRError(BAD_SELECTOR, f"{trail} 不是数组，不能用 [id]", path=trail)
                nxt.append(_index_by_id(val, step.by_id, trail))
            elif step.all:
                if not isinstance(val, list):
                    raise IRError(BAD_SELECTOR, f"{trail} 不是数组，不能用 [*]", path=trail)
                nxt.extend(val)
                fan = True
            elif step.filt:
                if not isinstance(val, list):
                    raise IRError(BAD_SELECTOR, f"{trail} 不是数组，不能用 [?…]", path=trail)
                f, v = step.filt
                nxt.extend(x for x in val if isinstance(x, dict) and str(x.get(f)) == v)
                fan = True
            else:
                nxt.append(val)
        current = nxt
    return current if fan else current[0]
