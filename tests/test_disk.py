import pytest

from modules.disk_performance import calculate_disk, response_time_curve


def test_disk_calculations():
    result = calculate_disk(7200, 4, 150, 4, 100)
    assert result["rotational_latency_ms"] == pytest.approx(30000 / 7200)
    assert result["service_time_ms"] > result["rotational_latency_ms"]
    assert result["estimated_iops"] == pytest.approx(1000 / result["service_time_ms"])
    assert result["utilization"] == pytest.approx(100 * (result["service_time_ms"] / 1000.0))


def test_disk_validation_and_stability():
    with pytest.raises(ValueError):
        calculate_disk(7200, 4, 150, 4, 1000)
    with pytest.raises(ValueError):
        calculate_disk(0, 4, 150, 4, 100)


def test_littles_law_and_response_curve():
    result = calculate_disk(7200, 4, 150, 4, 100)
    expected_requests = 100 * result["response_time_ms"] / 1000
    assert result["requests_in_system"] == pytest.approx(expected_requests)
    curve = response_time_curve(result["service_time_ms"])
    assert len(curve) == 91
    assert curve["Average response time (ms)"].iloc[-1] > curve["Average response time (ms)"].iloc[0]


def test_queue_length_formula():
    from modules.disk_performance import calculate_disk
    result = calculate_disk(7200, 4, 150, 4, 100)
    u = result["utilization"]
    assert result["queue_length"] == pytest.approx(u ** 2 / (1 - u))
