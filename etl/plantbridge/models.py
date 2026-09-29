from __future__ import annotations

from datetime import datetime
from typing import Any

from pydantic import BaseModel, Field


class PlantStudy(BaseModel):
    id: str
    entity_type: str = "study"

    # Provenance
    source: str
    source_id: str
    source_endpoint: str | None = None
    harvested_at: datetime | None = None

    # Core BrAPI fields
    study_name: str
    study_description: str | None = None
    study_type: str | None = None

    common_crop_name: str | None = None
    scientific_name: str | None = None

    location_id: str | None = None
    location_name: str | None = None
    country: str | None = None
    latitude: float | None = None
    longitude: float | None = None
    trial_id: str | None = None
    trial_name: str | None = None

    program_id: str | None = None
    program_name: str | None = None

    start_date: str | None = None
    end_date: str | None = None

    seasons: list[str] = Field(default_factory=list)
    traits: list[str] = Field(default_factory=list)

    external_references: list[dict[str, Any]] = Field(
        default_factory=list
    )
