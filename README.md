# PlantDataBridge 🌱

**Federated BrAPI harvesting, normalization, enrichment and search for plant research data**

PlantDataBridge is a lightweight prototype for federating heterogeneous plant research datasets exposed through **BrAPI** endpoints.

The project was designed around interoperability challenges similar to those addressed by plant research infrastructures such as **FAIDARE / URGI**: harvesting distributed data sources, normalizing metadata into a common model, enriching records through related BrAPI resources, indexing them in **Elasticsearch**, and exposing them through a **Spring Boot REST API**.

## Why this project?

Plant research data are often distributed across independent infrastructures, each exposing partially heterogeneous metadata and capabilities.

PlantDataBridge explores a simple architecture for:

- harvesting multiple BrAPI sources;
- normalizing studies into a common internal model;
- preserving data provenance;
- enriching study metadata using linked BrAPI resources;
- indexing heterogeneous records into a shared Elasticsearch index;
- exposing a searchable REST service with Spring Boot;
- handling partial failures from external scientific APIs.

The goal is not to reproduce FAIDARE, but to build a compact technical demonstrator around the same family of interoperability problems.

---

# Architecture

```text
                       External BrAPI sources

              ┌──────────────────────────────┐
              │                              │
              │  BrAPI Test Server           │
              │  Cassavabase                 │
              │  Future BrAPI sources        │
              │                              │
              └──────────────┬───────────────┘
                             │
                             │ BrAPI v2
                             ▼
                  ┌──────────────────────┐
                  │     Python ETL       │
                  │                      │
                  │  Extract             │
                  │  Validate            │
                  │  Normalize           │
                  │  Enrich              │
                  │  Preserve provenance │
                  └──────────┬───────────┘
                             │
                             ▼
                  ┌──────────────────────┐
                  │ Common Study Model   │
                  │                      │
                  │ source               │
                  │ source_id            │
                  │ study metadata       │
                  │ location metadata    │
                  │ coordinates          │
                  │ provenance           │
                  └──────────┬───────────┘
                             │
                             ▼
                  ┌──────────────────────┐
                  │   Elasticsearch      │
                  │                      │
                  │ Federated index      │
                  │ Full-text search     │
                  │ Multi-source data    │
                  └──────────┬───────────┘
                             │
                             ▼
                  ┌──────────────────────┐
                  │    Spring Boot       │
                  │                      │
                  │ /api/health          │
                  │ /api/search          │
                  └──────────────────────┘
```

---

# Technology stack

## Data integration

- Python 3
- BrAPI v2
- Requests
- Pydantic
- Elasticsearch Python client

## Backend

- Java 21
- Spring Boot
- Elasticsearch Java Client
- Maven

## Infrastructure

- Docker
- Docker Compose
- Elasticsearch 8
- Git

---

# Current capabilities

PlantDataBridge currently supports:

- BrAPI `/studies` harvesting;
- pagination;
- configurable source name and endpoint;
- study validation and normalization;
- federated identifiers;
- source provenance;
- geographic enrichment through `/locations/{locationDbId}`;
- country enrichment;
- GeoJSON coordinate extraction;
- Elasticsearch bulk indexing;
- multi-source indexing;
- Spring Boot full-text search;
- source resilience through retry handling;
- Python unit tests;
- Java/Maven tests;
- persistent Elasticsearch storage through Docker volumes.

---

# Common federated data model

Each study is normalized into a shared representation.

Example:

```json
{
  "id": "Cassavabase:3637",
  "entity_type": "study",

  "source": "Cassavabase",
  "source_id": "3637",
  "source_endpoint": "https://cassavabase.org/brapi/v2",

  "study_name": "00ayt11interspecIB",
  "study_description": "Assessment of Cassava varieties...",
  "study_type": "Advanced Yield Trial",

  "common_crop_name": "Cassava",

  "location_id": "3",
  "location_name": "Ibadan",
  "country": "Nigeria",

  "trial_id": "1810",
  "trial_name": "00_Ibadan",

  "program_id": "162",
  "program_name": "IITA",

  "start_date": "2000-04-11T00:00:00Z",
  "end_date": "2001-06-13T00:00:00Z",

  "seasons": [
    "2000"
  ]
}
```

Federated identifiers follow the pattern:

```text
<SOURCE>:<SOURCE_ID>
```

For example:

```text
Cassavabase:3637
BrAPITestServer:study1
```

This prevents identifier collisions across independent data providers.

---

# Geographic enrichment

Study records frequently contain a `locationDbId` but not complete geographic metadata.

PlantDataBridge therefore enriches records using:

```text
Study
  │
  │ locationDbId
  ▼
GET /locations/{locationDbId}
  │
  ├── country
  ├── location name
  ├── longitude
  └── latitude
```

Example successfully enriched record:

```text
Study      : BrAPITestServer:study1
Location   : Location 1
Country    : Peru
Latitude   : -76.46313
Longitude  : 42.44423
```

Coordinates follow the GeoJSON convention:

```text
[longitude, latitude]
```

---

# Results

## BrAPI Test Server

A complete test harvest produced:

```text
Records fetched : 3
Valid           : 3
Rejected        : 0
Indexed         : 3
Status          : SUCCESS
```

Geographic enrichment successfully recovered:

```text
BrAPITestServer:study1

country   = Peru
latitude  = -76.46313
longitude = 42.44423
```

---

## Cassavabase

