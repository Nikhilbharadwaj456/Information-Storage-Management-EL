import base64
import json
import os
import shutil
import time
from pathlib import Path

from fastapi import APIRouter, HTTPException
from fastapi.responses import StreamingResponse
from pydantic import BaseModel, Field

from modules import raid_engine as engine


WORKSPACE = Path(os.environ.get(
    "STORAGELAB_WORKSPACE",
    Path(__file__).resolve().parents[3] / "workspace",
))
REBUILD_SECONDS = 2.5

router = APIRouter(prefix="/api/raid/array", tags=["RAID live array"])


class CreateArrayRequest(BaseModel):
    raid_level: str
    disk_count: int = Field(ge=2, le=engine.MAX_DISKS)
    block_size: int
    hot_spares: int = Field(default=1, ge=0, le=engine.MAX_SPARES)
    filename: str = Field(default="upload.bin", max_length=200)
    content_base64: str


def _array_dir(array_id: str) -> Path:
    try:
        return engine.resolve_array_dir(WORKSPACE, array_id)
    except FileNotFoundError as error:
        raise HTTPException(status_code=404, detail=str(error)) from error


@router.post("")
async def create_array(request: CreateArrayRequest) -> dict:
    data = base64.b64decode(request.content_base64, validate=True)
    meta = engine.create_array(
        WORKSPACE,
        data,
        request.filename,
        request.raid_level,
        request.disk_count,
        request.block_size,
        request.hot_spares,
    )
    return engine.layout(WORKSPACE / meta["id"])


@router.get("/{array_id}")
async def get_array(array_id: str) -> dict:
    return engine.layout(_array_dir(array_id))


@router.post("/{array_id}/fail/{disk}")
async def fail_disk(array_id: str, disk: int) -> dict:
    array_dir = _array_dir(array_id)
    engine.fail_disk(array_dir, disk)
    return engine.layout(array_dir)


@router.get("/{array_id}/verify")
async def verify(array_id: str) -> dict:
    return engine.verify(_array_dir(array_id))


@router.post("/{array_id}/rebuild/{disk}")
def rebuild(array_id: str, disk: int) -> StreamingResponse:
    array_dir = _array_dir(array_id)
    steps = engine.rebuild_disk(array_dir, disk)
    rows = engine.load_meta(array_dir)["rows"]
    report = engine.progress_steps(rows)
    delay = REBUILD_SECONDS / rows

    def stream():
        for done, total in steps:
            time.sleep(delay)
            if report(done):
                yield json.dumps({"done": done, "total": total}) + "\n"
        yield json.dumps({"complete": True, "array": engine.layout(array_dir)}) + "\n"

    return StreamingResponse(stream(), media_type="application/x-ndjson")


@router.delete("/{array_id}")
async def delete_array(array_id: str) -> dict:
    shutil.rmtree(_array_dir(array_id))
    return {"deleted": array_id}
