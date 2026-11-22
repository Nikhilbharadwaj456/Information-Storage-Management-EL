import pytest

from modules.backup import backup_comparison


def test_backup_storage_order():
    result = backup_comparison(1000, 5, 7, 100, 24, 4, 24)
    values = dict(zip(result["Strategy"], result["Storage (GB)"]))
    assert values["Incremental"] < values["Full"]
    assert values["Incremental"] < values["Differential"]


def test_larger_data_and_retention():
    short = backup_comparison(100, 10, 3, 100, 24, 4, 24)
    large = backup_comparison(500, 10, 3, 100, 24, 4, 24)
    long = backup_comparison(100, 10, 10, 100, 24, 4, 24)
    assert large["Storage (GB)"].sum() > short["Storage (GB)"].sum()
    assert long["Storage (GB)"].sum() > short["Storage (GB)"].sum()


def test_rpo_rto_columns():
    result = backup_comparison(1000, 5, 7, 100, 24, 0.1, 24)
    assert "RPO compliant" in result
    assert "RTO compliant" in result
    assert (result["RTO compliant"] == "No").all()


def test_invalid_backup_parameters():
    with pytest.raises(ValueError):
        backup_comparison(0, 5, 7, 100, 24, 4, 24)
    with pytest.raises(ValueError):
        backup_comparison(100, 101, 7, 100, 24, 4, 24)
