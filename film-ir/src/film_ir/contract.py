"""风格合同（style-contract@1）：加载、包名解析、带宽内生效值。

合同 = styles/<pack>/contract.json，是 playbook 散文硬约束的机器编译。
数值叶子形如 {"value": x, "amend": [lo, hi]}：生产 agent 只能经
meta.contract_amendments["<dotted.path>"] 在带宽内调整（ir patch 自动留痕），
越界即违约——母版文件生产期内只读（守卫钩）。
"""

from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Optional

SCHEMA = "style-contract@1"
_ASCEND_MAX = 5  # project_dir 向上找仓库根（含 styles/ 的目录）的层数上限


def find_styles_dir(project_dir: Path) -> Optional[Path]:
    p = project_dir.resolve()
    for _ in range(_ASCEND_MAX):
        cand = p / "styles"
        if cand.is_dir():
            return cand
        if p.parent == p:
            break
        p = p.parent
    return None


def resolve_pack_dir(style_pack: str, styles_dir: Path) -> Optional[Path]:
    """meta.style_pack 是散文（如 "case-file v3 案卷档案（…）"），
    取 styles/ 下目录名出现在其中的那个；多命中取最长目录名。"""
    if not style_pack:
        return None
    hits = [d for d in styles_dir.iterdir()
            if d.is_dir() and d.name and d.name in style_pack]
    if not hits:
        return None
    return max(hits, key=lambda d: len(d.name))


def load_contract(style_pack: str, project_dir: Path) -> Optional[dict]:
    """找不到 styles/、包目录或 contract.json 都返回 None——无合同的包不受此门约束。"""
    styles_dir = find_styles_dir(project_dir)
    if styles_dir is None:
        return None
    pack_dir = resolve_pack_dir(style_pack, styles_dir)
    if pack_dir is None:
        return None
    f = pack_dir / "contract.json"
    if not f.is_file():
        return None
    data = json.loads(f.read_text(encoding="utf-8"))
    if data.get("schema") != SCHEMA:
        return None
    return data


# ---------------------------------------------------------------- 生效值

@dataclass
class Resolved:
    """一个合同数值经 amendments 解析后的结果。"""
    value: float
    amended: bool = False
    out_of_bounds: bool = False   # 修改越出带宽（越界值不生效，退回原值）
    requested: Optional[float] = None


def _leaf(contract: dict, dotted: str) -> Optional[dict]:
    node: object = contract
    for key in dotted.split("."):
        if not isinstance(node, dict) or key not in node:
            return None
        node = node[key]
    if isinstance(node, dict) and "value" in node:
        return node
    return None


def effective(contract: dict, dotted: str, amendments: dict) -> Optional[Resolved]:
    """按 dotted 路径取生效值。amendments 键 = dotted 路径（不含前导 schema 等）。"""
    leaf = _leaf(contract, dotted)
    if leaf is None:
        return None
    base = float(leaf["value"])
    if dotted not in amendments:
        return Resolved(value=base)
    try:
        req = float(amendments[dotted])
    except (TypeError, ValueError):
        return Resolved(value=base, out_of_bounds=True, requested=None)
    lo, hi = (leaf.get("amend") or [base, base])[:2]
    if not (float(lo) <= req <= float(hi)):
        return Resolved(value=base, out_of_bounds=True, requested=req)
    return Resolved(value=req, amended=True, requested=req)


def unknown_amendments(contract: dict, amendments: dict) -> list[str]:
    """指向不存在/不可调叶子的修改键——防拿 amendments 当自由字段用。"""
    return [k for k in amendments if _leaf(contract, k) is None]
