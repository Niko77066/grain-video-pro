"""结构化错误：grain 侧按 code 分支，不 parse message。"""

from __future__ import annotations


class IRError(Exception):
    """所有 API 错误的载体。code 稳定可枚举，见 DESIGN.md §1.5。"""

    def __init__(self, code: str, message: str, *, path: str | None = None,
                 hint: str | None = None):
        super().__init__(message)
        self.code = code
        self.message = message
        self.path = path
        self.hint = hint

    def to_dict(self) -> dict:
        d = {"code": self.code, "message": self.message}
        if self.path:
            d["path"] = self.path
        if self.hint:
            d["hint"] = self.hint
        return d


# 稳定错误码清单（新增须记入 DESIGN.md）
SCHEMA_INVALID = "SCHEMA_INVALID"
GATED_FIELD = "GATED_FIELD"
LEDGER_IMMUTABLE = "LEDGER_IMMUTABLE"
NOT_FOUND = "NOT_FOUND"
BAD_SELECTOR = "BAD_SELECTOR"
BAD_OP = "BAD_OP"
ILLEGAL_TRANSITION = "ILLEGAL_TRANSITION"
RULE_ZERO = "RULE_ZERO"
NOT_IMPLEMENTED = "NOT_IMPLEMENTED"
ENGINE_FAILURE = "ENGINE_FAILURE"
MIGRATION_NEEDED = "MIGRATION_NEEDED"
CONFLICT = "CONFLICT"
