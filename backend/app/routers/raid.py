from fastapi import APIRouter

from backend.app.schemas import RaidCalculateRequest, RaidFailureRequest, XorRequest
from modules.raid import (
    array_state,
    build_layout,
    calculate_raid,
    raid_comparison,
    rebuild_time,
    remaining_fault_tolerance,
    xor_demo,
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
    recoverable = bool(failed) and state == "Degraded"
    rebuilding = request.hot_spare and recoverable
    data_to_rebuild_tb = request.disk_size_tb * len(failed) if recoverable else 0.0

    rebuild_hours = rebuild_time(
        data_to_rebuild_tb,
        request.rebuild_throughput_mb_s,
    ) if recoverable else 0.0
    return {
        **base,
        "array_state": "Rebuilding" if rebuilding else state,
        "failed_disks": sorted(failed),
        "data_accessible": state != "Failed",
        "remaining_fault_tolerance": remaining_fault_tolerance(
            request.raid_level, request.disk_count, failed,
        ),
        "hot_spare_active": rebuilding,
        "data_to_rebuild_tb": data_to_rebuild_tb,
        "rebuild_throughput_mb_s": request.rebuild_throughput_mb_s,
        "rebuild_time_hours": rebuild_hours,
        "comparison": raid_comparison(request.disk_count, request.disk_size_tb).to_dict(orient="records"),
        "layout": build_layout(
            request.raid_level,
            request.disk_count,
            failed,
        ).to_dict(orient="records"),
        "explanation": raid_explanation(
            base,
            "Rebuilding" if rebuilding else state,
            rebuild_hours,
            len(failed),
            rebuilding,
        ),
    }


@router.post("/xor")
async def xor(request: XorRequest) -> dict:
    blocks = {}
    for name, value in (("A", request.a), ("B", request.b), ("C", request.c)):
        if not value or any(bit not in "01" for bit in value):
            raise ValueError(f"Block {name} must be a binary value such as 1010.")
        blocks[name] = int(value, 2)
    width = max(len(request.a), len(request.b), len(request.c))
    result = xor_demo(blocks, request.missing)
    return {
        "blocks": {name: format(value, f"0{width}b") for name, value in blocks.items()},
        "parity": format(result["parity"], f"0{width}b"),
        "missing": result["missing"],
        "recovered": format(result["recovered"], f"0{width}b"),
        "verified": result["verified"],
        "survivors": [name for name in blocks if name != request.missing],
    }
