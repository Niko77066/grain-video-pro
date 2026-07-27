"""风格合同门（style.contract.*）：P0-2 的回归考卷。

场景取自 2026-07-20 五片对照实验的真实病灶：
- Codex hf-breach：case-file 三声部压成单声部（collage=0）、成片 0 个 <video>、静态持有 75%、
  13 镜 static_class 全误标 false；
- Codex ac-26c：pixel-chronicle 像素叙事 0%（16 MG + 8 实拍）、五连 MG ≈36s。
"""

import json

import pytest

from film_ir.gates import run_gates
from film_ir.models import FilmIR

from conftest import minimal_ir, shot


CASE_FILE_CONTRACT = {
    "schema": "style-contract@1",
    "style_pack": "case-file",
    "plan": {
        "voices": {
            "collage_broll": {"providers": ["collage_broll"],
                              "min_shots": {"value": 3, "amend": [2, 6]}},
            "document": {"providers": ["hyperframes"], "declared_as": "document",
                         "min_shots": {"value": 1, "amend": [1, 4]}},
        },
    },
    "render": {
        "static_hold_ratio_max": {"value": 0.6, "amend": [0.45, 0.65]},
        "min_video_elements": {"value": 3, "amend": [2, 99]},
    },
}

PIXEL_CONTRACT = {
    "schema": "style-contract@1",
    "style_pack": "pixel-chronicle",
    "plan": {
        "traits": {
            "pixel_narrative": {"share_min": {"value": 0.4, "amend": [0.3, 0.5]}},
        },
        "graphics_run_max_s": {"value": 26, "amend": [22, 34]},
    },
}


@pytest.fixture
def project(tmp_path):
    """tmp 仓库骨架：<repo>/styles/<pack>/contract.json + <repo>/projects/p/。"""
    def _make(contract: dict, ir_dict: dict, evidence: dict | None = None):
        pack = contract["style_pack"]
        pack_dir = tmp_path / "styles" / pack
        pack_dir.mkdir(parents=True)
        (pack_dir / "contract.json").write_text(
            json.dumps(contract, ensure_ascii=False), encoding="utf-8")
        pdir = tmp_path / "projects" / "p"
        pdir.mkdir(parents=True)
        if evidence is not None:
            (pdir / "evidence").mkdir()
            (pdir / "evidence" / "render-metrics.json").write_text(
                json.dumps(evidence, ensure_ascii=False), encoding="utf-8")
        return FilmIR.model_validate(ir_dict), pdir
    return _make


def _codex_hf_ir(status="storyboard", **meta_over) -> dict:
    """全 hyperframes 单声部片（Codex hf-breach 形）。"""
    ir = minimal_ir(style_pack="case-file", status=status, **meta_over)
    ir["audio"] = {"timeline": {"duration_s": 72.0, "sections": []}}
    n, seg = 12, 6.0
    ir["shots"] = [shot(f"s{i:02d}", i * seg, (i + 1) * seg,
                        provider="hyperframes", static_class=False)
                   for i in range(n)]
    ir["meta"]["commitment"]["duration_s"] = 72.0
    return ir


def _errors(report, gate):
    return [x for x in report["violations"]
            if x["gate"] == gate and x["severity"] == "error"]


# ---------------------------------------------------------------- plan 门

def test_missing_voice_is_error(project):
    ir, pdir = project(CASE_FILE_CONTRACT, _codex_hf_ir())
    report = run_gates(ir, project_dir=pdir)
    msgs = [x["message"] for x in _errors(report, "style.contract.plan")]
    assert any("collage_broll" in m for m in msgs)


def test_voices_satisfied_passes(project):
    ir_dict = _codex_hf_ir()
    for i in (2, 5, 8):
        ir_dict["shots"][i]["source"] = {"provider": "collage_broll"}
    # document 声部声明在场
    ir_dict["shots"][0]["source"]["params"] = {"voice": "document"}
    ir, pdir = project(CASE_FILE_CONTRACT, ir_dict)
    report = run_gates(ir, project_dir=pdir)
    assert not _errors(report, "style.contract.plan")


def test_declared_voice_missing_is_warn_when_undeclared(project):
    """legacy 片全无 voice 声明：document 在场性降 warn，不误伤。"""
    ir_dict = _codex_hf_ir()
    for i in (2, 5, 8):
        ir_dict["shots"][i]["source"] = {"provider": "collage_broll"}
    ir, pdir = project(CASE_FILE_CONTRACT, ir_dict)
    report = run_gates(ir, project_dir=pdir)
    assert not _errors(report, "style.contract.plan")
    assert any(x["gate"] == "style.contract.plan" and "document" in x["message"]
               for x in report["violations"] if x["severity"] == "warn")


