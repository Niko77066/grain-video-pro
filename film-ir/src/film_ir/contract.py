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


# ------------------------------------------------------------ 执法词表

# 校验器真正执法的合同条目（dotted 模式，`*` 匹配任意一段）。
#
# 合同格式是开放词表，校验器是闭合词表：写进 contract.json 却没有执法点的
# 条目会被静默忽略——那比不写更危险，它让作者、评委和用户都以为那里有一道
# 门。本表把执法面变成显式清单：新增指标必须同时改 gates.py 的读取点和这里。
#
# **本表只覆盖合同校验器**。kuleshov-lint、measure-render 的其他检查、G2 评委
# 都是独立的执法层，不在此列。因此 "enforced": false 的准确含义是"合同校验器
# 不执法这一条"，不等于"这一条没人管"——条目自己的 basis 应写明它归谁管。
# 在该条目上写 "enforced": false，schema 门降为 warn 而不是 error。
ENFORCED_TERMS: frozenset[str] = frozenset({
    "plan.voices.*.min_shots",
    "plan.provider_share.*.min",
    "plan.provider_share.*.max",
    "plan.traits.pixel_narrative.share_min",
    "plan.traits.ai_nonpixel_stylization.share_max",
    "plan.graphics_run_max_s",
    "plan.transitions_max",
    "render.static_hold_ratio_max",
    "render.min_video_elements",
    "render.palette_drift_max",
})


def _term_paths(contract: dict) -> list[str]:
    """合同里所有阈值条目的 dotted 路径。

    条目 = `plan` / `render` 下形如 {"value": x, ...} 的叶子。散文字段
    （basis / role / note）与配置字段（providers / protocol）不是条目。
    """
    out: list[str] = []

    def walk(node: object, path: str) -> None:
        if not isinstance(node, dict):
            return
        if "value" in node:
            out.append(path)
            return
        for key, sub in node.items():
            walk(sub, f"{path}.{key}")

    for section in ("plan", "render"):
        walk(contract.get(section), section)
    return out


def _matches(path: str, pattern: str) -> bool:
    a, b = path.split("."), pattern.split(".")
    return len(a) == len(b) and all(q == "*" or p == q for p, q in zip(a, b))


def unenforced_terms(contract: dict) -> tuple[list[str], list[str]]:
    """区分两种没有机器执法的条目。

    返回 (dead, declared)：
    - dead——不在 ENFORCED_TERMS 里、也没自称声明性。这是装饰条款，报 error。
    - declared——显式写了 "enforced": false，作者知道它交 Judge 兜底，报 warn。
    """
    dead: list[str] = []
    declared: list[str] = []
    for path in _term_paths(contract):
        if any(_matches(path, pat) for pat in ENFORCED_TERMS):
            continue
        leaf = _leaf(contract, path) or {}
        (declared if leaf.get("enforced") is False else dead).append(path)
    return dead, declared
