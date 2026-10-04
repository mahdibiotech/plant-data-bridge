from __future__ import annotations

import logging
from typing import Iterator

import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry


logger = logging.getLogger(__name__)


class BrAPIClient:
    def __init__(
        self,
        base_url: str,
        timeout: int = 30,
        max_retries: int = 3,
    ):
        self.base_url = base_url.rstrip("/")
        self.timeout = timeout
        self.session = requests.Session()

        retry_strategy = Retry(
            total=max_retries,
            connect=max_retries,
            read=max_retries,
            status=max_retries,
            backoff_factor=1.0,
            status_forcelist=[429, 500, 502, 503, 504],
            allowed_methods=["GET"],
        )

        adapter = HTTPAdapter(
            max_retries=retry_strategy
        )

        self.session.mount(
            "https://",
            adapter,
        )

        self.session.mount(
            "http://",
            adapter,
        )

    def get_serverinfo(self) -> dict:
        url = f"{self.base_url}/serverinfo"

        logger.info(
            "GET %s",
            url,
        )

        try:
            response = self.session.get(
                url,
                timeout=self.timeout,
            )
            response.raise_for_status()

        except requests.RequestException as exc:
            raise RuntimeError(
                f"BrAPI source unavailable: "
                f"{self.base_url}: {exc}"
            ) from exc

        try:
            return response.json()

        except ValueError as exc:
            raise RuntimeError(
                f"Invalid JSON returned by "
                f"{self.base_url}/serverinfo"
            ) from exc

    def get_location(
        self,
        location_id: str,
    ) -> dict:
        url = (
            f"{self.base_url}/locations/"
            f"{location_id}"
        )

        logger.info(
            "Fetching location id=%s",
            location_id,
        )

        try:
            response = self.session.get(
                url,
                timeout=self.timeout,
            )
            response.raise_for_status()

        except requests.RequestException as exc:
            raise RuntimeError(
                f"Failed to retrieve location "
                f"{location_id}: {exc}"
            ) from exc

        try:
            payload = response.json()

        except ValueError as exc:
            raise RuntimeError(
                f"Invalid location JSON "
                f"for {location_id}"
            ) from exc

        return payload.get(
            "result",
            {},
        )

    def get_observation_variables(
        self,
        page_size: int = 100,
        study_id: str | None = None,
    ) -> list[dict]:
        url = (
            f"{self.base_url}/"
            f"observationvariables"
        )

        params = {
            "page": 0,
            "pageSize": page_size,
        }

        if study_id is not None:
            params["studyDbId"] = study_id

        logger.info(
            "Fetching observation variables "
            "study=%s",
            study_id,
        )

        try:
            response = self.session.get(
                url,
                params=params,
                timeout=self.timeout,
            )
            response.raise_for_status()

        except requests.RequestException as exc:
            raise RuntimeError(
                f"Failed to retrieve "
                f"observation variables: {exc}"
            ) from exc

        try:
            payload = response.json()

        except ValueError as exc:
            raise RuntimeError(
                "Invalid observation variable JSON"
            ) from exc

        return (
            payload
            .get("result", {})
            .get("data", [])
        )

    def get_studies(
        self,
        page_size: int = 100,
        max_pages: int | None = None,
    ) -> Iterator[dict]:

        page = 0

        while True:

            if (
                max_pages is not None
                and page >= max_pages
            ):
                break

            url = (
                f"{self.base_url}/studies"
            )

            logger.info(
                "Fetching studies page=%s "
                "pageSize=%s",
                page,
                page_size,
            )

            try:
                response = self.session.get(
                    url,
                    params={
                        "page": page,
                        "pageSize": page_size,
                    },
                    timeout=self.timeout,
                )

                response.raise_for_status()

            except requests.RequestException as exc:
                raise RuntimeError(
                    f"BrAPI source unavailable: "
                    f"{self.base_url} "
                    f"(page={page}): {exc}"
                ) from exc

            try:
                payload = response.json()

            except ValueError as exc:
                raise RuntimeError(
                    f"Invalid JSON returned by "
                    f"{self.base_url} "
                    f"(page={page})"
                ) from exc

            data = (
                payload
                .get("result", {})
                .get("data", [])
            )

            if not data:
                break

            for row in data:
                yield row

            pagination = (
                payload
                .get("metadata", {})
                .get("pagination", {})
            )

            current_page = (
                pagination.get(
                    "currentPage",
                    page,
                )
            )

            total_pages = (
                pagination.get(
                    "totalPages"
                )
            )

            logger.info(
                "Page %s retrieved: "
                "%s records",
                current_page,
                len(data),
            )

            page += 1

            if (
                total_pages is not None
                and page >= total_pages
            ):
                break
    def get_serverinfo(self) -> dict:
        url = f"{self.base_url}/serverinfo"

        logger.info("Fetching BrAPI server capabilities")

        try:
            response = self.session.get(
                url,
                timeout=self.timeout,
            )
            response.raise_for_status()
            return response.json()

        except requests.RequestException as exc:
            raise RuntimeError(
                f"Failed to retrieve serverinfo: {exc}"
            ) from exc


    def get_capabilities(self) -> dict[str, bool]:
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

        return {
            "studies": "studies" in services,
            "locations": "locations/{locationDbId}" in services,
            "traits": "traits" in services,
            "variables": "variables" in services,
            "observations": "observations" in services,
        }