def test_amendment_within_bounds(project):
    """带宽内调整生效（3→2），端到端不断；产生可见性 warn。"""
    ir_dict = _codex_hf_ir()
    for i in (2, 5):
        ir_dict["shots"][i]["source"] = {"provider": "collage_broll"}
    ir_dict["meta"]["contract_amendments"] = {
        "plan.voices.collage_broll.min_shots": 2}
    ir, pdir = project(CASE_FILE_CONTRACT, ir_dict)
    report = run_gates(ir, project_dir=pdir)
    assert not _errors(report, "style.contract.plan")
    assert any(x["gate"] == "style.contract.amend" and x["severity"] == "warn"
               for x in report["violations"])


def test_amendment_out_of_bounds_is_violation(project):
    """越界修改（min_shots→0，等于删声部）：修改无效 + 违约双 error。"""
    ir_dict = _codex_hf_ir()
    ir_dict["meta"]["contract_amendments"] = {
        "plan.voices.collage_broll.min_shots": 0}
    ir, pdir = project(CASE_FILE_CONTRACT, ir_dict)
    report = run_gates(ir, project_dir=pdir)
    assert _errors(report, "style.contract.amend")
    assert _errors(report, "style.contract.plan")


def test_unknown_amendment_key_is_error(project):
    ir_dict = _codex_hf_ir()
    ir_dict["meta"]["contract_amendments"] = {"plan.nonexistent": 1}
    ir, pdir = project(CASE_FILE_CONTRACT, ir_dict)
    report = run_gates(ir, project_dir=pdir)
    assert _errors(report, "style.contract.amend")


def test_pixel_narrative_zero_is_error(project):
    """Codex ac-26c 形：0 个 seedance 镜、无 pixel_narrative 标记 → 像素叙事 0%。"""
    ir_dict = minimal_ir(style_pack="pixel-chronicle", status="storyboard")
    ir_dict["audio"] = {"timeline": {"duration_s": 100.0, "sections": []}}
    ir_dict["shots"] = [shot(f"s{i:02d}", i * 10.0, (i + 1) * 10.0,
                             provider="hyperframes" if i % 2 else "footage",
                             static_class=bool(i % 2))
                        for i in range(10)]
    ir, pdir = project(PIXEL_CONTRACT, ir_dict)
    report = run_gates(ir, project_dir=pdir)
    msgs = [x["message"] for x in _errors(report, "style.contract.plan")]
    assert any("像素叙事" in m for m in msgs)


def test_seedance_counts_as_pixel_narrative_fallback(project):
    ir_dict = minimal_ir(style_pack="pixel-chronicle", status="storyboard")
    ir_dict["audio"] = {"timeline": {"duration_s": 100.0, "sections": []}}
    ir_dict["shots"] = [
        shot("s01", 0, 45, provider="seedance", static_class=False,
             motion="推近"),
        shot("s02", 45, 100, provider="footage", static_class=False),
    ]
    ir, pdir = project(PIXEL_CONTRACT, ir_dict)
    ir.shot_groups = []
    report = run_gates(ir, project_dir=pdir)
    assert not any("像素叙事" in x["message"]
                   for x in _errors(report, "style.contract.plan"))


def test_graphics_run_over_limit(project):
    """五连 MG 36s（Codex ac-26c s14–s18 形）> 26s 上限。"""
    ir_dict = minimal_ir(style_pack="pixel-chronicle", status="storyboard")
    ir_dict["audio"] = {"timeline": {"duration_s": 72.0, "sections": []}}
    shots = [shot("s00", 0, 18, provider="seedance", static_class=False,
                  source={"provider": "seedance",
                          "params": {"pixel_narrative": True}}),
             shot("s0x", 18, 36, provider="footage", static_class=False)]
    shots += [shot(f"s{i:02d}", 36 + (i - 1) * 7.2, 36 + i * 7.2,
                   provider="hyperframes") for i in range(1, 6)]
    ir_dict["shots"] = shots
    ir, pdir = project(PIXEL_CONTRACT, ir_dict)
    report = run_gates(ir, project_dir=pdir)
    msgs = [x["message"] for x in _errors(report, "style.contract.plan")]
    assert any("连续" in m for m in msgs)


