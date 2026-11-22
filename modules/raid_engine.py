from __future__ import annotations

import hashlib
import json
import math
import re
import uuid
from collections.abc import Callable, Iterator
from pathlib import Path

import numpy as np


LEVELS = ("RAID 0", "RAID 1", "RAID 5", "RAID 6", "RAID 10")
BLOCK_SIZES = (512, 1024, 4096, 16384, 65536)
MAX_DISKS = 8
MAX_SPARES = 2
MAX_FILE_BYTES = 5 * 1024 * 1024
META_FILE = "meta.json"
ARRAY_ID_PATTERN = re.compile(r"[0-9a-f]{12}")


class DataLossError(ValueError):
    """Raised when more disks have failed than the RAID level can tolerate."""


def _build_gf_tables() -> tuple[np.ndarray, np.ndarray]:
    exp = np.zeros(512, dtype=np.int32)
    log = np.zeros(256, dtype=np.int32)
    value = 1
    for power in range(255):
        exp[power] = value
        log[value] = power
        value <<= 1
        if value & 0x100:
            value ^= 0x11D
    exp[255:510] = exp[0:255]
    return exp, log


GF_EXP, GF_LOG = _build_gf_tables()


def gf_pow2(power: int) -> int:
    """Return g^power in GF(2^8) with generator g = 2."""
    return int(GF_EXP[power % 255])


def gf_inverse(value: int) -> int:
    """Return the multiplicative inverse of a non-zero GF(2^8) element."""
    if value == 0:
        raise ZeroDivisionError("Zero has no inverse in GF(2^8).")
    return int(GF_EXP[(255 - GF_LOG[value]) % 255])


def gf_scale(block: np.ndarray, coefficient: int) -> np.ndarray:
    """Multiply every byte of a block by a GF(2^8) coefficient."""
    result = np.zeros_like(block)
    if coefficient == 0:
        return result
    nonzero = block != 0
    result[nonzero] = GF_EXP[GF_LOG[block[nonzero]] + GF_LOG[coefficient]]
    return result


def xor_parity(blocks: list[np.ndarray], block_size: int) -> np.ndarray:
    """Return the XOR (P parity) of a list of blocks."""
    result = np.zeros(block_size, dtype=np.uint8)
    for block in blocks:
        result ^= block
    return result


def q_parity(blocks: list[np.ndarray], indexes: list[int], block_size: int) -> np.ndarray:
    """Return the Reed-Solomon Q parity: sum of g^i * D_i over GF(2^8)."""
    result = np.zeros(block_size, dtype=np.uint8)
    for block, index in zip(blocks, indexes):
        result ^= gf_scale(block, gf_pow2(index))
    return result


def validate_config(level: str, disks: int, block_size: int, spares: int) -> None:
    """Raise ValueError when the array configuration is not allowed."""
    if level not in LEVELS:
        raise ValueError(f"Unsupported RAID level. Choose one of {', '.join(LEVELS)}.")
    minimum = {"RAID 0": 2, "RAID 1": 2, "RAID 5": 3, "RAID 6": 4, "RAID 10": 4}[level]
    if disks < minimum:
        raise ValueError(f"{level} requires at least {minimum} disks.")
    if disks > MAX_DISKS:
        raise ValueError(f"The live simulator supports at most {MAX_DISKS} disks.")
    if level == "RAID 1" and disks != 2:
        raise ValueError("RAID 1 in the live simulator is a two-disk mirror. Use RAID 10 for more disks.")
    if level == "RAID 10" and disks % 2:
        raise ValueError("RAID 10 requires an even number of disks.")
    if block_size not in BLOCK_SIZES:
        raise ValueError(f"Stripe unit must be one of {', '.join(map(str, BLOCK_SIZES))} bytes.")
    if not 0 <= spares <= MAX_SPARES:
        raise ValueError(f"Hot spares must be between 0 and {MAX_SPARES}.")


def data_blocks_per_row(level: str, disks: int) -> int:
    """Return how many data blocks one stripe row holds."""
    return {
        "RAID 0": disks,
        "RAID 1": 1,
        "RAID 5": disks - 1,
        "RAID 6": disks - 2,
        "RAID 10": disks // 2,
    }[level]


def fault_tolerance(level: str, disks: int) -> int:
    """Return the number of disk failures the level always survives."""
    return {"RAID 0": 0, "RAID 1": 1, "RAID 5": 1, "RAID 6": 2, "RAID 10": 1}[level]