Cassavabase exposes thousands of real plant breeding studies through BrAPI.

A controlled harvest test produced:

```text
Records fetched     : 2
Valid               : 2
Rejected            : 0
Locations enriched  : 2
Location failures   : 0
Indexed             : 2
Duration            : 3.92 s
Status              : SUCCESS
```

Example source:

```text
https://cassavabase.org/brapi/v2
```

---

## Federated indexing

Both sources were successfully indexed into the same Elasticsearch index:

```text
plant-studies-real
```

Observed source distribution:

```text
BrAPITestServer
BrAPITestServer
BrAPITestServer
Cassavabase
Cassavabase
```

Total indexed records during the validation run:

```text
5
```

This demonstrates that data from independent BrAPI infrastructures can be normalized and searched through a shared index.

---

# Search API

PlantDataBridge exposes a Spring Boot REST API.

## Health check

```bash
curl http://localhost:8080/api/health
```

Example:

```json
{
  "service": "plant-data-bridge-api",
  "status": "ok"
}
```

## Full-text search

```bash
curl "http://localhost:8080/api/search?q=study"
```

Search currently covers fields including:

- study name;
- study description;
- scientific name;
- crop name;
- traits;
- location name;
- trial name;
- program name.

Relevant fields receive Elasticsearch boosts to improve ranking.

---

# Quick Start

## Requirements

You only need:

- Docker
- Docker Compose
- Python 3.11+ for local ETL development

## 1. Clone

```bash
git clone https://github.com/mahdibiotech/plant-data-bridge.git
cd plant-data-bridge
```

## 2. Start Elasticsearch and Spring Boot

```bash
docker compose up -d elasticsearch backend
```

Check services:

```bash
docker compose ps
```

## 3. Prepare the ETL environment

```bash
cd etl

python -m venv .venv
source .venv/bin/activate

python -m pip install --upgrade pip
python -m pip install -e .
```

## 4. Run tests

```bash
python -m pytest -q
```

## 5. Harvest BrAPI Test Server

```bash
ELASTICSEARCH_URL=http://localhost:9200 \
ELASTICSEARCH_INDEX=plant-studies-real \
python -m plantbridge.cli harvest \
  --source BrAPITestServer \
  --base-url https://test-server.brapi.org/brapi/v2 \
  --page-size 5 \
  --max-pages 1
```

## 6. Harvest Cassavabase

```bash
ELASTICSEARCH_URL=http://localhost:9200 \
ELASTICSEARCH_INDEX=plant-studies-real \
python -m plantbridge.cli harvest \
  --source Cassavabase \
  --base-url https://cassavabase.org/brapi/v2 \
  --page-size 2 \
  --max-pages 1
```

## 7. Search through Spring Boot

```bash
curl "http://localhost:8080/api/search?q=Cassava"
```

or:

```bash
curl "http://localhost:8080/api/search?q=Peru"
```

---

# CLI

Available commands:

```bash
python -m plantbridge.cli --help
```

Current commands:

```text
demo-index
harvest
```

Example:

```bash
python -m plantbridge.cli harvest \
  --source Cassavabase \
  --base-url https://cassavabase.org/brapi/v2 \
  --page-size 10 \
  --max-pages 2
```

The ETL reports:

```text
Records fetched
Valid
Rejected
Locations enriched
Location failures
Indexed
Duration
Status
```

---

# Reliability considerations

External scientific APIs are not always continuously available.

PlantDataBridge therefore includes:

- request timeouts;
- HTTP retries;
- exponential backoff;
- validation before indexing;
- per-record rejection handling;
- non-blocking location enrichment failures;
- explicit execution statistics.

A future version will extend this toward source-level `PARTIAL_SUCCESS` reporting.

---

# Testing

## Python

```bash
cd etl
python -m pytest -q
```

## Java

Maven can be run directly through Docker:

```bash
docker run --rm \
  -v "$PWD/backend:/app" \
  -w /app \
  maven:3.9-eclipse-temurin-21 \
  mvn test
```

Validated result:

```text
Tests run: 1
Failures: 0
Errors: 0

BUILD SUCCESS
```

---

# Project structure

```text
plant-data-bridge/
│
├── docker-compose.yml
├── README.md
├── Makefile
│
├── etl/
│   ├── pyproject.toml
│   ├── requirements.txt
│   ├── Dockerfile
│   │
│   ├── plantbridge/
│   │   ├── brapi_client.py
│   │   ├── cli.py
│   │   ├── indexer.py
│   │   ├── models.py
│   │   └── transform.py
│   │
│   └── tests/
│
└── backend/
    ├── pom.xml
    ├── Dockerfile
    └── src/
        ├── main/
        └── test/
```

---

# Roadmap

Short-term extensions include:

- BrAPI capability discovery using `/serverinfo`;
- source configuration through YAML;
- filtering by source, crop and country;
- Elasticsearch facets;
- observation-variable integration where supported;
- additional BrAPI sources;
- Angular search interface;
- ETL execution reports;
- knowledge graph export;
- exploration of graph-based retrieval and generative AI.

---

# Scientific and engineering focus

PlantDataBridge sits at the intersection of:

```text
Bioinformatics
+
Data integration
+
Web services
+
Search systems
+
Scientific interoperability
```

The project is intended as a technical demonstrator for plant-data federation and scientific information systems.

---

## Author

**Mahdi Attabi**

Bioinformatics / Data Engineering

GitHub: `mahdibiotech`