# ---------------------------------------------------------------- render 门

def _evidence(hold_ratio=0.75, video_elements=0, per_shot=None,
              palette=None) -> dict:
    ev = {
        "schema": "render-metrics@1",
        "video": {"duration_s": 72.0},
        "static": {"hold_ratio": hold_ratio, "hold_total_s": hold_ratio * 72,
                   "per_shot": per_shot or []},
        "compose": {"video_elements": video_elements},
    }
    if palette is not None:
        ev["palette"] = palette
    return ev


def _palette(max_drift, shot_id="s07") -> dict:
    return {"measurable": True, "max_drift": max_drift, "max_drift_shot": shot_id,
            "pairwise_distance_var": 0.044, "drift_median": 0.33,
            "outlier_shots": [{"id": shot_id, "drift": max_drift}]}


def test_render_evidence_missing_is_error_in_review(project):
    ir, pdir = project(CASE_FILE_CONTRACT, _codex_hf_ir(status="review"))
    report = run_gates(ir, project_dir=pdir)
    assert _errors(report, "style.contract.render")


def test_render_codex_shape_fails(project):
    """静态持有 75% + 0 个 <video> + 12 镜自报/实测矛盾 → 三重 error。"""
    per_shot = [{"id": f"s{i:02d}", "measured_static": True} for i in range(12)]
    ir, pdir = project(CASE_FILE_CONTRACT, _codex_hf_ir(status="review"),
                       evidence=_evidence(0.75, 0, per_shot))
    report = run_gates(ir, project_dir=pdir)
    msgs = [x["message"] for x in _errors(report, "style.contract.render")]
    assert any("静态持有" in m for m in msgs)
    assert any("<video>" in m for m in msgs)
    assert any("static_class" in m for m in msgs)


def test_render_polished_shape_passes(project):
    """打磨版形：52% 持有 + 4 个 <video> → render 门无 error。"""
    ir, pdir = project(CASE_FILE_CONTRACT, _codex_hf_ir(status="review"),
                       evidence=_evidence(0.52, 4))
    report = run_gates(ir, project_dir=pdir)
    assert not _errors(report, "style.contract.render")


# ------------------------------------------------- render 门 · 跨镜头主色漂移

def _palette_contract(value=0.8, amend=(0.72, 0.88)) -> dict:
    c = json.loads(json.dumps(CASE_FILE_CONTRACT))
    c["render"]["palette_drift_max"] = {"value": value, "amend": list(amend)}
    return c


def test_palette_green_anchor_passes(project):
    """浣熊片实测绿锚 0.691（delivered / G2 缝合 4-5）不得被回溯判红。

    该镜是夜戏声部与琥珀编年史世界的合理色温差，不是缝合失败。
    """
    ir, pdir = project(_palette_contract(), _codex_hf_ir(status="review"),
                       evidence=_evidence(0.52, 4, palette=_palette(0.6914)))
    assert not _errors(run_gates(ir, project_dir=pdir), "style.contract.render")


def test_palette_red_anchor_fails(project):
    """负对照红锚 0.974：把另一部片（蓝调新闻棚）未调色镜头切进浣熊时间轴。"""
    ir, pdir = project(_palette_contract(), _codex_hf_ir(status="review"),
                       evidence=_evidence(0.52, 4,
                                          palette=_palette(0.9737, "s17_roof")))
    msgs = [x["message"] for x in
            _errors(run_gates(ir, project_dir=pdir), "style.contract.render")]
    assert any("主色漂移" in m and "s17_roof" in m for m in msgs)


def test_palette_red_anchor_still_red_at_amend_ceiling(project):
    """带宽顶 0.88 仍挡得住红锚——basis 里的这句承诺是可回归的。"""
    ir_dict = _codex_hf_ir(status="review")
    ir_dict["meta"]["contract_amendments"] = {"render.palette_drift_max": 0.88}
    ir, pdir = project(_palette_contract(), ir_dict,
                       evidence=_evidence(0.52, 4, palette=_palette(0.9737)))
    assert _errors(run_gates(ir, project_dir=pdir), "style.contract.render")


