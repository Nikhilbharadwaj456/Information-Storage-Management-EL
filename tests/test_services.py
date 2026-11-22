from utils.storage_services import backup_service, disk_service, raid_service


def test_raid_service_includes_state():
    result = raid_service("RAID 5", 4, 1.0, {0})
    assert result["usable_capacity_tb"] == 3
    assert result["array_state"] == "Degraded"
    assert result["failed_disks"] == [0]


def test_disk_service_includes_response_curve():
    result = disk_service(7200, 4, 150, 4, 100)
    assert len(result["response_curve"]) == 91
    assert result["requests_in_system"] >= 0


def test_backup_service_includes_records_and_recommendation():
    result = backup_service(1000, 5, 7, 100, 24, 4, 24)
    assert len(result["strategies"]) == 3
    assert isinstance(result["recommendation"], str)
