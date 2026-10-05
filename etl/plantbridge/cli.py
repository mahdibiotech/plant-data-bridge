from __future__ import annotations

import argparse
import logging
import os
import time

from pydantic import ValidationError

from .brapi_client import BrAPIClient
from .indexer import bulk_index, ensure_index, get_client
from .transform import enrich_study, normalize_study


logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)s | %(message)s",
)

logger = logging.getLogger(__name__)


def demo_documents() -> list[dict]:
    return [
        {
            "id": "demo-001",
            "entity_type": "study",
            "source": "demo",
            "source_id": "demo-001",
            "source_endpoint": None,
            "harvested_at": None,
            "study_name": "Wheat drought tolerance trial",
            "study_description": "Demo study about drought tolerance in wheat.",
            "study_type": "Phenotyping",
            "common_crop_name": "wheat",
            "scientific_name": "Triticum aestivum",
            "location_id": None,
            "location_name": "Versailles",
            "country": "France",
            "latitude": None,
            "longitude": None,
            "trial_id": None,
            "trial_name": None,
            "program_id": None,
            "program_name": None,
            "start_date": None,
            "end_date": None,
            "seasons": [],
            "traits": [
                "drought tolerance",
                "grain yield",
            ],
            "external_references": [],
        },
        {
            "id": "demo-002",
            "entity_type": "study",
            "source": "demo",
            "source_id": "demo-002",
            "source_endpoint": None,
            "harvested_at": None,
            "study_name": "Barley plant height experiment",
            "study_description": "Demo barley phenotyping experiment.",
            "study_type": "Phenotyping",
            "common_crop_name": "barley",
            "scientific_name": "Hordeum vulgare",
            "location_id": None,
            "location_name": "Berlin",
            "country": "Germany",
            "latitude": None,
            "longitude": None,
            "trial_id": None,
            "trial_name": None,
            "program_id": None,
            "program_name": None,
            "start_date": None,
            "end_date": None,
            "seasons": [],
            "traits": [
                "plant height",
            ],
            "external_references": [],
        },
    ]


def demo_index() -> None:
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


def discover_capabilities(
    brapi: BrAPIClient,
) -> dict[str, bool]:
    try:
        capabilities = brapi.get_capabilities()

        print("Capabilities")
        print(f"  studies      : {capabilities['studies']}")
        print(f"  locations    : {capabilities['locations']}")
        print(f"  traits       : {capabilities['traits']}")
        print(f"  variables    : {capabilities['variables']}")
        print(f"  observations : {capabilities['observations']}")
        print()

        return capabilities

    except RuntimeError as exc:
        logger.warning(
            "Capability discovery failed: %s",
            exc,
        )

        fallback = {
            "studies": True,
            "locations": True,
            "traits": False,
            "variables": False,
            "observations": False,
        }

        print("Capabilities")
        print("  serverinfo unavailable")
        print("  using conservative fallback")
        print()

        return fallback


