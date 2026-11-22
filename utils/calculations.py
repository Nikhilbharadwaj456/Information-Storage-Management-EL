from __future__ import annotations


def gb_to_mb(value_gb: float) -> float:
    return value_gb * 1024.0


def mb_to_gb(value_mb: float) -> float:
    return value_mb / 1024.0


def hours_to_seconds(value_hours: float) -> float:
    return value_hours * 3600.0


def validate_positive(name: str, value: float) -> None:
    if value is None or value <= 0:
        raise ValueError(f"{name} must be greater than zero.")
