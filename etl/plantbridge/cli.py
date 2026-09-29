from __future__ import annotations

import argparse
import logging
import os
import time

from pydantic import ValidationError

from .brapi_client import BrAPIClient
from .indexer import get_client, ensure_index, bulk_index
from .transform import normalize_study, enrich_study


logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)s | %(message)s",
)

logger = logging.getLogger(__name__)


def demo_documents():
    return [
        {
            "id": "demo-001",
            "entity_type": "study",
            "source": "demo",
            "study_name": "Wheat drought tolerance trial",
            "common_crop_name": "wheat",
            "scientific_name": "Triticum aestivum",
            "country": "France",
            "traits": [
                "drought tolerance",
                "grain yield",
            ],
        },
        {
            "id": "demo-002",
            "entity_type": "study",
            "source": "demo",
            "study_name": "Barley plant height experiment",
            "common_crop_name": "barley",
            "scientific_name": "Hordeum vulgare",
            "country": "Germany",
            "traits": [
                "plant height",
            ],
        },
    ]


def demo_index():
    index_name = os.getenv(
        "ELASTICSEARCH_INDEX",
        "plant-studies",
    )

    client = get_client()

    ensure_index(
        client,
        index_name,
    )

    success, _ = bulk_index(
        client,
        index_name,
        demo_documents(),
    )

    client.indices.refresh(
        index=index_name
    )

    print(
        f"Indexed {success} demo documents "
        f"into '{index_name}'."
    )


def harvest(
    source: str,
    base_url: str,
    page_size: int,
    max_pages: int | None,
):
    start = time.perf_counter()

    print()
    print("PlantDataBridge harvest")
    print("-" * 50)
    print(f"Source          : {source}")
    print(f"BrAPI endpoint  : {base_url}")
    print()

    brapi = BrAPIClient(base_url)

    fetched = 0
    valid = 0
    rejected = 0

    documents = []

    for raw in brapi.get_studies(
        page_size=page_size,
        max_pages=max_pages,
    ):
        fetched += 1

        try:
            # --------------------------------------------------
            # 1. NORMALISATION + VALIDATION
            # --------------------------------------------------

            study = normalize_study(
                raw,
                source=source,
                source_endpoint=base_url,
            )

            # --------------------------------------------------
            # 2. LOCATION ENRICHMENT
            # --------------------------------------------------

            location = None

            if study.location_id:
                try:
                    location = brapi.get_location(
                        study.location_id
                    )
                except RuntimeError as exc:
                    logger.warning(
                        "Location enrichment failed "
                        "for %s: %s",
                        study.id,
                        exc,
                    )

            study = enrich_study(
                study,
                location=location,
                observation_variables=None,
            )
            # --------------------------------------------------
            # 3. OBSERVATION VARIABLES ENRICHMENT
            # --------------------------------------------------

            observation_variables = []

            try:
                observation_variables = (
                    brapi.get_observation_variables(
                        study.source_id
                    )
                )

            except RuntimeError as exc:
                logger.warning(
                    "Observation variable enrichment "
                    "failed for %s: %s",
                    study.id,
                    exc,
                )

            # --------------------------------------------------
            # 4. FINAL ENRICHMENT
            # --------------------------------------------------

            study = enrich_study(
                study,
                location=location,
                observation_variables=(
                    observation_variables
                ),
            )

            # --------------------------------------------------
            # 5. CONVERSION POUR ELASTICSEARCH
            # --------------------------------------------------

            documents.append(
                study.model_dump()
            )

            valid += 1

        except (
            ValidationError,
            ValueError,
            TypeError,
        ) as exc:

            rejected += 1

            logger.warning(
                "Rejected study: %s",
                exc,
            )

    # ----------------------------------------------------------
    # 6. PROTECTION CONTRE UNE RÉCOLTE VIDE
    # ----------------------------------------------------------

    if not documents:
        raise RuntimeError(
            "No valid BrAPI studies were harvested."
        )

    # ----------------------------------------------------------
    # 7. ELASTICSEARCH
    # ----------------------------------------------------------

    index_name = os.getenv(
        "ELASTICSEARCH_INDEX",
        "plant-studies",
    )

    elastic = get_client()

    ensure_index(
        elastic,
        index_name,
    )

    indexed, _ = bulk_index(
        elastic,
        index_name,
        documents,
    )

    elastic.indices.refresh(
        index=index_name
    )

    # ----------------------------------------------------------
    # 8. STATISTIQUES
    # ----------------------------------------------------------

    duration = time.perf_counter() - start

    print()
    print("-" * 50)
    print(f"Records fetched : {fetched}")
    print(f"Valid           : {valid}")
    print(f"Rejected        : {rejected}")
    print(f"Indexed         : {indexed}")
    print(f"Duration        : {duration:.2f} s")
    print("-" * 50)
    print("STATUS          : SUCCESS")
    print()


def main():
    parser = argparse.ArgumentParser(
        prog="plantbridge"
    )

    sub = parser.add_subparsers(
        dest="command"
    )

    # ----------------------------------------------------------
    # DEMO INDEX
    # ----------------------------------------------------------

    sub.add_parser(
        "demo-index"
    )

    # ----------------------------------------------------------
    # HARVEST
    # ----------------------------------------------------------

    harvest_parser = sub.add_parser(
        "harvest"
    )

    harvest_parser.add_argument(
        "--source",
        required=True,
    )

    harvest_parser.add_argument(
        "--base-url",
        required=True,
    )

    harvest_parser.add_argument(
        "--page-size",
        type=int,
        default=100,
    )

    harvest_parser.add_argument(
        "--max-pages",
        type=int,
        default=None,
    )

    # ----------------------------------------------------------
    # PARSE ARGUMENTS
    # ----------------------------------------------------------

    args = parser.parse_args()

    # ----------------------------------------------------------
    # COMMAND DISPATCH
    # ----------------------------------------------------------

    if args.command == "demo-index":

        demo_index()

    elif args.command == "harvest":

        harvest(
            source=args.source,
            base_url=args.base_url,
            page_size=args.page_size,
            max_pages=args.max_pages,
        )

    else:

        parser.print_help()


if __name__ == "__main__":
    main()

