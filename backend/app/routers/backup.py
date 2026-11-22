from fastapi import APIRouter

from backend.app.schemas import BackupRequest
from modules.backup import backup_comparison, recommend_strategy
from modules.explainability import backup_explanation


router = APIRouter(prefix="/api/backup", tags=["Backup"])


@router.post("/compare")
async def compare(request: BackupRequest) -> dict:
    comparison = backup_comparison(
        request.data_size_gb,
        request.change_percent,
        request.retention_days,
        request.throughput_mb_s,
        request.rpo_hours,
        request.rto_hours,
        request.backup_interval_hours,
    )
    recommendation = recommend_strategy(
        comparison,
        request.rpo_hours,
        request.rto_hours,
    )
    return {
        "strategies": comparison.to_dict(orient="records"),
        "recommendation": recommendation,
        "backup_interval_hours": request.backup_interval_hours,
        "rpo_hours": request.rpo_hours,
        "rto_hours": request.rto_hours,
        "units": {
            "storage": "GB",
            "duration": "hours",
        },
        "assumptions": [
            "Fixed daily changed data",
            "One initial full backup",
            "Fixed throughput",
            "Differential cumulative data is capped at original dataset size",
        ],
        "explanation": backup_explanation(
            comparison.to_dict(orient="records"),
            recommendation,
            request.rpo_hours,
            request.rto_hours,
            request.backup_interval_hours,
        ),
    }
