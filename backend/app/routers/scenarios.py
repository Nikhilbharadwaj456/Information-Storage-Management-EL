import csv
import io

from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session

from backend.app.database import get_db
from backend.app.models import Scenario
from backend.app.schemas_scenarios import (
    ScenarioComparison,
    ScenarioCreate,
    ScenarioResponse,
    ScenarioUpdate,
)


router = APIRouter(prefix="/api/scenarios", tags=["Scenarios"])


def get_scenario(db: Session, scenario_id: int) -> Scenario:
    scenario = db.get(Scenario, scenario_id)
    if scenario is None:
        raise HTTPException(status_code=404, detail="Scenario not found.")
    return scenario


@router.post("", response_model=ScenarioResponse)
async def create_scenario(payload: ScenarioCreate, db: Session = Depends(get_db)):
    scenario = Scenario(**payload.model_dump())
    db.add(scenario)
    db.commit()
    db.refresh(scenario)
    return scenario


@router.get("", response_model=list[ScenarioResponse])
async def list_scenarios(db: Session = Depends(get_db)):
    return db.query(Scenario).order_by(Scenario.updated_at.desc()).all()


@router.get("/export/csv")
async def export_scenarios_csv(db: Session = Depends(get_db)):
    scenarios = db.query(Scenario).order_by(Scenario.id).all()
    output = io.StringIO()
    writer = csv.writer(output)
    writer.writerow(["id", "name", "module_type", "inputs", "results", "assumptions", "tags"])
    for scenario in scenarios:
        writer.writerow([
            scenario.id,
            scenario.name,
            scenario.module_type,
            str(scenario.inputs),
            str(scenario.results),
            str(scenario.assumptions),
            str(scenario.tags),
        ])
    output.seek(0)
    return StreamingResponse(
        iter([output.getvalue()]),
        media_type="text/csv",
        headers={"Content-Disposition": "attachment; filename=storagelab-scenarios.csv"},
    )


@router.get("/{scenario_id}", response_model=ScenarioResponse)
async def get_scenario_api(scenario_id: int, db: Session = Depends(get_db)):
    return get_scenario(db, scenario_id)


@router.patch("/{scenario_id}", response_model=ScenarioResponse)
async def update_scenario(
    scenario_id: int,
    payload: ScenarioUpdate,
    db: Session = Depends(get_db),
):
    scenario = get_scenario(db, scenario_id)
    for key, value in payload.model_dump(exclude_unset=True).items():
        setattr(scenario, key, value)
    db.commit()
    db.refresh(scenario)
    return scenario


@router.delete("/{scenario_id}")
async def delete_scenario(scenario_id: int, db: Session = Depends(get_db)):
    scenario = get_scenario(db, scenario_id)
    db.delete(scenario)
    db.commit()
    return {"deleted": scenario_id}


@router.post("/{scenario_id}/clone", response_model=ScenarioResponse)
async def clone_scenario(scenario_id: int, db: Session = Depends(get_db)):
    source = get_scenario(db, scenario_id)
    clone = Scenario(
        name=f"{source.name} (Copy)",
        module_type=source.module_type,
        inputs=dict(source.inputs),
        results=dict(source.results),
        assumptions=list(source.assumptions),
        tags=list(source.tags),
    )
    db.add(clone)
    db.commit()
    db.refresh(clone)
    return clone


@router.post("/compare")
async def compare_scenarios(
    payload: ScenarioComparison,
    db: Session = Depends(get_db),
):
    unique_ids = list(dict.fromkeys(payload.scenario_ids))
    if len(unique_ids) != len(payload.scenario_ids):
        raise HTTPException(status_code=422, detail="Scenario IDs must be unique.")
    return [
        get_scenario(db, scenario_id)
        for scenario_id in payload.scenario_ids
    ]


