from __future__ import annotations

import logging
from typing import Any, Iterator

import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry


logger = logging.getLogger(__name__)


class BrAPIClient:
    """
    Minimal resilient BrAPI v2 client used by PlantDataBridge.

    Responsibilities:
    - capability discovery via /serverinfo
    - study pagination
    - location enrichment
    - observation retrieval by study
    - observation variable retrieval
    - trait extraction from study-linked observations
    """

    def __init__(
        self,
        base_url: str,
        timeout: int = 30,
        max_retries: int = 3,
        backoff_factor: float = 1.0,
    ) -> None:

        self.base_url = base_url.rstrip("/")
        self.timeout = timeout

        retry = Retry(
            total=max_retries,
            connect=max_retries,
            read=max_retries,
            status=max_retries,
            backoff_factor=backoff_factor,
            status_forcelist=[
                429,
                500,
                502,
                503,
                504,
            ],
            allowed_methods=frozenset(["GET"]),
            raise_on_status=False,
        )

        adapter = HTTPAdapter(
            max_retries=retry
        )

        self.session = requests.Session()

        self.session.mount(
            "https://",
            adapter,
        )

        self.session.mount(
            "http://",
            adapter,
        )


    # ------------------------------------------------------------------
    # Generic HTTP helper
    # ------------------------------------------------------------------

    def _get_json(
        self,
        url: str,
        params: dict[str, Any] | None = None,
    ) -> dict:

        try:
            response = self.session.get(
                url,
                params=params,
                timeout=self.timeout,
            )

            response.raise_for_status()

            return response.json()

        except requests.RequestException as exc:
            raise RuntimeError(
                f"GET request failed for {url}: {exc}"
            ) from exc

        except ValueError as exc:
            raise RuntimeError(
                f"Invalid JSON response from {url}: {exc}"
            ) from exc


    # ------------------------------------------------------------------
    # Capability discovery
    # ------------------------------------------------------------------

    def get_serverinfo(self) -> dict:

        url = f"{self.base_url}/serverinfo"

        logger.info(
            "Fetching BrAPI server capabilities"
        )

        return self._get_json(url)


    def get_capabilities(
        self,
    ) -> dict[str, bool]:

        serverinfo = self.get_serverinfo()

        calls = (
            serverinfo
            .get("result", {})
            .get("calls", [])
        )

        services = {
            call.get("service")
            for call in calls
            if call.get("service")
        }

        def supports(prefix: str) -> bool:
            return any(
                service == prefix
                or service.startswith(
                    f"{prefix}/"
                )
                for service in services
            )

        return {
            "studies": supports("studies"),
            "locations": supports("locations"),
            "traits": supports("traits"),
            "variables": supports("variables"),
            "observations": supports(
                "observations"
            ),
        }


    # ------------------------------------------------------------------
    # Studies
    # ------------------------------------------------------------------

    def get_studies(
        self,
        page_size: int = 100,
        max_pages: int | None = None,
    ) -> Iterator[dict]:

        page = 0

        while True:

            logger.info(
                "Fetching studies page=%s pageSize=%s",
                page,
                page_size,
            )

            payload = self._get_json(
                f"{self.base_url}/studies",
                params={
                    "page": page,
                    "pageSize": page_size,
                },
            )

            data = (
                payload
                .get("result", {})
                .get("data", [])
            )

            logger.info(
                "Page %s retrieved: %s records",
                page,
                len(data),
            )

            for item in data:
                yield item

            pagination = (
                payload
                .get("metadata", {})
                .get("pagination", {})
            )

            total_pages = pagination.get(
                "totalPages"
            )

            page += 1

            if not data:
                break

            if (
                max_pages is not None
                and page >= max_pages
            ):
                break

            if (
                total_pages is not None
                and page >= total_pages
            ):
                break


    # ------------------------------------------------------------------
    # Locations
    # ------------------------------------------------------------------

    def get_location(
        self,
        location_id: str,
    ) -> dict:

        logger.info(
            "Fetching location id=%s",
            location_id,
        )

        payload = self._get_json(
            f"{self.base_url}/locations/{location_id}"
        )

        return (
            payload
            .get("result", {})
        )


    # ------------------------------------------------------------------
    # Observation Variables
    # ------------------------------------------------------------------

    def get_variable(
        self,
        variable_id: str,
    ) -> dict:

        logger.debug(
            "Fetching observation variable id=%s",
            variable_id,
        )

        payload = self._get_json(
            f"{self.base_url}/variables/{variable_id}"
        )

        return (
            payload
            .get("result", {})
        )


    # ------------------------------------------------------------------
    # Observations
    # ------------------------------------------------------------------

    def get_observations_for_study(
        self,
        study_id: str,
        page_size: int = 100,
        max_pages: int | None = None,
    ) -> Iterator[dict]:

        page = 0

        while True:

            logger.info(
                "Fetching observations "
                "study=%s page=%s pageSize=%s",
                study_id,
                page,
                page_size,
            )

            payload = self._get_json(
                f"{self.base_url}/observations",
                params={
                    "studyDbId": study_id,
                    "page": page,
                    "pageSize": page_size,
                },
            )

            data = (
                payload
                .get("result", {})
                .get("data", [])
            )

            logger.info(
                "Observation page %s: %s records",
                page,
                len(data),
            )

            for observation in data:
                yield observation

            pagination = (
                payload
                .get("metadata", {})
                .get("pagination", {})
            )

            total_pages = pagination.get(
                "totalPages"
            )

            page += 1

            if not data:
                break

            if (
                max_pages is not None
                and page >= max_pages
            ):
                break

            if (
                total_pages is not None
                and page >= total_pages
            ):
                break


    # ------------------------------------------------------------------
    # Trait extraction
    # ------------------------------------------------------------------

    def get_traits_for_study(
        self,
        study_id: str,
        page_size: int = 5,
        max_pages: int | None = 2,
        max_variables: int = 20,
    ) -> list[str] | None:
        """
        Resolve traits actually associated with a study.

        If observation retrieval fails or times out, return an empty list
        instead of interrupting the main harvest.
        """

        variable_ids: dict[str, str | None] = {}

        try:
            observations = self.get_observations_for_study(
                study_id=study_id,
                page_size=page_size,
                max_pages=max_pages,
            )

            for observation in observations:

                variable_id = observation.get(
                    "observationVariableDbId"
                )

                variable_name = observation.get(
                    "observationVariableName"
                )

                if not variable_id:
                    continue

                variable_id = str(variable_id)

                if variable_id not in variable_ids:
                    variable_ids[variable_id] = variable_name

                if len(variable_ids) >= max_variables:
                    logger.warning(
                        "Variable limit reached for study=%s: %s",
                        study_id,
                        max_variables,
                    )
                    break

        except RuntimeError as exc:
            logger.warning(
                "Observation retrieval failed for study=%s: %s",
                study_id,
                exc,
            )

            return None

        logger.info(
            "Study %s references %s unique observation variables",
            study_id,
            len(variable_ids),
        )

        traits: list[str] = []

        for variable_id, fallback_name in variable_ids.items():

            trait_name: str | None = None

            try:
                variable = self.get_variable(
                    variable_id
                )

                trait = variable.get("trait") or {}

                trait_name = trait.get(
                    "traitName"
                )

                if not trait_name:
                    trait_name = variable.get(
                        "observationVariableName"
                    )

            except RuntimeError as exc:
                logger.warning(
                    "Variable enrichment failed "
                    "study=%s variable=%s: %s",
                    study_id,
                    variable_id,
                    exc,
                )

                trait_name = fallback_name

            if trait_name and trait_name not in traits:
                traits.append(trait_name)

        logger.info(
            "Resolved %s unique traits for study=%s",
            len(traits),
            study_id,
        )

        return traits
