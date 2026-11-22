from datetime import datetime
from typing import Any

from pydantic import BaseModel, Field


class ScenarioCreate(BaseModel):
    name: str = Field(min_length=1, max_length=200)
    module_type: str = Field(min_length=1, max_length=50)
    inputs: dict[str, Any]
    results: dict[str, Any]
    assumptions: list[str] = Field(default_factory=list)
    tags: list[str] = Field(default_factory=list)


class ScenarioUpdate(BaseModel):
    name: str | None = Field(default=None, min_length=1, max_length=200)
    module_type: str | None = Field(default=None, min_length=1, max_length=50)
    inputs: dict[str, Any] | None = None
    results: dict[str, Any] | None = None
    assumptions: list[str] | None = None
    tags: list[str] | None = None


class ScenarioResponse(BaseModel):
    id: int
    name: str
    module_type: str
    inputs: dict[str, Any]
    results: dict[str, Any]
    assumptions: list[str]
    tags: list[str]
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class ScenarioComparison(BaseModel):
    scenario_ids: list[int] = Field(min_length=2, max_length=3)
