# PlantDataBridge Architecture

## Data flow

```mermaid
flowchart TD

    A[BrAPI Test Server]
    B[Cassavabase]
    C[Future BrAPI Sources]

    A --> D[Python BrAPI Client]
    B --> D
    C --> D

    D --> E[Validation]
    E --> F[Normalization]
    F --> G[Location Enrichment]

    G --> H[Common Study Model]

    H --> I[Elasticsearch Federated Index]

    I --> J[Spring Boot REST API]

    J --> K[Search Clients]
    J --> L[Future Angular Frontend]
