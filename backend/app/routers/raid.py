from fastapi import APIRouter

from backend.app.schemas import RaidCalculateRequest, RaidFailureRequest
from modules.raid import (
    array_state,
    build_layout,
    calculate_raid,
    rebuild_time,
    xor_recover,
)
from modules.explainability import raid_explanation


router = APIRouter(prefix="/api/raid", tags=["RAID"])


@router.post("/calculate")
async def calculate(request: RaidCalculateRequest) -> dict:
    result = calculate_raid(
        request.raid_level,
        request.disk_count,
        request.disk_size_tb,
    )
    layout = build_layout(request.raid_level, request.disk_count)
    rebuild_hours = 0.0
    return {
        **result,
        "array_state": "Healthy",
        "failed_disks": [],
        "layout": layout.to_dict(orient="records"),
        "units": {
            "capacity": "TB",
            "efficiency": "%",
        },
        "assumptions": [
            "Logical RAID simulation",
            "Relative read/write characteristics are not hardware benchmarks",
        ],
        "explanation": raid_explanation(result, "Healthy", rebuild_hours, 0, False),
    }


@router.post("/simulate-failure")
async def simulate_failure(request: RaidFailureRequest) -> dict:
    for disk in request.failed_disks:
        if disk < 0 or disk >= request.disk_count:
            raise ValueError("Failed disk index is outside the disk array.")

    failed = set(request.failed_disks)
    base = calculate_raid(
        request.raid_level,
        request.disk_count,
        request.disk_size_tb,
    )
    state = array_state(request.raid_level, request.disk_count, failed)
    rebuilding = request.hot_spare and failed and state in ("Degraded", "Failed")

    rebuild_hours = rebuild_time(
        request.disk_size_tb,
        request.rebuild_throughput_mb_s,
    ) if rebuilding or failed else 0.0
    return {
        **base,
        "array_state": "Rebuilding" if rebuilding else state,
        "failed_disks": sorted(failed),
        "hot_spare_active": rebuilding,
        "rebuild_time_hours": rebuild_hours,
        "layout": build_layout(
            request.raid_level,
            request.disk_count,
            failed,
        ).to_dict(orient="records"),
        "xor_example": {
            "a": "1010",
            "b": "1100",
            "c": "0110",
            "parity": format(
                xor_recover(0b1010, 0b1100, 0b0110)[0],
                "04b",
            ),
            "recovered_c": format(
                xor_recover(0b1010, 0b1100, 0b0110)[2],
                "04b",
            ),
        },
        "explanation": raid_explanation(
            base,
            "Rebuilding" if rebuilding else state,
            rebuild_hours,
            len(failed),
            rebuilding,
        ),
    }
