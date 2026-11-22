from fastapi import APIRouter

from backend.app.schemas import DiskRequest
from modules.disk_performance import calculate_disk, response_time_curve
from modules.explainability import disk_explanation


router = APIRouter(prefix="/api/disk", tags=["Disk Performance"])


@router.post("/analyze")
async def analyze(request: DiskRequest) -> dict:
    result = calculate_disk(
        request.rpm,
        request.seek_ms,
        request.transfer_rate_mb_s,
        request.block_kb,
        request.arrival_iops,
    )
    curve = response_time_curve(result["service_time_ms"])
    return {
        **result,
        "utilization_percent": result["utilization"] * 100,
        "response_curve": curve.to_dict(orient="records"),
        "units": {
            "latency": "ms",
            "service_time": "ms",
            "response_time": "ms",
            "iops": "IOPS",
        },
        "assumptions": [
            "Simplified single-server M/M/1 queue model",
            "No response-time result is returned when utilization is 100% or higher",
        ],
        "explanation": disk_explanation(result, request.arrival_iops),
    }
