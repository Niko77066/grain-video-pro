"""CLI 端到端：new → patch → read → validate 的完整回合 + 退出码契约。"""

import json

from click.testing import CliRunner

from film_ir.cli import main

from conftest import shot


def _invoke(runner, args, **kw):
    result = runner.invoke(main, args, **kw)
    return result


def test_full_round_trip(tmp_path):
    runner = CliRunner()
    proj = str(tmp_path / "demo")

    r = _invoke(runner, ["new", proj, "--title", "CLI 冒烟片", "--format",
                         "faceless_news_recap", "--duration", "60"])
    assert r.exit_code == 0, r.output

    r = _invoke(runner, ["read", proj, "meta.status"])
    assert r.exit_code == 0 and json.loads(r.output) == "brief"

    # 铺一条最小分镜（timeline 在 shots 为空时可写，非门控）
    ops = [
        {"op": "set", "path": "meta.status", "value": "storyboard"},
        {"op": "set", "path": "audio.timeline",
         "value": {"duration_s": 10.0, "sections": [{"id": "sec01", "t": [0.0, 10.0]}]}},
        {"op": "append", "path": "shots", "value": shot("s01", 0.0, 6.0, voice_ref="sec01")},
        {"op": "append", "path": "shots", "value": shot("s02", 6.0, 10.0, voice_ref="sec01")},
    ]
    r = _invoke(runner, ["patch", proj, "--stdin"], input=json.dumps(ops))
    assert r.exit_code == 0, r.output

    r = _invoke(runner, ["validate", proj])
    report = json.loads(r.output)
    # 10s 音频 vs 60s 承诺 → timeline.commitment 必须拦下（退出码 1）
    assert r.exit_code == 1
    assert any(v["gate"] == "timeline.commitment" for v in report["violations"])

    # 修订承诺后过门
    r = _invoke(runner, ["patch", proj,
                         "--op", json.dumps({"op": "set", "path": "meta.commitment.duration_s",
                                             "value": 10}),
                         "--revision", "冒烟片改 10s 承诺"])
    assert r.exit_code == 0, r.output
    r = _invoke(runner, ["validate", proj])
    assert r.exit_code == 0, r.output

    # 门控字段裸改 → 退出码 1 + 结构化错误
    r = _invoke(runner, ["patch", proj,
                         "--op", json.dumps({"op": "set", "path": "meta.aspect", "value": "9:16"})])
    assert r.exit_code == 1
    assert json.loads(r.stderr)["code"] == "GATED_FIELD"


def test_exit_codes(tmp_path):
    runner = CliRunner()
    proj = str(tmp_path / "demo2")
    _invoke(runner, ["new", proj, "--title", "x"])

    r = _invoke(runner, ["read", proj, "shots[s99]"])
    assert r.exit_code == 2                       # NOT_FOUND → 用法/寻址

    r = _invoke(runner, ["execute", proj, "shots.s99"])
    assert r.exit_code == 1                       # RULE_ZERO → 门禁

    r = _invoke(runner, ["new", proj, "--title", "重复"])
    assert r.exit_code == 2                       # CONFLICT


def test_migrate_dry_run_does_not_write(tmp_path):
    import shutil
    from pathlib import Path
    fixture = Path(__file__).parent / "fixtures" / "800v-thermal-runaway.json"
    proj = tmp_path / "legacy"
    proj.mkdir()
    shutil.copy(fixture, proj / "film.json")
    before = (proj / "film.json").read_text(encoding="utf-8")

    runner = CliRunner()
    r = _invoke(runner, ["migrate", str(proj)])
    assert r.exit_code == 0, r.output
    assert (proj / "film.json").read_text(encoding="utf-8") == before, "dry-run 不落盘"

    r = _invoke(runner, ["migrate", str(proj), "--write"])
    assert r.exit_code == 0
    after = json.loads((proj / "film.json").read_text(encoding="utf-8"))
    assert after["meta"]["schema_version"] == "m1-v1"

    # 迁移后 read/patch 正常工作
    r = _invoke(runner, ["read", str(proj), "shots[?status=qc_pass]"])
    assert r.exit_code == 0
    assert len(json.loads(r.output)) > 0
