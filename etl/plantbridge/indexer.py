from __future__ import annotations

import os
from elasticsearch import Elasticsearch, helpers


def get_client() -> Elasticsearch:
    return Elasticsearch(os.getenv("ELASTICSEARCH_URL", "http://localhost:9200"))


def ensure_index(client: Elasticsearch, index_name: str):
    if client.indices.exists(index=index_name):
        return

    client.indices.create(
        index=index_name,
        mappings={
            "properties": {
                "id": {
                    "type": "keyword"
                },
                "entity_type": {
                    "type": "keyword"
                },

                "source": {
                    "type": "keyword"
                },
                "source_id": {
                    "type": "keyword"
                },
                "source_endpoint": {
                    "type": "keyword",
                    "index": False
                },
                "harvested_at": {
                    "type": "date"
                },

                "study_name": {
                    "type": "text",
                    "fields": {
                        "keyword": {
                            "type": "keyword"
                        }
                    }
                },

                "study_description": {
                    "type": "text"
                },

                "study_type": {
                    "type": "keyword"
                },

                "common_crop_name": {
                    "type": "keyword"
                },

                "scientific_name": {
                    "type": "text",
                    "fields": {
                        "keyword": {
                            "type": "keyword"
                        }
                    }
                },

                "location_id": {
                    "type": "keyword"
                },

                "location_name": {
                    "type": "text",
                    "fields": {
                        "keyword": {
                            "type": "keyword"
                        }
                    }
                },

                "country": {
                    "type": "keyword"
                },
                "latitude": {
                    "type": "float"
                },

                "longitude": {
                    "type": "float"
                },
                "trial_id": {
                    "type": "keyword"
                },

                "trial_name": {
                    "type": "text"
                },

                "program_id": {
                    "type": "keyword"
                },

                "program_name": {
                    "type": "keyword"
                },

                "start_date": {
                    "type": "date",
                    "ignore_malformed": True
                },

                "end_date": {
                    "type": "date",
                    "ignore_malformed": True
                },

                "seasons": {
                    "type": "keyword"
                },

                "traits": {
                    "type": "text"
                },

                "external_references": {
                    "type": "object",
                    "enabled": False
                }
            }
        },
    )


def bulk_index(client: Elasticsearch, index_name: str, documents: list[dict]):
    actions = [
        {
            "_index": index_name,
            "_id": doc["id"],
            "_source": doc,
        }
        for doc in documents
    ]
    return helpers.bulk(client, actions)
