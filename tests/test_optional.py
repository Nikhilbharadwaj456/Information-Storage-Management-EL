import pytest

from modules.replication import replication_comparison
from modules.risk_assessment import calculate_risk, risk_category


def test_replication_modes():
    sync = replication_comparison("Synchronous", 2, 20, 1000, 500)
    async_result = replication_comparison("Asynchronous", 2, 20, 1000, 500)
    assert sync["response_ms"] == 22
    assert async_result["response_ms"] == 2
    assert sync["lag_ms"] < async_result["lag_ms"]
    with pytest.raises(ValueError):
        replication_comparison("Hybrid", 2, 20, 1000, 500)


def test_risk_score():
    assert calculate_risk(5, 5) == 25
    assert risk_category(25) == "Critical"
    assert risk_category(8) == "Medium"
    with pytest.raises(ValueError):
        calculate_risk(0, 5)
    with pytest.raises(ValueError):
        calculate_risk(3.5, 5)


def test_replication_distance_adds_propagation_delay():
    near = replication_comparison("Synchronous", 2, 1, 1000, 500, distance_km=0)
    far = replication_comparison("Synchronous", 2, 1, 1000, 500, distance_km=1000)
    assert far["response_ms"] - near["response_ms"] == pytest.approx(10.0)


def test_async_lag_has_consistent_units():
    light = replication_comparison("Asynchronous", 2, 20, 1000, 100, write_size_kb=8)
    heavy = replication_comparison("Asynchronous", 2, 20, 1000, 10000, write_size_kb=8)
    assert light["lag_ms"] == pytest.approx(10 + 0.065536 / (1 - 0.0065536))
    assert 10 < heavy["lag_ms"] < 11
    assert heavy["rpo_ms"] == heavy["lag_ms"]


def test_saturated_replication_link_is_rejected():
    with pytest.raises(ValueError, match="saturated"):
        replication_comparison("Asynchronous", 2, 20, 100, 2000, write_size_kb=8)
