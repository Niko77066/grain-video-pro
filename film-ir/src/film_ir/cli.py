"""kuleshov-ir CLI。stdout 的 JSON 即 grain 集成契约（DESIGN.md §0）。

退出码：0 成功；1 校验/门禁不过；2 用法/寻址错误；3 引擎执行失败。
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

import click

from . import api
from .errors import (IRError, BAD_OP, BAD_SELECTOR, CONFLICT, ENGINE_FAILURE,
                     MIGRATION_NEEDED, NOT_FOUND, NOT_IMPLEMENTED)

_EXIT_USAGE = {NOT_FOUND, BAD_SELECTOR, BAD_OP, MIGRATION_NEEDED, CONFLICT}
_EXIT_ENGINE = {ENGINE_FAILURE, NOT_IMPLEMENTED}


def _emit(data) -> None:
    click.echo(json.dumps(data, ensure_ascii=False, indent=2))


def _fail(e: IRError) -> None:
    click.echo(json.dumps(e.to_dict(), ensure_ascii=False, indent=2), err=True)
    if e.code in _EXIT_USAGE:
        sys.exit(2)
    sys.exit(3 if e.code in _EXIT_ENGINE else 1)


@click.group()
def main() -> None:
    """Kuleshov Film IR API — film.json 的受管读写、G1 硬门与执行入口。"""


@main.command()
@click.argument("project", type=click.Path(exists=True))
@click.argument("selector")
def read(project: str, selector: str) -> None:
    """按选择器读 IR：meta.status / shots[s03].gen / shots[?status=qc_fail]"""
    try:
        _emit(api.ir_read(project, selector))
    except IRError as e:
        _fail(e)


@main.command()
@click.argument("project", type=click.Path(exists=True))
@click.option("--op", "ops_json", multiple=True, help='单个 op 的 JSON，可重复')
@click.option("--ops-file", type=click.Path(exists=True), help="ops 数组 JSON 文件；- 读 stdin 用 --stdin")
@click.option("--stdin", "from_stdin", is_flag=True, help="从 stdin 读 ops 数组 JSON")
@click.option("--revision", help="门控字段修订理由（自动追加决策进 ledger）")
@click.option("--supersedes", help="被本次修订取代的决策 id")
def patch(project: str, ops_json: tuple[str, ...], ops_file: str | None,
          from_stdin: bool, revision: str | None, supersedes: str | None) -> None:
    """原子补丁组：全组成功或全组不写。"""
    try:
        ops: list[dict] = [json.loads(x) for x in ops_json]
        if ops_file:
            ops.extend(json.loads(Path(ops_file).read_text(encoding="utf-8")))
        if from_stdin:
            ops.extend(json.loads(sys.stdin.read()))
        if not ops:
            raise IRError(BAD_OP, "没有可应用的 op（--op / --ops-file / --stdin 三选一）")
        rev = {"reason": revision, "supersedes": supersedes} if revision else None
        _emit(api.ir_patch(project, ops, rev))
    except json.JSONDecodeError as e:
        _fail(IRError(BAD_OP, f"op JSON 解析失败: {e}"))
    except IRError as e:
        _fail(e)


@main.command()
@click.argument("project", type=click.Path(exists=True))
@click.option("--stage", help="按指定阶段跑门（缺省用 meta.status）")
def validate(project: str, stage: str | None) -> None:
    """跑 G1 门套件；有 error 级违规时退出码 1。"""
    try:
        report = api.ir_validate(project, stage)
        _emit(report)
        if not report["ok"]:
            sys.exit(1)
    except IRError as e:
        _fail(e)


@main.command()
@click.argument("project", type=click.Path(exists=True))
@click.argument("targets", nargs=-1, required=True)
@click.option("--dry-run", is_flag=True, help="只出执行计划，不花钱")
def execute(project: str, targets: tuple[str, ...], dry_run: bool) -> None:
    """执行生成：shots.<id> / shot_groups.<id> / anchors.<id> / audio.voiceover / compose"""
    try:
        _emit(api.ir_execute(project, list(targets), dry_run=dry_run))
    except IRError as e:
        _fail(e)


@main.command()
@click.argument("project", type=click.Path(exists=True))
@click.option("--write", is_flag=True, help="落盘（缺省 dry-run 只出报告）")
def migrate(project: str, write: bool) -> None:
    """M0 旧格式收编到 m1-v1。"""
    try:
        _emit(api.ir_migrate(project, write=write))
    except IRError as e:
        _fail(e)


@main.command()
@click.argument("project", type=click.Path())
@click.option("--title", required=True)
@click.option("--format", "format_", default="", help="片型")
@click.option("--style-pack", default="")
@click.option("--duration", type=float, default=60, help="承诺时长（秒）")
@click.option("--tolerance", type=float, default=5, help="承诺公差（%）")
@click.option("--aspect", default="16:9")
def new(project: str, title: str, format_: str, style_pack: str,
        duration: float, tolerance: float, aspect: str) -> None:
    """新建项目 film.json（m1-v1）。"""
    try:
        _emit(api.ir_new(project, title=title, format=format_, style_pack=style_pack,
                         duration_s=duration, tolerance_pct=tolerance, aspect=aspect))
    except IRError as e:
        _fail(e)


if __name__ == "__main__":
    main()
