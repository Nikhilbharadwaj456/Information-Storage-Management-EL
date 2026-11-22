from pydantic import BaseModel, Field


class RaidCalculateRequest(BaseModel):
    raid_level: str = Field(pattern=r"^RAID (0|1|5|6|10)$")
    disk_count: int = Field(ge=2, le=32)
    disk_size_tb: float = Field(gt=0)


class RaidFailureRequest(BaseModel):
    raid_level: str = Field(pattern=r"^RAID (0|1|5|6|10)$")
    disk_count: int = Field(ge=2, le=32)
    disk_size_tb: float = Field(gt=0)
    failed_disks: list[int] = Field(default_factory=list)
    hot_spare: bool = False
    rebuild_throughput_mb_s: float = Field(default=200.0, gt=0)


class XorRequest(BaseModel):
    a: str = Field(max_length=16)
    b: str = Field(max_length=16)
    c: str = Field(max_length=16)
    missing: str = Field(pattern=r"^(A|B|C)$")


class DiskRequest(BaseModel):
    rpm: float = Field(gt=0, le=30000)
    seek_ms: float = Field(ge=0)
    transfer_rate_mb_s: float = Field(gt=0)
    block_kb: float = Field(gt=0)
    arrival_iops: float = Field(ge=0)


class BackupRequest(BaseModel):
    data_size_gb: float = Field(gt=0)
    change_percent: float = Field(ge=0, le=100)
    retention_days: int = Field(ge=1, le=365)
    throughput_mb_s: float = Field(gt=0)
    rpo_hours: float = Field(gt=0)
    rto_hours: float = Field(gt=0)
    backup_interval_hours: float = Field(gt=0)


class ReplicationRequest(BaseModel):
    mode: str = Field(pattern=r"^(Synchronous|Asynchronous)$")
    local_write_ms: float = Field(ge=0)
    network_round_trip_ms: float = Field(ge=0)
    bandwidth_mbps: float = Field(gt=0)
    write_frequency_iops: float = Field(ge=0)
    distance_km: float = Field(default=0.0, ge=0, le=20000)
    write_size_kb: float = Field(default=8.0, gt=0)


class RiskRequest(BaseModel):
    asset: str = Field(min_length=1)
    threat: str = Field(min_length=1)
    vulnerability: str = Field(min_length=1)
    likelihood: int = Field(ge=1, le=5)
    impact: int = Field(ge=1, le=5)
