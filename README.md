# PlantDataBridge

Prototype de fédération de données végétales inspiré des problématiques FAIDARE/URGI.

## Objectif V0.1

- Extraire des données depuis une API BrAPI
- Normaliser les enregistrements
- Indexer les documents dans Elasticsearch
- Exposer une API REST Spring Boot
- Lancer l'ensemble avec Docker Compose

## Architecture

BrAPI -> Python ETL -> Elasticsearch -> Spring Boot API

## Démarrage rapide

```bash
cp .env.example .env
docker compose up --build
```

API Spring Boot:
- http://localhost:8080/api/health
- http://localhost:8080/api/search?q=wheat

Elasticsearch:
- http://localhost:9200
