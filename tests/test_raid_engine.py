import hashlib
import itertools
import os

import numpy as np
import pytest

from modules import raid_engine as engine


CONFIGS = [
    ("RAID 0", 3),
    ("RAID 1", 2),
    ("RAID 5", 4),
    ("RAID 6", 5),
    ("RAID 10", 4),
]


def sample_bytes(size: int = 10_000) -> bytes:
    return os.urandom(size)


def make_array(tmp_path, level, disks, data, spares=2, block_size=512):
    meta = engine.create_array(tmp_path, data, "sample.bin", level, disks, block_size, spares)
    return tmp_path / meta["id"]


def rebuild(array_dir, disk):
    steps = list(engine.rebuild_disk(array_dir, disk))
    return steps[-1]


@pytest.mark.parametrize(("level", "disks"), CONFIGS)
def test_write_then_read_returns_identical_bytes(tmp_path, level, disks):
    data = sample_bytes()
    array_dir = make_array(tmp_path, level, disks, data)
    assert engine.read_file(array_dir) == data
    assert engine.verify(array_dir)["match"] is True


@pytest.mark.parametrize(("level", "disks"), [c for c in CONFIGS if c[0] != "RAID 0"])
def test_failures_within_tolerance_rebuild_to_matching_sha(tmp_path, level, disks):
    tolerance = engine.fault_tolerance(level, disks)
    for failed in itertools.combinations(range(disks), tolerance):
        data = sample_bytes()
        root = tmp_path / "-".join(map(str, failed))
        array_dir = make_array(root, level, disks, data)
        for disk in failed:
            engine.fail_disk(array_dir, disk)

        degraded = engine.verify(array_dir)
        assert degraded["state"] == "Degraded"
        assert degraded["read_sha256"] == hashlib.sha256(data).hexdigest()

        for disk in failed:
            done, total = rebuild(array_dir, disk)
            assert done == total
        healed = engine.verify(array_dir)
        assert healed["state"] == "Healthy"
        assert healed["match"] is True


@pytest.mark.parametrize(
    ("level", "disks", "failed"),
    [
        ("RAID 0", 3, (1,)),
        ("RAID 1", 2, (0, 1)),
        ("RAID 5", 4, (0, 2)),
        ("RAID 6", 5, (0, 1, 3)),
        ("RAID 10", 4, (2, 3)),
    ],
)
def test_failures_beyond_tolerance_report_data_loss(tmp_path, level, disks, failed):
    array_dir = make_array(tmp_path, level, disks, sample_bytes())
    for disk in failed:
        engine.fail_disk(array_dir, disk)

    result = engine.verify(array_dir)
    assert result["state"] == "Failed"
    assert result["data_loss"] is True
    assert result["match"] is False
    assert result["read_sha256"] is None
    with pytest.raises(engine.DataLossError):
        engine.read_file(array_dir)
    with pytest.raises(engine.DataLossError):
        engine.rebuild_disk(array_dir, failed[0])


def test_raid10_survives_one_failure_in_each_mirror_pair(tmp_path):
    data = sample_bytes()
    array_dir = make_array(tmp_path, "RAID 10", 4, data)
    engine.fail_disk(array_dir, 0)
    engine.fail_disk(array_dir, 3)
    assert engine.read_file(array_dir) == data


def test_raid5_parity_block_is_xor_of_data_blocks(tmp_path):
    array_dir = make_array(tmp_path, "RAID 5", 4, sample_bytes(), block_size=512)
    meta = engine.load_meta(array_dir)
    disks = [np.fromfile(engine.disk_path(array_dir, d), dtype=np.uint8).reshape(meta["rows"], 512)
             for d in range(4)]
    for row in range(meta["rows"]):
        roles = engine.row_roles("RAID 5", 4, row)
        parity_disk = next(d for d, (role, _) in enumerate(roles) if role == "parity")
        expected = np.zeros(512, dtype=np.uint8)
        for disk, (role, _) in enumerate(roles):
            if role == "data":
                expected ^= disks[disk][row]
        assert np.array_equal(disks[parity_disk][row], expected)


def test_raid5_parity_rotates_across_disks():
    parity_disks = [
        next(d for d, (role, _) in enumerate(engine.row_roles("RAID 5", 4, row)) if role == "parity")
        for row in range(4)
    ]
    assert sorted(parity_disks) == [0, 1, 2, 3]


def test_gf_inverse_and_scaling():
    for value in range(1, 256):
        assert engine.gf_scale(np.array([value], dtype=np.uint8), engine.gf_inverse(value))[0] == 1


def test_rebuild_requires_a_spare(tmp_path):
    array_dir = make_array(tmp_path, "RAID 5", 3, sample_bytes(), spares=0)
    engine.fail_disk(array_dir, 1)
    with pytest.raises(ValueError, match="No hot spare"):
        engine.rebuild_disk(array_dir, 1)


def test_invalid_configurations(tmp_path):
    with pytest.raises(ValueError):
        engine.create_array(tmp_path, b"x", "f", "RAID 5", 2, 512, 0)
    with pytest.raises(ValueError):
        engine.create_array(tmp_path, b"x", "f", "RAID 6", 3, 512, 0)
    with pytest.raises(ValueError):
        engine.create_array(tmp_path, b"x", "f", "RAID 10", 5, 512, 0)
    with pytest.raises(ValueError):
        engine.create_array(tmp_path, b"", "f", "RAID 0", 2, 512, 0)
    with pytest.raises(FileNotFoundError):
        engine.resolve_array_dir(tmp_path, "../etc")


def test_layout_reports_real_blocks(tmp_path):
    array_dir = make_array(tmp_path, "RAID 6", 4, sample_bytes(4096), block_size=512)
    engine.fail_disk(array_dir, 2)
    result = engine.layout(array_dir)
    first = result["layout_rows"][0]["cells"]
    assert [cell["label"] for cell in first] == ["P1", "Q1", "D1", "D2"]
    assert first[2]["preview"] is None
    assert first[3]["preview"] is not None
    assert result["state"] == "Degraded"
