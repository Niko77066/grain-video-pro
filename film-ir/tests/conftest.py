import json
from pathlib import Path

import pytest

FIXTURES = Path(__file__).parent / "fixtures"
REAL_FILMS = ["800v-thermal-runaway", "samsung-health-ai-consent", "estee-lauder-night",
              "uk-argentina-feud", "openai-78m-logs"]


@pytest.fixture(params=REAL_FILMS)
def real_film_raw(request):
    return json.loads((FIXTURES / f"{request.param}.json").read_text(encoding="utf-8"))


def load_fixture(name: str) -> dict:
    return json.loads((FIXTURES / f"{name}.json").read_text(encoding="utf-8"))


def minimal_ir(**meta_over) -> dict:
    """最小合法 m1-v1 IR（测试基底）。"""
    meta = {
        "title": "测试片", "format": "faceless_explainer", "style_pack": "daily-brief",
        "commitment": {"type": "typography_led", "duration_s": 60, "tolerance_pct": 5},
        "aspect": "16:9", "budget": {"cap_usd": None, "spent_usd": 0},
        "pipeline_version": "m1-v1", "schema_version": "m1-v1", "status": "brief",
    }
    meta.update(meta_over)
    return {
        "meta": meta,
        "audio": {}, "anchors": [], "shot_groups": [], "shots": [], "overlays": [],
        "edit": {"transitions": [], "loudness_lufs": -14},
        "ledger": {"decisions": [], "costs": [], "gates": []},
    }


def shot(id_, t0, t1, provider="hyperframes", **over) -> dict:
    s = {"id": id_, "t": [t0, t1], "intent": f"镜头 {id_}",
         "source": {"provider": provider}, "anchor_refs": [],
         "static_class": provider in ("hyperframes", "image_motion"),
         "status": "planned"}
    s.update(over)
    return s
