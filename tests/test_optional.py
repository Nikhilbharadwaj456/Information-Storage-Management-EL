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
