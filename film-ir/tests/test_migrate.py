"""五部成片（M0/M1 五种方言）→ m1-v1 收编回归。fixtures 只读，不碰真实项目文件。"""

from film_ir.gates import run_gates
from film_ir.migrate import migrate
from film_ir.models import FilmIR, SCHEMA_VERSION

from conftest import load_fixture, minimal_ir, shot


def _minimal_m0() -> dict:
    """最小 m0 方言底座：给 dont-set-ac-26 那组用例用。"""
    raw = minimal_ir(pipeline_version="m0-v1", status="delivered")
    raw["shots"] = [shot("s01", 0.0, 5.0)]
    return raw


def test_all_real_films_migrate_to_valid_schema(real_film_raw):
    new, log = migrate(real_film_raw)
    assert new["meta"]["schema_version"] == SCHEMA_VERSION
    assert log, "真实旧片必然有收编动作"
    ir = FilmIR.model_validate(new)
    report = run_gates(ir)          # 门套件在真实数据上必须能跑完（结果另行校准）
    assert isinstance(report["ok"], bool)


def test_migrate_idempotent(real_film_raw):
    once, _ = migrate(real_film_raw)
    twice, log2 = migrate(once)
    assert once == twice, "迁移必须幂等"


def test_800v_dialect():
    new, _ = migrate(load_fixture("800v-thermal-runaway"))
    vo = new["audio"]["voiceover"]
    assert "gen" in vo and vo["gen"]["model"], "平铺留痕收进 gen 块"
    assert "model" not in vo
    assert isinstance(new["audio"]["music"]["gen"], dict)
    assert new["meta"]["status"] == "delivered"        # delivered-v2 归一
    assert new["meta"]["status_original"] == "delivered-v2"
    for g in new["shot_groups"]:
        assert g.get("seam_out") in ("tail_relay", "hard_cut", "transition", "none", None)
    provs = {s["source"]["provider"] for s in new["shots"]}
    assert provs <= {"hyperframes", "seedance", "image_motion", "avatar", "footage", "tts"}


def test_samsung_dialect():
    new, _ = migrate(load_fixture("samsung-health-ai-consent"))
    assert any(s["source"]["provider"] == "avatar" for s in new["shots"])
    for o in new["overlays"]:
        assert "range" not in o
        assert o.get("shot_range") or o.get("shot_refs") or o.get("scope") == "global"
    # source.group → group_ref
    grouped = [s for s in new["shots"] if s.get("group_ref")]
    assert grouped, "samsung 的 source.group 应迁为 group_ref"


def test_uk_argentina_dialect():
    raw = load_fixture("uk-argentina-feud")
    new, _ = migrate(raw)
    # timeline 缺 duration_s → 从实测音频时长回填，来源留痕
    tl = new["audio"]["timeline"]
    assert tl["duration_s"] == 256.68
    assert "duration_s_source" in tl
    # voiceover engine 平铺 → gen 块（model + params，原字段不丢）
    vo = new["audio"]["voiceover"]
    assert "engine" not in vo
    assert vo["gen"]["model"].startswith("minimax")
    assert vo["gen"]["params"]["voice"]
    assert vo["gen"]["duration_actual_s"] == 256.68
    assert vo["sections"], "分节 TTS 留痕原样保留"
    # collage-broll-pixel → collage_broll，原名存 origin_provider
    collage = [s for s in new["shots"] if s["source"]["provider"] == "collage_broll"]
    assert collage
    assert all(s["source"]["params"]["origin_provider"] == "collage-broll-pixel" for s in collage)
    # 镜头 gen.engine → model
    assert all("engine" not in (s.get("gen") or {}) for s in new["shots"])
    # ledger 条目补 id，一条不丢
    for key, n in (("decisions", 22), ("gates", 9)):
        items = new["ledger"][key]
        assert len(items) == len(raw["ledger"][key])
        assert all(it.get("id") for it in items)
    assert new["ledger"]["decisions"][0]["id"] == "dec01"
    assert new["ledger"]["decisions"][0]["by"] == "用户"          # 方言字段原样保留
    assert new["ledger"]["costs"][0]["id"] == "tts_voiceover_adopted"  # 已有 id 不动


