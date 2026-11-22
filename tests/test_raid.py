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


def test_write_penalty_per_level():
    penalties = {level: calculate_raid(level, 4, 1)["write_penalty"]
                 for level in ("RAID 0", "RAID 1", "RAID 5", "RAID 6", "RAID 10")}
    assert penalties == {"RAID 0": 1, "RAID 1": 2, "RAID 5": 4, "RAID 6": 6, "RAID 10": 2}


def test_xor_demo_recovers_any_missing_block():
    from modules.raid import xor_demo
    blocks = {"A": 0b1010, "B": 0b1100, "C": 0b0110}
    for name in blocks:
        result = xor_demo(blocks, name)
        assert result["parity"] == 0b0000
        assert result["recovered"] == blocks[name]
        assert result["verified"] is True


def test_remaining_fault_tolerance():
    from modules.raid import remaining_fault_tolerance
    assert remaining_fault_tolerance("RAID 6", 5, {0}) == "1 disk"
    assert remaining_fault_tolerance("RAID 5", 4, {0, 1}) == "0 disks"
    assert remaining_fault_tolerance("RAID 0", 4, set()) == "0 disks"
