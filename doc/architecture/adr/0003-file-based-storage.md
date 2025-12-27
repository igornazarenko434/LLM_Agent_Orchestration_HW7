# ADR-0003: File-based JSON storage with repositories

Status: Accepted
Date: 2025-12-27

## Context
The system needs to persist standings, rounds, matches, and player history
without external dependencies.

## Decision
Use JSON files managed by repository classes with atomic writes.

## Alternatives
- SQLite/PostgreSQL: stronger transactional guarantees but adds setup overhead.

## Consequences
- Easy to inspect and backup.
- Requires careful handling of concurrent writes (addressed via sequential
  processing and atomic writes).
