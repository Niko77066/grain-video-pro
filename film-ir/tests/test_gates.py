"""G1 门套件：每个硬门一个能触发它的最小案例。"""

from film_ir.gates import run_gates
from film_ir.models import FilmIR

from conftest import minimal_ir, shot


def _gates(d, stage=None):
    report = run_gates(FilmIR.model_validate(d), stage)
    return {v["gate"] for v in report["violations"] if v["severity"] == "error"}, report


def _with_timeline(d, duration=60.0):
    d["meta"]["status"] = "storyboard"
    d["audio"]["timeline"] = {"duration_s": duration,
                              "sections": [{"id": "sec01", "t": [0.0, duration]}]}
    return d


def test_clean_film_passes():
    d = _with_timeline(minimal_ir())
    d["shots"] = [shot("s01", 0.0, 30.0, provider="seedance", motion="dolly-in",
                       group_ref="g01", static_class=False),
                  shot("s02", 30.0, 60.0, provider="footage", static_class=False)]
    d["shot_groups"] = [{"id": "g01", "shots": ["s01"], "provider": "seedance",
                         "duration_s": 30.0, "seam_out": "hard_cut"}]
    errs, report = _gates(d)
    # s01 组 30s 超 15s 上限——这是故意的对照组
    assert errs == {"groups.arithmetic"}


def test_timeline_gap_and_overlap():
    d = _with_timeline(minimal_ir(), 20.0)
    d["shots"] = [shot("s01", 0.0, 8.0), shot("s02", 9.0, 14.0), shot("s03", 13.0, 20.0)]
    errs, report = _gates(d)
    msgs = [v["message"] for v in report["violations"] if v["gate"] == "timeline.coverage"]
    assert any("缝隙" in m for m in msgs) and any("重叠" in m for m in msgs)


def test_commitment_duration():
    d = _with_timeline(minimal_ir(), 70.0)   # 60s ± 5% 之外
    d["meta"]["status"] = "audio"
    errs, _ = _gates(d)
    assert "timeline.commitment" in errs


def test_groups_arithmetic_membership():
    d = _with_timeline(minimal_ir(), 10.0)
    d["shots"] = [shot("s01", 0.0, 5.0, provider="seedance"),
                  shot("s02", 5.0, 10.0, provider="seedance")]
    d["shot_groups"] = [{"id": "g01", "shots": ["s01"], "duration_s": 5.0},
                        {"id": "g02", "shots": ["s01"], "duration_s": 5.0}]  # s01 双重属组，s02 无组
    errs, report = _gates(d)
    assert "groups.arithmetic" in errs
    paths = {v["path"] for v in report["violations"] if v["gate"] == "groups.arithmetic"}
    assert "shots[s01]" in paths and "shots[s02]" in paths


def test_slides_risk_static_run():
    d = _with_timeline(minimal_ir(), 40.0)
    d["shots"] = [shot(f"s{i}", i * 10.0, (i + 1) * 10.0, provider="hyperframes")
                  for i in range(4)]   # 4 连静态
    errs, _ = _gates(d)
    assert "slides.risk" in errs


def test_transitions_max():
    d = minimal_ir(status="compose")
    d["edit"]["transitions"] = ["a", "b", "c", "d", "e"]
    errs, _ = _gates(d)
    assert "edit.transitions" in errs


def test_refs_integrity():
    d = _with_timeline(minimal_ir(), 10.0)
    d["shots"] = [shot("s01", 0.0, 10.0, anchor_refs=["a_missing"], voice_ref="sec99")]
    errs, report = _gates(d)
    assert "refs" in errs
    assert len([v for v in report["violations"] if v["gate"] == "refs"]) == 2


def test_stage_filtering():
    d = minimal_ir(status="brief")
    d["edit"]["transitions"] = ["a", "b", "c", "d", "e"]   # compose 阶段的门
    errs, report = _gates(d)                                # brief 阶段不应触发
    assert "edit.transitions" not in errs
    errs2, _ = _gates(d, stage="compose")
    assert "edit.transitions" in errs2
