import pytest

from modules.raid import array_state, calculate_raid, rebuild_time, xor_recover


@pytest.mark.parametrize(
    ("level", "expected"),
    [
        ("RAID 0", 4),
        ("RAID 1", 2),
        ("RAID 5", 3),
        ("RAID 6", 2),
        ("RAID 10", 2),
    ],
)
def test_raid_capacity(level, expected):
    result = calculate_raid(level, 4, 1)
    assert result["usable_capacity_tb"] == expected


def test_invalid_raids():
    with pytest.raises(ValueError):
        calculate_raid("RAID 5", 2, 1)
    with pytest.raises(ValueError):
        calculate_raid("RAID 10", 5, 1)
    with pytest.raises(ValueError):
        calculate_raid("RAID 7", 4, 1)


def test_raid_failure_states():
    assert array_state("RAID 0", 4, {0}) == "Failed"
    assert array_state("RAID 5", 4, {1}) == "Degraded"
    assert array_state("RAID 5", 4, {1, 2}) == "Failed"
    assert array_state("RAID 6", 4, {1, 2}) == "Degraded"
    assert array_state("RAID 10", 4, {0, 2}) == "Degraded"
    assert array_state("RAID 10", 4, {0, 1}) == "Failed"


def test_xor_recovery():
    a, b, c = int("1010", 2), int("1100", 2), int("0110", 2)
    parity, _missing, recovered = xor_recover(a, b, c)
    assert parity == int("0000", 2)
    assert recovered == c


def test_rebuild_time():
    one_tb_mb = 1024 * 1024
    assert rebuild_time(1, one_tb_mb / 3600) == pytest.approx(1.0)
