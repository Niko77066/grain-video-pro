import pytest

from film_ir.errors import IRError
from film_ir.selectors import resolve

DATA = {
    "meta": {"status": "storyboard", "budget": {"cap_usd": None}},
    "shots": [
        {"id": "s01", "status": "qc_pass", "gen": {"model": "m1"}},
        {"id": "s02", "status": "qc_fail", "gen": {"model": "m2"}},
        {"id": "s03", "status": "qc_fail"},
    ],
}


def test_dotted_path():
    assert resolve(DATA, "meta.status") == "storyboard"


def test_by_id():
    assert resolve(DATA, "shots[s02].gen.model") == "m2"


def test_projection():
    assert resolve(DATA, "shots[*].status") == ["qc_pass", "qc_fail", "qc_fail"]


def test_filter():
    assert [s["id"] for s in resolve(DATA, "shots[?status=qc_fail]")] == ["s02", "s03"]


def test_whole_array():
    assert len(resolve(DATA, "shots")) == 3


def test_errors():
    with pytest.raises(IRError) as e:
        resolve(DATA, "shots[s99]")
    assert e.value.code == "NOT_FOUND"
    with pytest.raises(IRError) as e:
        resolve(DATA, "meta[*]")
    assert e.value.code == "BAD_SELECTOR"
    with pytest.raises(IRError) as e:
        resolve(DATA, "nothing.here")
    assert e.value.code == "NOT_FOUND"