def test_openai_78m_dialect():
    raw = load_fixture("openai-78m-logs")
    new, _ = migrate(raw)
    # anchors.gen 字符串 → gen 块：model/prompt_file 拆出，原文存 note
    for a in new["anchors"]:
        assert isinstance(a["gen"], dict)
        assert a["gen"]["model"] == "gpt-image-2 medium"
        assert a["gen"]["prompt_file"].endswith(".json")
        assert a["gen"]["note"]
    # shots.qc 字符串 → {note} 块
    qcs = [s["qc"] for s in new["shots"] if s.get("qc")]
    assert qcs and all(isinstance(q, dict) and q.get("note") for q in qcs)
    # transitions 结构化条目 → 字符串，原文存 transitions_detail
    trans = new["edit"]["transitions"]
    assert all(isinstance(t, str) for t in trans)
    assert trans[0] == "硬切（默认；拼贴 b-roll 与版式卡之间(seam B)）"
    assert new["edit"]["transitions_detail"] == raw["edit"]["transitions"]
    # collage-broll → collage_broll
    assert any(s["source"]["provider"] == "collage_broll" for s in new["shots"])
    # ledger 补 id
    for key in ("decisions", "costs", "gates"):
        assert len(new["ledger"][key]) == len(raw["ledger"][key])
        assert all(it.get("id") for it in new["ledger"][key])


def test_estee_dialect():
    new, _ = migrate(load_fixture("estee-lauder-night"))
    assert all("static_type" not in s for s in new["shots"])
    ov_by_id = {o["id"]: o for o in new["overlays"]}
    assert ov_by_id["ov_sub"]["scope"] == "global"
    assert ov_by_id["ov_num_22"]["shot_range"] == ["s01_hook_film_number", "s01_hook_film_number"]
    assert ov_by_id["ov_tag_brand"]["shot_refs"] == ["s01_hook_film_number", "s06b_space_float"]


# ---------------------------------------------- dont-set-ac-26 方言

def test_shot_status_render_marker_maps_to_generated():
    """rendered_v2 是渲染版本标记不是状态机取值 → generated，原值留痕。

    刻意不映射到 qc_pass：该片方言里 shots.qc 全是 null，没有任何质检证据，
    写成 qc_pass 等于凭空补一份留痕。
    """
    raw = _minimal_m0()
    raw["shots"][0]["status"] = "rendered_v2"
    out, log = migrate(raw)
    assert out["shots"][0]["status"] == "generated"
    assert out["shots"][0]["status_original"] == "rendered_v2"
    assert any("status_original" in x for x in log)


def test_gate_when_renamed_to_date():
    """gates[].when → date：纯改名，是真数据。"""
    raw = _minimal_m0()
    raw["ledger"]["gates"] = [{"id": "G1", "stage": "review", "when": "2026-07-20",
                               "result": "PASS"}]
    out, log = migrate(raw)
    g = out["ledger"]["gates"][0]
    assert g["date"] == "2026-07-20" and "when" not in g


def test_missing_dates_backfilled_from_own_gates_with_source():
    """decisions/costs 缺 date：只用本片记录过的日期回填，且逐条标 date_source。"""
    raw = _minimal_m0()
    raw["ledger"]["gates"] = [{"id": "G1", "stage": "review", "when": "2026-07-20",
                               "result": "PASS"}]
    raw["ledger"]["decisions"] = [{"id": "d1", "stage": "brief", "decision": "x"}]
    out, log = migrate(raw)
    dec = out["ledger"]["decisions"][0]
    assert dec["date"] == "2026-07-20"
    assert "非条目实际发生日" in dec["date_source"]
    assert any("回填 2026-07-20" in x for x in log)


def test_no_date_anywhere_is_not_fabricated():
    """全片一个日期都没有就不回填——宁可让它报错，也不编日期。"""
    raw = _minimal_m0()
    raw["ledger"]["gates"] = []
    raw["ledger"]["decisions"] = [{"id": "d1", "stage": "brief", "decision": "x"}]
    try:
        out, _ = migrate(raw)
    except Exception:
        return                                  # schema 校验拦下，符合预期
    assert "date" not in out["ledger"]["decisions"][0]
