# rr
minimalist "registered report" system

## three related services

### archive
the archive stores arbitrary digital items, retrievable by checksum/hash.

### registry
the registry stores metadata records (including references
to archived items), retrievable by id.

### index
the index stores registry record ids, retrievable by metadata query.

## rr workflow
happy path:
```mermaid
sequenceDiagram
    participant researcher
    participant archive
    participant registry
    participant index
    participant publisher
    researcher->>archive: PUT statement of intent
    researcher->>registry: POST signed record of intent
    registry->>publisher: prompt to review
    publisher->>registry: GET record of intent 
    publisher->>archive: GET statement of intent
    Note over publisher: (some review/feedback process)
    publisher->>archive: PUT statement of endorsement
    publisher->>registry: POST signed record of endorsement
    registry->>index: PUT record of endorsement
    registry->>researcher: notify of endorsement
    Note over researcher: (research)
    researcher->>archive: PUT artifacts produced in research
    researcher->>registry: POST record of outcome
    registry->>index: PUT record of outcome
```

## from what exists
- archive: content-addressed osfstorage
- registry: metadata records in share
- index: elasticsearch in share
