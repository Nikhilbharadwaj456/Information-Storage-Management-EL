from __future__ import annotations

from modules.backup import backup_comparison, recommend_strategy
from modules.disk_performance import calculate_disk, response_time_curve
from modules.raid import array_state, calculate_raid, rebuild_time, xor_recover
from modules.replication import replication_comparison
from modules.risk_assessment import calculate_risk, risk_category


def raid_service(raid_level: str, disk_count: int, disk_size_tb: float,
                 failed_disks: set[int] | None = None) -> dict:
    result = calculate_raid(raid_level, disk_count, disk_size_tb)
    failed = failed_disks or set()
    result["array_state"] = array_state(raid_level, disk_count, failed)
    result["failed_disks"] = sorted(failed)
    return result


def disk_service(rpm: float, seek_ms: float, transfer_rate_mb_s: float,
                 block_kb: float, arrival_iops: float) -> dict:
    result = calculate_disk(rpm, seek_ms, transfer_rate_mb_s, block_kb, arrival_iops)
    curve = response_time_curve(result["service_time_ms"])
    result["response_curve"] = curve.to_dict(orient="records")
    return result


def backup_service(data_size_gb: float, change_percent: float, retention_days: int,
                   throughput_mb_s: float, rpo_hours: float, rto_hours: float,
                   backup_interval_hours: float) -> dict:
    comparison = backup_comparison(
        data_size_gb,
        change_percent,
        retention_days,
        throughput_mb_s,
        rpo_hours,
        rto_hours,
        backup_interval_hours,
    )
    return {
        "strategies": comparison.to_dict(orient="records"),
        "recommendation": recommend_strategy(comparison, rpo_hours, rto_hours),
    }


__all__ = [
    "array_state",
    "backup_service",
    "calculate_risk",
    "disk_service",
    "raid_service",
    "rebuild_time",
    "replication_comparison",
    "risk_category",
    "xor_recover",
]
