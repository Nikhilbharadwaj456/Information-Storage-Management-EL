from fastapi.testclient import TestClient

from backend.app.main import app
from backend.app.database import SessionLocal
from backend.app.models import Scenario


client = TestClient(app)


def clean_scenarios():
    db = SessionLocal()
    db.query(Scenario).delete()
    db.commit()
    db.close()


def create_scenario(name: str):
    return client.post(
        "/api/scenarios",
        json={
            "name": name,
            "module_type": "raid",
            "inputs": {"raid_level": "RAID 5", "disk_count": 4, "disk_size_tb": 1},
            "results": {"usable_capacity_tb": 3},
            "assumptions": ["Logical simulation"],
            "tags": ["test"],
        },
    )


def test_scenario_crud_and_clone():
    clean_scenarios()
    created = create_scenario("RAID Test")
    assert created.status_code == 200
    scenario = created.json()

    loaded = client.get(f"/api/scenarios/{scenario['id']}")
    assert loaded.status_code == 200

    updated = client.patch(
        f"/api/scenarios/{scenario['id']}",
        json={"name": "Updated RAID Test"},
    )
    assert updated.status_code == 200
    assert updated.json()["name"] == "Updated RAID Test"

    cloned = client.post(f"/api/scenarios/{scenario['id']}/clone")
    assert cloned.status_code == 200
    assert cloned.json()["name"] == "Updated RAID Test (Copy)"

    deleted = client.delete(f"/api/scenarios/{scenario['id']}")
    assert deleted.status_code == 200
    assert deleted.json()["deleted"] == scenario["id"]

    clean_scenarios()


def test_scenario_comparison_csv_and_missing_id():
    clean_scenarios()
    first = create_scenario("First").json()
    second = create_scenario("Second").json()

    compared = client.post(
        "/api/scenarios/compare",
        json={"scenario_ids": [first["id"], second["id"]]},
    )
    assert compared.status_code == 200
    assert len(compared.json()) == 2

    duplicate = client.post(
        "/api/scenarios/compare",
        json={"scenario_ids": [first["id"], first["id"]]},
    )
    assert duplicate.status_code == 422

    missing = client.get("/api/scenarios/999999")
    assert missing.status_code == 404

    csv_export = client.get("/api/scenarios/export/csv")
    assert csv_export.status_code == 200
    assert "text/csv" in csv_export.headers["content-type"]
    assert "storagelab-scenarios.csv" in csv_export.headers["content-disposition"]

    clean_scenarios()
