"""ir_patch 的安全性质：门控字段、ledger 只追加、状态机、原子性。"""

import pytest

from film_ir.errors import IRError
from film_ir.patch import apply_patch

from conftest import minimal_ir, shot


def _base():
    d = minimal_ir(status="storyboard")
    d["audio"]["timeline"] = {"duration_s": 10.0,
                              "sections": [{"id": "sec01", "t": [0.0, 10.0]}]}
    d["shots"] = [shot("s01", 0.0, 5.0), shot("s02", 5.0, 10.0)]
    d["ledger"]["decisions"] = [{"id": "d01", "stage": "brief", "date": "2026-07-16",
                                 "decision": "立项", "why": "测试"}]
    return d


def test_set_and_append():
    new, res = apply_patch(_base(), [
        {"op": "set", "path": "shots[s01].intent", "value": "改后的意图"},
        {"op": "append", "path": "ledger.gates",
         "value": {"id": "g01", "stage": "storyboard", "date": "2026-07-16",
                   "check": "自查", "result": "pass"}},
    ])
    assert res.applied == 2
    assert new["shots"][0]["intent"] == "改后的意图"
    assert new["ledger"]["gates"][0]["id"] == "g01"


def test_gated_field_requires_revision():
    with pytest.raises(IRError) as e:
        apply_patch(_base(), [{"op": "set", "path": "meta.commitment.duration_s", "value": 90}])
    assert e.value.code == "GATED_FIELD"

    new, res = apply_patch(_base(),
                           [{"op": "set", "path": "meta.commitment.duration_s", "value": 90}],
                           revision={"reason": "客户要求加长到 90s"})
    assert new["meta"]["commitment"]["duration_s"] == 90
    assert res.revision_decision_id == "d02"
    assert new["ledger"]["decisions"][-1]["why"] == "客户要求加长到 90s"


def test_timeline_gated_after_shots_exist():
    with pytest.raises(IRError) as e:
        apply_patch(_base(), [{"op": "set", "path": "audio.timeline.duration_s", "value": 12.0}])
    assert e.value.code == "GATED_FIELD"
    # 分镜为空时 timeline 可自由写（audio 阶段的正常回填）
    d = minimal_ir(status="audio")
    d["audio"]["timeline"] = {"duration_s": 10.0, "sections": []}
    new, _ = apply_patch(d, [{"op": "set", "path": "audio.timeline.duration_s", "value": 12.0}])
    assert new["audio"]["timeline"]["duration_s"] == 12.0


def test_ledger_append_only():
    for bad in (
        [{"op": "set", "path": "ledger.decisions[d01].why", "value": "篡改"}],
        [{"op": "remove", "path": "ledger.decisions[d01]"}],
    ):
        with pytest.raises(IRError) as e:
            apply_patch(_base(), bad)
        assert e.value.code == "LEDGER_IMMUTABLE"


def test_shot_status_machine():
    ok, _ = apply_patch(_base(), [
        {"op": "set", "path": "shots[s01].gen", "value": {"model": "x", "file": "shots/s01.mp4"}},
        {"op": "set", "path": "shots[s01].status", "value": "generated"},
    ])
    assert ok["shots"][0]["status"] == "generated"

    with pytest.raises(IRError) as e:  # planned → qc_pass 跳步
        apply_patch(_base(), [{"op": "set", "path": "shots[s01].status", "value": "qc_pass"}])
    assert e.value.code == "ILLEGAL_TRANSITION"

    with pytest.raises(IRError) as e:  # generated 但没有 gen 留痕
        apply_patch(_base(), [{"op": "set", "path": "shots[s01].status", "value": "generated"}])
    assert e.value.code == "ILLEGAL_TRANSITION"

    base_gen = apply_patch(_base(), [
        {"op": "set", "path": "shots[s01].gen", "value": {"model": "x"}},
        {"op": "set", "path": "shots[s01].status", "value": "generated"},
    ])[0]
    with pytest.raises(IRError) as e:  # qc_pass 但没写 qc 结果
        apply_patch(base_gen, [{"op": "set", "path": "shots[s01].status", "value": "qc_pass"}])
    assert e.value.code == "ILLEGAL_TRANSITION"
    ok2, _ = apply_patch(base_gen, [
        {"op": "set", "path": "shots[s01].qc", "value": {"technical": "pass", "semantic": "兑现"}},
        {"op": "set", "path": "shots[s01].status", "value": "qc_pass"},
    ])
    assert ok2["shots"][0]["status"] == "qc_pass"


def test_atomicity_schema_failure_discards_all():
    old = _base()
    with pytest.raises(IRError) as e:
        apply_patch(old, [
            {"op": "set", "path": "shots[s01].intent", "value": "会被丢弃"},
            {"op": "set", "path": "meta.status", "value": "不存在的阶段"},
        ])
    assert e.value.code == "SCHEMA_INVALID"
    assert old["shots"][0]["intent"] == "镜头 s01", "输入不被就地修改"


def test_insert_after_and_remove():
    new, _ = apply_patch(_base(), [
        {"op": "insert", "path": "shots", "after": "s01",
         "value": shot("s01b", 4.0, 5.0)},
    ])
    assert [s["id"] for s in new["shots"]] == ["s01", "s01b", "s02"]
    new2, _ = apply_patch(new, [{"op": "remove", "path": "shots[s01b]"}])
    assert [s["id"] for s in new2["shots"]] == ["s01", "s02"]
