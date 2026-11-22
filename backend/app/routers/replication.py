from fastapi import APIRouter

from backend.app.schemas import ReplicationRequest
from modules.replication import replication_comparison
from modules.explainability import replication_explanation


router = APIRouter(prefix="/api/replication", tags=["Replication"])


@router.post("/compare")
async def compare(request: ReplicationRequest) -> dict:
    args = (
        request.local_write_ms,
        request.network_round_trip_ms,
        request.bandwidth_mbps,
        request.write_frequency_iops,
        request.distance_km,
        request.write_size_kb,
    )
    selected = replication_comparison(request.mode, *args)
    synchronous = replication_comparison("Synchronous", *args)
    asynchronous = replication_comparison("Asynchronous", *args)
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
            "Signal propagation is 5 microseconds per km in each direction",
            "Each write is sent as one transfer of the given size over the link",
        ],
        "explanation": replication_explanation(selected, request.mode),
    }