def test_palette_missing_in_legacy_evidence_is_warn(project):
    """早于本指标的证据文件没有 palette 段：提示重跑，不误判违约。"""
    ir, pdir = project(_palette_contract(), _codex_hf_ir(status="review"),
                       evidence=_evidence(0.52, 4))
    report = run_gates(ir, project_dir=pdir)
    assert not _errors(report, "style.contract.render")
    assert any(x["severity"] == "warn" and "palette" in x["path"]
               for x in report["violations"])


def test_palette_unmeasurable_is_warn(project):
    """单镜片/空帧流的跨镜头指标无定义——降 warn，不假装能判。"""
    ir, pdir = project(
        _palette_contract(), _codex_hf_ir(status="review"),
        evidence=_evidence(0.52, 4,
                           palette={"measurable": False, "reason": "镜头数 <2"}))
    report = run_gates(ir, project_dir=pdir)
    assert not _errors(report, "style.contract.render")
    assert any(x["severity"] == "warn" and "不可测" in x["message"]
               for x in report["violations"])


def test_palette_term_absent_skips_gate(project):
    """未写此条目的合同（尚未标定的包）不受此门约束，也不因缺证据报错。"""
    ir, pdir = project(CASE_FILE_CONTRACT, _codex_hf_ir(status="review"),
                       evidence=_evidence(0.52, 4))
    report = run_gates(ir, project_dir=pdir)
    assert not any("palette" in x["path"] for x in report["violations"])


def test_no_contract_pack_skips(project, tmp_path):
    """无合同的风格包不受此门约束。"""
    ir_dict = _codex_hf_ir()
    ir_dict["meta"]["style_pack"] = "daily-brief"
    ir, pdir = project(CASE_FILE_CONTRACT, ir_dict)
    report = run_gates(ir, project_dir=pdir)
    assert not [x for x in report["violations"]
                if x["gate"].startswith("style.contract")]


# ---------------------------------------------------------------- schema 门

def test_unenforced_term_is_error(project):
    """合同写了校验器不读的阈值条目：报 error，不静默忽略。

    真实病灶：2026-07-27 风格包生成实验里，两份合成合同一共写了 26 条
    render 门，校验器实际执法 1 条——其余全被静默吞掉，看起来却像有门。
    """
    contract = json.loads(json.dumps(CASE_FILE_CONTRACT))
    contract["render"]["motion_source_share_min"] = {"value": 0.5,
                                                     "amend": [0.44, 0.56]}
    ir, pdir = project(contract, _codex_hf_ir())
    msgs = [x["message"] for x in _errors(run_gates(ir, project_dir=pdir),
                                          "style.contract.schema")]
    assert any("render.motion_source_share_min" in m for m in msgs)


def test_declared_unenforced_term_is_warn(project):
    """自称 enforced:false 的条目降 warn——声明性条款合法，装饰品不合法。"""
    contract = json.loads(json.dumps(CASE_FILE_CONTRACT))
    contract["plan"]["visual_handle_declared"] = {"value": 1, "amend": [1, 1],
                                                  "enforced": False}
    ir, pdir = project(contract, _codex_hf_ir())
    report = run_gates(ir, project_dir=pdir)
    assert not _errors(report, "style.contract.schema")
    assert any(x["gate"] == "style.contract.schema" and x["severity"] == "warn"
               and "visual_handle_declared" in x["message"]
               for x in report["violations"])


def test_prose_fields_are_not_terms(project):
    """basis / role / providers 是散文与配置，不是阈值条目，不该被误报。"""
    contract = json.loads(json.dumps(CASE_FILE_CONTRACT))
    contract["plan"]["voices"]["document"]["note"] = "文件实证声部"
    contract["render"]["static_hold_ratio_max"]["basis"] = "实测 0.619 绿 / 0.747 红"
    ir, pdir = project(contract, _codex_hf_ir())
    assert not _errors(run_gates(ir, project_dir=pdir), "style.contract.schema")


def test_shipped_contracts_have_no_dead_terms():
    """三个出厂风格包不得有装饰条款——本门的回归锚。"""
    from pathlib import Path

    from film_ir import contract as _c

    styles = Path(__file__).resolve().parents[2] / "styles"
    checked = []
    for f in sorted(styles.glob("*/contract.json")):
        data = json.loads(f.read_text(encoding="utf-8"))
        if data.get("schema") != _c.SCHEMA:
            continue
        dead, _ = _c.unenforced_terms(data)
        assert not dead, f"{f.parent.name} 有无人执法的合同条目: {dead}"
        checked.append(f.parent.name)
    assert checked, "一个风格包都没扫到，路径大概错了"
