from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from fastapi.exceptions import RequestValidationError

from backend.app.routers import (
    raid,
    disk,
    backup,
    replication,
    risk,
)
from backend.app.database import Base, engine
from backend.app import models
from backend.app.routers.scenarios import router as scenarios_router


app = FastAPI(
    title="StorageLab API",
    description="REST API for the StorageLab storage simulation and analysis platform.",
    version="1.0.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:5173",
        "http://127.0.0.1:5173",
        "http://localhost",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.exception_handler(ValueError)
async def value_error_handler(request: Request, exc: ValueError) -> JSONResponse:
    return JSONResponse(status_code=422, content={"detail": str(exc)})


@app.exception_handler(RequestValidationError)
async def validation_error_handler(request: Request, exc: RequestValidationError) -> JSONResponse:
    return JSONResponse(
        status_code=422,
        content={"detail": exc.errors(), "message": "Invalid request parameters."},
    )


@app.get("/api/health")
async def health() -> dict:
    return {"status": "healthy", "service": "storagelab-api"}


app.include_router(raid.router)
app.include_router(disk.router)
app.include_router(backup.router)
app.include_router(replication.router)
app.include_router(risk.router)
app.include_router(scenarios_router)

Base.metadata.create_all(bind=engine)
