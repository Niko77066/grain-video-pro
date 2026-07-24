"""film.json 的载入 / 原子写 / 文件锁。状态从文件读（铁律 4）。"""

from __future__ import annotations

import fcntl
import json
import os
from contextlib import contextmanager
from pathlib import Path

from pydantic import ValidationError

from .errors import IRError, MIGRATION_NEEDED, NOT_FOUND, SCHEMA_INVALID
from .models import FilmIR


class Project:
    """一个片子项目的句柄。path 接受项目目录或 film.json 本身。"""

    def __init__(self, path: str | Path):
        p = Path(path)
        # 显式 .json 路径当文件；其余一律当项目目录（目录可以尚不存在——ir_new 会建）
        self.file = p if p.suffix == ".json" else p / "film.json"
        self.dir = self.file.parent

    def exists(self) -> bool:
        return self.file.is_file()

    def load_raw(self) -> dict:
        if not self.exists():
            raise IRError(NOT_FOUND, f"找不到 film.json: {self.file}")
        with open(self.file, encoding="utf-8") as f:
            return json.load(f)

    def load(self) -> FilmIR:
        raw = self.load_raw()
        meta = raw.get("meta") or {}
        if not meta.get("schema_version"):
            raise IRError(
                MIGRATION_NEEDED,
                f"{self.file} 缺 meta.schema_version（M0 旧格式）",
                hint="先跑 `kuleshov-ir migrate <project>` 收编到 m1-v1",
            )
        return validate_dict(raw)

    def save(self, ir: FilmIR) -> None:
        self.save_raw(ir.dump())

    def save_raw(self, data: dict) -> None:
        """原子写：tmp + rename。调用方保证 data 已过 schema。"""
        tmp = self.file.with_suffix(".json.tmp")
        with open(tmp, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
            f.write("\n")
        os.replace(tmp, self.file)

    @contextmanager
    def locked(self):
        """排他锁包住 read-modify-write（cron 与交互可能并发同一项目）。"""
        lock_path = self.file.with_suffix(".json.lock")
        lock_path.parent.mkdir(parents=True, exist_ok=True)
        with open(lock_path, "w") as lf:
            fcntl.flock(lf, fcntl.LOCK_EX)
            try:
                yield self
            finally:
                fcntl.flock(lf, fcntl.LOCK_UN)


def validate_dict(raw: dict) -> FilmIR:
    """dict → FilmIR，pydantic 错误translated成结构化 IRError。"""
    try:
        return FilmIR.model_validate(raw)
    except ValidationError as e:
        first = e.errors()[0]
        loc = ".".join(str(x) for x in first["loc"])
        raise IRError(
            SCHEMA_INVALID,
            f"schema 校验失败（共 {e.error_count()} 处）: {loc}: {first['msg']}",
            path=loc,
            hint="完整错误清单见 stderr detail 字段",
        ) from e
