"""Тесты маршрутизации агента (предикат condition edge)."""

from app.agents.nodes import decide_route


def test_decide_route_defaults_to_search():
    assert decide_route({}) == "search"


def test_decide_route_explicit_direct():
    assert decide_route({"route": "direct"}) == "direct"


def test_decide_route_explicit_search():
    assert decide_route({"route": "search"}) == "search"
