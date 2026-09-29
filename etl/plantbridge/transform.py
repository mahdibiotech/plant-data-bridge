from __future__ import annotations

from datetime import datetime, timezone

from .models import PlantStudy


def normalize_study(
    raw: dict,
    source: str,
    source_endpoint: str | None = None,
) -> PlantStudy:

    source_id = (
        raw.get("studyDbId")
        or raw.get("studyName")
        or raw.get("studyCode")
    )

    if not source_id:
        raise ValueError(
            "Study has no studyDbId, studyName or studyCode"
        )

    source_id = str(source_id)

    additional_info = raw.get("additionalInfo") or {}

    federated_id = f"{source}:{source_id}"

    return PlantStudy(
        id=federated_id,

        source=source,
        source_id=source_id,
        source_endpoint=source_endpoint,
        harvested_at=datetime.now(timezone.utc),

        study_name=(
            raw.get("studyName")
            or raw.get("studyCode")
            or "Unnamed study"
        ),

        study_description=raw.get(
            "studyDescription"
        ),

        study_type=raw.get(
            "studyType"
        ),

        common_crop_name=raw.get(
            "commonCropName"
        ),

        scientific_name=raw.get(
            "scientificName"
        ),

        location_id=raw.get(
            "locationDbId"
        ),

        location_name=raw.get(
            "locationName"
        ),

        country=None,

        trial_id=raw.get(
            "trialDbId"
        ),

        trial_name=raw.get(
            "trialName"
        ),

        program_id=additional_info.get(
            "programDbId"
        ),

        program_name=additional_info.get(
            "programName"
        ),

        start_date=raw.get(
            "startDate"
        ),

        end_date=raw.get(
            "endDate"
        ),

        seasons=raw.get(
            "seasons"
        ) or [],

        traits=[],

        external_references=raw.get(
            "externalReferences"
        ) or [],
    )
def enrich_study(
    study: PlantStudy,
    location: dict | None = None,
    observation_variables: list[dict] | None = None,
) -> PlantStudy:

    if location:

        study.country = (
            location.get("countryName")
            or location.get("countryCode")
            or study.country
        )

        coordinates = (
            location.get("coordinates")
            or {}
        )

        geometry = (
            coordinates.get("geometry")
            or {}
        )

        values = geometry.get("coordinates")

        if (
            isinstance(values, list)
            and len(values) >= 2
        ):
            # GeoJSON = longitude, latitude
            study.longitude = values[0]
            study.latitude = values[1]

        study.location_name = (
            location.get("locationName")
            or study.location_name
        )

    if observation_variables:

        traits = []

        for variable in observation_variables:

            trait = (
                variable.get("trait")
                or {}
            )

            trait_name = (
                trait.get("traitName")
                or variable.get("observationVariableName")
            )

            if (
                trait_name
                and trait_name not in traits
            ):
                traits.append(trait_name)

        study.traits = traits

    return study