def row_roles(level: str, disks: int, row: int) -> list[tuple[str, int]]:
    """Return (role, data index) for every disk in a stripe row."""
    if level == "RAID 0":
        return [("data", disk) for disk in range(disks)]
    if level in ("RAID 1", "RAID 10"):
        return [("data" if disk % 2 == 0 else "mirror", disk // 2) for disk in range(disks)]
    p_disk = row % disks
    q_disk = (row + 1) % disks if level == "RAID 6" else -1
    roles: list[tuple[str, int]] = []
    data_index = 0
    for disk in range(disks):
        if disk == p_disk:
            roles.append(("parity", -1))
        elif disk == q_disk:
            roles.append(("q", -1))
        else:
            roles.append(("data", data_index))
            data_index += 1
    return roles


def is_recoverable(level: str, disks: int, missing: set[int]) -> bool:
    """Return True if the data survives the given set of missing disks."""
    if level == "RAID 0":
        return not missing
    if level in ("RAID 1", "RAID 10"):
        return not any(pair in missing and pair + 1 in missing for pair in range(0, disks, 2))
    return len(missing) <= fault_tolerance(level, disks)


def encode_row(level: str, disks: int, row: int, data: list[np.ndarray]) -> list[np.ndarray]:
    """Return the block each disk stores for one stripe row."""
    block_size = len(data[0])
    blocks: list[np.ndarray] = []
    for role, index in row_roles(level, disks, row):
        if role in ("data", "mirror"):
            blocks.append(data[index].copy())
        elif role == "parity":
            blocks.append(xor_parity(data, block_size))
        else:
            blocks.append(q_parity(data, list(range(len(data))), block_size))
    return blocks


def recover_row(level: str, disks: int, row: int, stored: list[np.ndarray | None]) -> list[np.ndarray]:
    """Rebuild every block of a stripe row from the surviving disks."""
    missing = {disk for disk, block in enumerate(stored) if block is None}
    if not missing:
        return [block for block in stored if block is not None]
    if not is_recoverable(level, disks, missing):
        raise DataLossError(f"{level} cannot survive the loss of disks {_disk_names(missing)}.")

    roles = row_roles(level, disks, row)
    block_size = next(len(block) for block in stored if block is not None)
    count = data_blocks_per_row(level, disks)
    data: list[np.ndarray | None] = [None] * count
    p_block = q_block = None
    for disk, (role, index) in enumerate(roles):
        block = stored[disk]
        if block is None:
            continue
        if role in ("data", "mirror"):
            data[index] = block
        elif role == "parity":
            p_block = block
        else:
            q_block = block

    lost = [index for index, block in enumerate(data) if block is None]
    if lost and level in ("RAID 5", "RAID 6"):
        known = [index for index in range(count) if data[index] is not None]
        known_blocks = [data[index] for index in known]
        if len(lost) == 1 and p_block is not None:
            data[lost[0]] = p_block ^ xor_parity(known_blocks, block_size)
        elif len(lost) == 1 and q_block is not None:
            partial = q_block ^ q_parity(known_blocks, known, block_size)
            data[lost[0]] = gf_scale(partial, gf_inverse(gf_pow2(lost[0])))
        else:
            x, y = lost
            p_xy = p_block ^ xor_parity(known_blocks, block_size)
            q_xy = q_block ^ q_parity(known_blocks, known, block_size)
            denominator = gf_pow2(x) ^ gf_pow2(y)
            numerator = q_xy ^ gf_scale(p_xy, gf_pow2(y))
            data[x] = gf_scale(numerator, gf_inverse(denominator))
            data[y] = p_xy ^ data[x]

    return encode_row(level, disks, row, [block for block in data if block is not None])


def _disk_names(disks: set[int] | list[int]) -> str:
    return ", ".join(f"Disk {disk + 1}" for disk in sorted(disks))


def disk_path(array_dir: Path, disk: int) -> Path:
    return array_dir / f"disk_{disk}.bin"


def spare_path(array_dir: Path, spare: int) -> Path:
    return array_dir / f"spare_{spare}.bin"


def resolve_array_dir(root: Path, array_id: str) -> Path:
    """Return the directory of an existing array, rejecting malformed ids."""
    if not ARRAY_ID_PATTERN.fullmatch(array_id):
        raise FileNotFoundError("Unknown array id.")
    array_dir = root / array_id
    if not (array_dir / META_FILE).exists():
        raise FileNotFoundError("Unknown array id.")
    return array_dir


def load_meta(array_dir: Path) -> dict:
    return json.loads((array_dir / META_FILE).read_text())


def save_meta(array_dir: Path, meta: dict) -> None:
    (array_dir / META_FILE).write_text(json.dumps(meta, indent=2))


def create_array(root: Path, data: bytes, filename: str, level: str, disks: int,
                 block_size: int, spares: int) -> dict:
    """Stripe a file across disk files under root and return the array metadata."""
    validate_config(level, disks, block_size, spares)
    if not data:
        raise ValueError("The uploaded file is empty.")
    if len(data) > MAX_FILE_BYTES:
        raise ValueError(f"Files must be at most {MAX_FILE_BYTES // (1024 * 1024)} MB.")

    per_row = data_blocks_per_row(level, disks)
    rows = math.ceil(len(data) / (per_row * block_size))
    padded = data + bytes(rows * per_row * block_size - len(data))
    blocks = np.frombuffer(padded, dtype=np.uint8).reshape(rows * per_row, block_size)
    disk_data = np.zeros((disks, rows, block_size), dtype=np.uint8)
    for row in range(rows):
        encoded = encode_row(level, disks, row, list(blocks[row * per_row:(row + 1) * per_row]))
        for disk, block in enumerate(encoded):
            disk_data[disk, row] = block

    array_id = uuid.uuid4().hex[:12]
    array_dir = root / array_id
    array_dir.mkdir(parents=True)
    for disk in range(disks):
        disk_data[disk].tofile(disk_path(array_dir, disk))
    for spare in range(spares):
        spare_path(array_dir, spare).write_bytes(bytes(rows * block_size))

    meta = {
        "id": array_id,
        "filename": filename,
        "level": level,
        "disks": disks,
        "block_size": block_size,
        "rows": rows,
        "size": len(data),
        "sha256": hashlib.sha256(data).hexdigest(),
        "spares_total": spares,
        "spares_used": 0,
        "events": [f"Created {level} with {disks} disks and {spares} hot spare(s)."],
    }
    save_meta(array_dir, meta)
    return meta


def missing_disks(array_dir: Path, meta: dict) -> list[int]:
    """Return the disks whose backing file no longer exists."""
    return [disk for disk in range(meta["disks"]) if not disk_path(array_dir, disk).exists()]


def array_state(meta: dict, missing: list[int]) -> str:
    if not missing:
        return "Healthy"
    return "Degraded" if is_recoverable(meta["level"], meta["disks"], set(missing)) else "Failed"


def _load_disks(array_dir: Path, meta: dict) -> list[np.ndarray | None]:
    shape = (meta["rows"], meta["block_size"])
    return [
        np.fromfile(path, dtype=np.uint8).reshape(shape) if path.exists() else None
        for path in (disk_path(array_dir, disk) for disk in range(meta["disks"]))
    ]


def _row_blocks(disks: list[np.ndarray | None], row: int) -> list[np.ndarray | None]:
    return [None if disk is None else disk[row] for disk in disks]


def fail_disk(array_dir: Path, disk: int) -> dict:
    """Simulate a disk failure by deleting the disk's backing file."""
    meta = load_meta(array_dir)
    if not 0 <= disk < meta["disks"]:
        raise ValueError("Disk index is outside the array.")
    path = disk_path(array_dir, disk)
    if not path.exists():
        raise ValueError(f"Disk {disk + 1} has already failed.")
    path.unlink()
    missing = missing_disks(array_dir, meta)
    meta["events"].append(f"Disk {disk + 1} failed. Array is now {array_state(meta, missing).lower()}.")
    save_meta(array_dir, meta)
    return meta


def read_file(array_dir: Path) -> bytes:
    """Reassemble the original file, reconstructing missing blocks if possible."""
    meta = load_meta(array_dir)
    level, disks, rows = meta["level"], meta["disks"], meta["rows"]
    missing = set(missing_disks(array_dir, meta))
    if not is_recoverable(level, disks, missing):
        raise DataLossError(f"{level} cannot survive the loss of {_disk_names(missing)}.")
    stored = _load_disks(array_dir, meta)
    chunks: list[bytes] = []
    for row in range(rows):
        blocks = recover_row(level, disks, row, _row_blocks(stored, row))
        roles = row_roles(level, disks, row)
        ordered = sorted(
            (index, disk) for disk, (role, index) in enumerate(roles) if role == "data"
        )
        chunks.extend(blocks[disk].tobytes() for _, disk in ordered)
    return b"".join(chunks)[:meta["size"]]


def verify(array_dir: Path) -> dict:
    """Read the array back and compare its SHA-256 with the original file."""
    meta = load_meta(array_dir)
    missing = missing_disks(array_dir, meta)
    state = array_state(meta, missing)
    result = {
        "state": state,
        "missing_disks": missing,
        "original_sha256": meta["sha256"],
        "read_sha256": None,
        "match": False,
        "data_loss": state == "Failed",
        "message": "",
    }
    try:
        data = read_file(array_dir)
    except DataLossError as error:
        result["message"] = str(error)
        return result
    result["read_sha256"] = hashlib.sha256(data).hexdigest()
    result["match"] = result["read_sha256"] == meta["sha256"]
    if missing:
        result["message"] = f"Read in degraded mode: {_disk_names(missing)} reconstructed on the fly."
    else:
        result["message"] = "Read directly from all disks."
    return result


def rebuild_disk(array_dir: Path, disk: int) -> Iterator[tuple[int, int]]:
    """Validate, then return a generator that rebuilds a failed disk onto a hot spare."""
    meta = load_meta(array_dir)
    level, disks, rows = meta["level"], meta["disks"], meta["rows"]
    if not 0 <= disk < disks:
        raise ValueError("Disk index is outside the array.")
    missing = set(missing_disks(array_dir, meta))
    if disk not in missing:
        raise ValueError(f"Disk {disk + 1} is healthy and does not need a rebuild.")
    if not is_recoverable(level, disks, missing):
        raise DataLossError(f"Rebuild impossible: {level} cannot survive the loss of {_disk_names(missing)}.")
    if meta["spares_used"] >= meta["spares_total"]:
        raise ValueError("No hot spare is available.")

    spare = meta["spares_used"]

    def run() -> Iterator[tuple[int, int]]:
        stored = _load_disks(array_dir, meta)
        target = spare_path(array_dir, spare)
        with target.open("r+b") as handle:
            for row in range(rows):
                blocks = recover_row(level, disks, row, _row_blocks(stored, row))
                handle.write(blocks[disk].tobytes())
                yield row + 1, rows
        target.rename(disk_path(array_dir, disk))
        meta["spares_used"] = spare + 1
        meta["events"].append(f"Hot spare {spare + 1} rebuilt as Disk {disk + 1} ({rows} stripe rows).")
        save_meta(array_dir, meta)

    return run()


def layout(array_dir: Path, max_rows: int = 12) -> dict:
    """Return the block map of the array with a byte preview from each disk file."""
    meta = load_meta(array_dir)
    level, disks = meta["level"], meta["disks"]
    missing = missing_disks(array_dir, meta)
    stored = _load_disks(array_dir, meta)
    per_row = data_blocks_per_row(level, disks)
    rows = []
    for row in range(min(meta["rows"], max_rows)):
        cells = []
        for disk, (role, index) in enumerate(row_roles(level, disks, row)):
            number = row * per_row + index + 1
            label = {
                "data": f"D{number}",
                "mirror": f"D{number}′",
                "parity": f"P{row + 1}",
                "q": f"Q{row + 1}",
            }[role]
            block = stored[disk]
            cells.append({
                "disk": disk,
                "role": role,
                "label": label,
                "preview": None if block is None else block[row][:4].tobytes().hex(),
            })
        rows.append({"row": row + 1, "cells": cells})
    state = array_state(meta, missing)
    return {
        **{key: meta[key] for key in ("id", "filename", "level", "disks", "block_size", "rows", "size", "sha256")},
        "state": state,
        "missing_disks": missing,
        "fault_tolerance": fault_tolerance(level, disks),
        "usable_bytes": meta["rows"] * per_row * meta["block_size"],
        "raw_bytes": meta["rows"] * disks * meta["block_size"],
        "spares_available": meta["spares_total"] - meta["spares_used"],
        "spares_total": meta["spares_total"],
        "events": meta["events"],
        "layout_rows": rows,
        "rows_shown": len(rows),
    }


def progress_steps(rows: int, steps: int = 50) -> Callable[[int], bool]:
    """Return a predicate selecting about `steps` evenly spaced progress updates."""
    stride = max(1, rows // steps)
    return lambda done: done == rows or done % stride == 0
