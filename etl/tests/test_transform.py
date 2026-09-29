from plantbridge.transform import normalize_study


def test_normalize_study():

    raw = {
        "studyDbId": "S1",
        "studyName": "Demo wheat trial",
        "studyDescription": "Drought experiment",
        "studyType": "Yield Trial",

        "commonCropName": "wheat",

        "locationDbId": "LOC1",
        "locationName": "Versailles",

        "trialDbId": "T1",
        "trialName": "Trial 2026",

        "additionalInfo": {
            "programDbId": "P1",
            "programName": "Demo Program",
        },

        "startDate": "2026-01-01T00:00:00Z",
        "endDate": "2026-07-01T00:00:00Z",

        "seasons": [
            "2026"
        ],
    }

    study = normalize_study(
        raw,
        source="demo",
        source_endpoint="https://example.org/brapi/v2",
    )

    assert study.id == "demo:S1"
    assert study.source_id == "S1"

    assert study.study_name == "Demo wheat trial"
    assert study.study_description == "Drought experiment"

    assert study.location_name == "Versailles"

    assert study.trial_name == "Trial 2026"

    assert study.program_name == "Demo Program"

    assert study.common_crop_name == "wheat"

    assert study.seasons == ["2026"]