def harvest(
    source: str,
    base_url: str,
    page_size: int,
    max_pages: int | None,
    enrich_traits: bool,
) -> None:

    start = time.perf_counter()

    print()
    print("PlantDataBridge harvest")
    print("-" * 50)
    print(f"Source          : {source}")
    print(f"BrAPI endpoint  : {base_url}")
    print()

    brapi = BrAPIClient(
        base_url=base_url,
    )
    trait_client = BrAPIClient(
        base_url=base_url,
        timeout=5,
        max_retries=0,
    )

    capabilities = discover_capabilities(
        brapi
    )

    if not capabilities.get(
        "studies",
        True,
    ):
        raise RuntimeError(
            "The BrAPI source does not advertise "
            "study support."
        )

    fetched = 0
    valid = 0
    rejected = 0

    enriched_locations = 0
    failed_locations = 0

    enriched_traits = 0
    trait_failures = 0

    documents: list[dict] = []

    for raw in brapi.get_studies(
        page_size=page_size,
        max_pages=max_pages,
    ):

        fetched += 1

        try:
            study = normalize_study(
                raw,
                source=source,
                source_endpoint=base_url,
            )

            # ----------------------------------------------------------
            # Geographic enrichment
            # ----------------------------------------------------------

            location = None

            if (
                study.location_id
                and capabilities.get(
                    "locations",
                    False,
                )
            ):
                try:
                    location = brapi.get_location(
                        study.location_id
                    )

                    if location:
                        enriched_locations += 1

                except RuntimeError as exc:
                    failed_locations += 1

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

            # ----------------------------------------------------------
            # Trait enrichment
            # ----------------------------------------------------------

            traits: list[str] = []

            if (
                enrich_traits
                and capabilities.get("observations", False)
                and capabilities.get("variables", False)
            ):
                traits_result = trait_client.get_traits_for_study(
                    study_id=study.source_id,
                    page_size=5,
                    max_pages=1,
                    max_variables=10,
                )

                if traits_result is None:
                    trait_failures += 1

                else:
                    traits = traits_result

                    if traits:
                        enriched_traits += 1


            study.traits = traits

            documents.append(
                study.model_dump(
                    mode="json"
                )
            )

            valid += 1

        except (
            ValidationError,
            ValueError,
            TypeError,
        ) as exc:

            rejected += 1

            logger.warning(
                "Rejected study #%s: %s",
                fetched,
                exc,
            )

    if not documents:
        raise RuntimeError(
            "No valid BrAPI studies were harvested."
        )

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

    duration = time.perf_counter() - start

    print()
    print("-" * 50)
    print(f"Records fetched     : {fetched}")
    print(f"Valid               : {valid}")
    print(f"Rejected            : {rejected}")
    print(f"Locations enriched  : {enriched_locations}")
    print(f"Location failures   : {failed_locations}")
    print(f"Studies with traits : {enriched_traits}")
    print(f"Trait failures      : {trait_failures}")
    print(f"Indexed             : {indexed}")
    print(f"Duration            : {duration:.2f} s")
    print("-" * 50)

    if (
        rejected == 0
        and failed_locations == 0
        and trait_failures == 0
    ):
        print("STATUS              : SUCCESS")

    elif valid > 0:
        print("STATUS              : PARTIAL_SUCCESS")

    else:
        print("STATUS              : FAILED")

    print()


def build_parser() -> argparse.ArgumentParser:

    parser = argparse.ArgumentParser(
        prog="plantbridge",
        description=(
            "Federated BrAPI harvesting, enrichment "
            "and Elasticsearch indexing prototype."
        ),
    )

    subparsers = parser.add_subparsers(
        dest="command",
    )

    subparsers.add_parser(
        "demo-index",
        help="Index local demonstration documents.",
    )

    harvest_parser = subparsers.add_parser(
        "harvest",
        help="Harvest studies from a BrAPI source.",
    )

    harvest_parser.add_argument(
        "--source",
        required=True,
        help=(
            "Human-readable source name, "
            "for example Cassavabase."
        ),
    )

    harvest_parser.add_argument(
        "--base-url",
        required=True,
        help=(
            "BrAPI v2 base URL."
        ),
    )

    harvest_parser.add_argument(
        "--page-size",
        type=int,
        default=100,
        help=(
            "Number of study records requested "
            "per BrAPI page."
        ),
    )
    
    harvest_parser.add_argument(
        "--enrich-traits",
        action="store_true",
        help=(
            "Enable optional phenotype/trait enrichment. "
            "Disabled by default because remote observation "
            "endpoints may be slow."
        ),
    )

    harvest_parser.add_argument(
        "--max-pages",
        type=int,
        default=None,
        help=(
            "Maximum number of study pages to harvest. "
            "Default: all available pages."
        ),
    )

    return parser


def main() -> None:

    parser = build_parser()
    args = parser.parse_args()

    if args.command == "demo-index":
        demo_index()

    elif args.command == "harvest":
        harvest(
            source=args.source,
            base_url=args.base_url,
            page_size=args.page_size,
            max_pages=args.max_pages,
            enrich_traits=args.enrich_traits,
        )

    else:
        parser.print_help()


if __name__ == "__main__":
    main()
