from fastapi.testclient import TestClient

from backend.app.main import app


client = TestClient(app)


def test_health():
    response = client.get("/api/health")
    assert response.status_code == 200
    assert response.json()["status"] == "healthy"


def test_raid_calculate():
    response = client.post(
        "/api/raid/calculate",
        json={"raid_level": "RAID 5", "disk_count": 4, "disk_size_tb": 1},
    )
    assert response.status_code == 200
    body = response.json()
    assert body["usable_capacity_tb"] == 3
    assert body["array_state"] == "Healthy"
    assert body["explanation"]["summary"]
    assert body["explanation"]["formula"]
    assert body["explanation"]["contributing_factors"]


def test_raid_failure_and_invalid_disk():
    response = client.post(
        "/api/raid/simulate-failure",
        json={
            "raid_level": "RAID 5",
            "disk_count": 4,
            "disk_size_tb": 1,
            "failed_disks": [0, 1],
            "hot_spare": True,
            "rebuild_throughput_mb_s": 200,
        },
    )
    assert response.status_code == 200
    assert response.json()["array_state"] in ("Failed", "Rebuilding")

    invalid = client.post(
        "/api/raid/simulate-failure",
        json={
            "raid_level": "RAID 5",
            "disk_count": 4,
            "disk_size_tb": 1,
            "failed_disks": [4],
        },
    )
    assert invalid.status_code == 422


def test_disk_analyze():
    response = client.post(
        "/api/disk/analyze",
        json={
            "rpm": 7200,
            "seek_ms": 4,
            "transfer_rate_mb_s": 150,
            "block_kb": 4,
            "arrival_iops": 100,
        },
    )
    assert response.status_code == 200
    assert len(response.json()["response_curve"]) == 91


def test_disk_rejects_unstable_utilization():
    response = client.post(
        "/api/disk/analyze",
        json={
            "rpm": 7200,
            "seek_ms": 4,
            "transfer_rate_mb_s": 150,
            "block_kb": 4,
            "arrival_iops": 1000,
        },
    )
    assert response.status_code == 422


def test_backup_compare():
    response = client.post(
        "/api/backup/compare",
        json={
            "data_size_gb": 1000,
            "change_percent": 5,
            "retention_days": 7,
            "throughput_mb_s": 100,
            "rpo_hours": 24,
            "rto_hours": 4,
            "backup_interval_hours": 24,
        },
    )
    assert response.status_code == 200
    assert len(response.json()["strategies"]) == 3


def test_replication_and_risk():
    replication = client.post(
        "/api/replication/compare",
        json={
            "mode": "Synchronous",
            "local_write_ms": 2,
            "network_round_trip_ms": 20,
            "bandwidth_mbps": 1000,
            "write_frequency_iops": 500,
        },
    )
    assert replication.status_code == 200

    risk = client.post(
        "/api/risk/calculate",
        json={
            "asset": "Stored data",
            "threat": "Ransomware",
            "vulnerability": "Unencrypted backups",
            "likelihood": 5,
            "impact": 5,
        },
    )
    assert risk.status_code == 200
    assert risk.json()["risk_category"] == "Critical"


def test_invalid_request_parameters():
    response = client.post(
        "/api/disk/analyze",
        json={
            "rpm": 0,
            "seek_ms": -1,
            "transfer_rate_mb_s": 0,
            "block_kb": 0,
            "arrival_iops": -1,
        },
    )
    assert response.status_code == 422


def test_failed_array_is_never_reported_as_rebuilding():
    for level, failed in (("RAID 0", [1]), ("RAID 5", [0, 1])):
        body = client.post("/api/raid/simulate-failure", json={
            "raid_level": level, "disk_count": 4, "disk_size_tb": 1,
            "failed_disks": failed, "hot_spare": True,
        }).json()
        assert body["array_state"] == "Failed"
        assert body["hot_spare_active"] is False
        assert body["data_accessible"] is False
        assert body["rebuild_time_hours"] == 0


def test_degraded_array_with_spare_rebuilds_failed_data():
    body = client.post("/api/raid/simulate-failure", json={
        "raid_level": "RAID 6", "disk_count": 5, "disk_size_tb": 2,
        "failed_disks": [0, 3], "hot_spare": True, "rebuild_throughput_mb_s": 200,
    }).json()
    assert body["array_state"] == "Rebuilding"
    assert body["data_to_rebuild_tb"] == 4
    assert body["remaining_fault_tolerance"] == "0 disks"
    assert [row["RAID"] for row in body["comparison"]] == ["RAID 0", "RAID 5", "RAID 6"]


def test_xor_endpoint():
    body = client.post("/api/raid/xor", json={"a": "1010", "b": "1100", "c": "0110", "missing": "B"}).json()
    assert body["parity"] == "0000"
    assert body["recovered"] == "1100"
    assert body["verified"] is True
    bad = client.post("/api/raid/xor", json={"a": "10a0", "b": "1100", "c": "0110", "missing": "A"})
    assert bad.status_code == 422
