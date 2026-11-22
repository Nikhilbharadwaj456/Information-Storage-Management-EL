from fastapi import APIRouter

from backend.app.schemas import ReplicationRequest
from modules.replication import replication_comparison
from modules.explainability import replication_explanation


router = APIRouter(prefix="/api/replication", tags=["Replication"])


@router.post("/compare")
async def compare(request: ReplicationRequest) -> dict:
    selected = replication_comparison(
        request.mode,
        request.local_write_ms,
        request.network_round_trip_ms,
        request.bandwidth_mbps,
        request.write_frequency_iops,
    )
    synchronous = replication_comparison(
        "Synchronous",
        request.local_write_ms,
        request.network_round_trip_ms,
        request.bandwidth_mbps,
        request.write_frequency_iops,
    )
    asynchronous = replication_comparison(
        "Asynchronous",
        request.local_write_ms,
        request.network_round_trip_ms,
        request.bandwidth_mbps,
        request.write_frequency_iops,
    )
    return {
        "selected": selected,
        "comparison": [synchronous, asynchronous],
        "units": {
            "response_time": "ms",
            "replication_lag": "ms",
        },
        "assumptions": [
            "Synchronous writes wait for remote acknowledgement",
            "Asynchronous writes acknowledge locally without waiting",
        ],
        "explanation": replication_explanation(selected, request.mode),
    }
