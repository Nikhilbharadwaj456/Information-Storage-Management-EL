import base64
import json
import os

import pytest
from fastapi.testclient import TestClient

from backend.app.main import app
from backend.app.routers import raid_array


client = TestClient(app)


@pytest.fixture(autouse=True)
def isolated_workspace(tmp_path, monkeypatch):
    monkeypatch.setattr(raid_array, "WORKSPACE", tmp_path)
    monkeypatch.setattr(raid_array, "REBUILD_SECONDS", 0)


def create(level="RAID 5", disks=4, spares=1, data=None):
    payload = data or os.urandom(20_000)
    response = client.post("/api/raid/array", json={
        "raid_level": level,
        "disk_count": disks,
        "block_size": 1024,
        "hot_spares": spares,
        "filename": "demo.bin",
        "content_base64": base64.b64encode(payload).decode(),
    })
    assert response.status_code == 200, response.text
    return response.json()


def test_demo_flow_raid5_fail_rebuild_verify():
    array = create()
    array_id = array["id"]
    assert array["state"] == "Healthy"

    failed = client.post(f"/api/raid/array/{array_id}/fail/1").json()
    assert failed["state"] == "Degraded"
    assert client.get(f"/api/raid/array/{array_id}/verify").json()["match"] is True

    response = client.post(f"/api/raid/array/{array_id}/rebuild/1")
    lines = [json.loads(line) for line in response.text.splitlines()]
    assert lines[-2]["done"] == lines[-2]["total"]
    assert lines[-1]["complete"] is True
    assert lines[-1]["array"]["state"] == "Healthy"
    assert lines[-1]["array"]["spares_available"] == 0

    verify = client.get(f"/api/raid/array/{array_id}/verify").json()
    assert verify["match"] is True


def test_raid5_two_failures_is_data_loss_but_raid6_recovers():
    raid5 = create("RAID 5", 4)["id"]
    client.post(f"/api/raid/array/{raid5}/fail/0")
    client.post(f"/api/raid/array/{raid5}/fail/2")
    result = client.get(f"/api/raid/array/{raid5}/verify").json()
    assert result["data_loss"] is True
    assert client.post(f"/api/raid/array/{raid5}/rebuild/0").status_code == 422

    raid6 = create("RAID 6", 5)["id"]
    client.post(f"/api/raid/array/{raid6}/fail/0")
    client.post(f"/api/raid/array/{raid6}/fail/2")
    assert client.get(f"/api/raid/array/{raid6}/verify").json()["match"] is True


def test_errors():
    assert client.get("/api/raid/array/000000000000").status_code == 404
    bad = client.post("/api/raid/array", json={
        "raid_level": "RAID 5", "disk_count": 2, "block_size": 1024,
        "content_base64": base64.b64encode(b"abc").decode(),
    })
    assert bad.status_code == 422
    array_id = create()["id"]
    assert client.post(f"/api/raid/array/{array_id}/rebuild/0").status_code == 422
    assert client.delete(f"/api/raid/array/{array_id}").status_code == 200
    assert client.get(f"/api/raid/array/{array_id}").status_code == 404
