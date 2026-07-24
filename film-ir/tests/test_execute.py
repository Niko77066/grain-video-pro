"""执行层：Rule Zero、占位拒绝、TTS 计划与时间轴构建、HyperFrames lint 门。"""

import json

import pytest

from film_ir.errors import IRError
from film_ir.execute import resolve_target, execute
from film_ir.execute.tts import TTSAdapter
from film_ir.execute.base import Target
from film_ir.models import FilmIR
from film_ir.store import Project

from conftest import minimal_ir, shot


@pytest.fixture
def project(tmp_path):
    d = minimal_ir(status="audio")
    d["audio"]["voiceover"] = {"text_prompt_file": "script-tts.txt"}
    d["shots"] = [shot("s01", 0.0, 5.0, provider="seedance")]
    (tmp_path / "film.json").write_text(json.dumps(d, ensure_ascii=False), encoding="utf-8")
    (tmp_path / "script-tts.txt").write_text(
        "一位专业的中文新闻播报员朗读：“库勒肖夫链路测试。”", encoding="utf-8")
    return Project(tmp_path)


def test_rule_zero_rejects_unknown_target(project):
    ir = project.load()
    with pytest.raises(IRError) as e:
        resolve_target(ir, "shots.s99")
    assert e.value.code == "RULE_ZERO"


def test_rule_zero_rejects_voiceover_without_entry(tmp_path):
    d = minimal_ir()
    (tmp_path / "film.json").write_text(json.dumps(d), encoding="utf-8")
    ir = Project(tmp_path).load()
    with pytest.raises(IRError) as e:
        resolve_target(ir, "audio.voiceover")
    assert e.value.code == "RULE_ZERO"


def test_seedance_adapter_plans_translation(project):
    """去模型化：seedance 不再占位报错，dry-run 出译好的 provider 请求方言（脱敏、无 key）。"""
    out = execute(project, ["shots.s01"], dry_run=True)   # s01 → seedance
    r = out["results"][0]
    assert r["provider"] == "seedance" and r["dry_run"] is True
    req = r["plan"]["requests"][0]
    assert req["model"] == "doubao-seedance-2-0-260128"
    assert req["duration_s"] == 5.0
    assert not any(("KEY" in str(k).upper() or "TOKEN" in str(k).upper()) for k in req)


def test_provider_adapter_delegates_on_run(project):
    """run 委托宿主：写请求文件 + 置 sourced + gen 记请求 + ledger 决策（不 fake 生成、不持 key）。"""
    out = execute(project, ["shots.s01"])
    assert out["ok"]
    ir = project.load()
    s = next(x for x in ir.shots if x.id == "s01")
    assert s.status == "sourced"
    assert s.gen is not None and "delegated" in s.gen.model
    assert (project.dir / "shots" / "s01.request.json").is_file()
    assert any("交宿主" in d.decision for d in ir.ledger.decisions)


def test_tts_plan(project):
    ir = project.load()
    plan = TTSAdapter().plan(ir, Target("audio.voiceover", "audio.voiceover", None, "tts"),
                             project.dir)
    payload = plan.requests[0]
    assert payload["model"] == "speech-2.8-hd"       # MiniMax，非火山 seed-audio
    assert "朗读" in payload["text"]
    assert not any("KEY" in str(k).upper() or "TOKEN" in str(k).upper() for k in payload)


def test_tts_plan_missing_prompt_file(tmp_path):
    d = minimal_ir()
    d["audio"]["voiceover"] = {}
    (tmp_path / "film.json").write_text(json.dumps(d), encoding="utf-8")
    p = Project(tmp_path)
    ir = p.load()
    with pytest.raises(IRError) as e:
        TTSAdapter().plan(ir, Target("audio.voiceover", "audio.voiceover", None, "tts"), p.dir)
    assert e.value.code == "RULE_ZERO"


def test_tts_delegates_on_run(project):
    """MiniMax + 委托：run 写请求文件 + 置 awaiting + gen 记请求 + ledger 决策（不 fake、不持 key）。
    timeline 不再由 TTS 自报字幕建——交 forced-alignment 另建。"""
    out = execute(project, ["audio.voiceover"])
    assert out["ok"]
    ir = project.load()
    assert ir.audio.voiceover.status == "awaiting_generation"
    assert ir.audio.voiceover.gen and "delegated" in ir.audio.voiceover.gen.model
    assert (project.dir / "audio" / "voiceover.request.json").is_file()
    assert ir.audio.timeline is None   # timeline 由 forced-alignment 建，不由 TTS


def test_execute_dry_run_tts(project):
    out = execute(project, ["audio.voiceover"], dry_run=True)
    assert out["results"][0]["dry_run"] is True
    assert out["results"][0]["provider"] == "tts"


def test_budget_fuse(project, monkeypatch):
    from film_ir import api
    api.ir_patch(project.dir, [
        {"op": "set", "path": "meta.budget", "value": {"cap_usd": 1.0, "spent_usd": 2.0}},
    ], revision={"reason": "测试熔断"})
    with pytest.raises(IRError) as e:
        execute(Project(project.dir), ["audio.voiceover"])
    assert "熔断" in e.value.message


def test_hyperframes_lint_gate(tmp_path, monkeypatch):
    import subprocess
    from film_ir.execute.hyperframes import HyperframesAdapter

    d = minimal_ir(status="compose")
    (tmp_path / "film.json").write_text(json.dumps(d), encoding="utf-8")
    (tmp_path / "compose").mkdir()
    p = Project(tmp_path)

    calls = []

    def fake_run(cmd, **kw):
        calls.append(cmd)
        class R:
            returncode = 1 if "lint" in cmd else 0
            stdout, stderr = "", "clip missing data-start"
        return R()

    monkeypatch.setattr(subprocess, "run", fake_run)
    ad = HyperframesAdapter()
    target = Target("compose", "compose", None, "hyperframes")
    plan = ad.plan(p.load(), target, p.dir)
    with pytest.raises(IRError) as e:
        ad.run(p.load(), target, plan, p.dir)
    assert "lint 不过" in e.value.message
    assert len(calls) == 1, "lint 不过必须禁 render"
