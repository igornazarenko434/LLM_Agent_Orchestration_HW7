# ADR-0007: Scheduled cleanup and retention policy

Status: Accepted
Date: 2025-12-27

## Context
Long-running leagues produce large data/log footprints. We need predictable
retention and archival behavior.

## Decision
Implement async cleanup in the League Manager using the retention settings in
`system.json`, including archive-before-delete.

## Alternatives
- Manual cleanup only: error-prone and inconsistent.
- External cron: adds deployment complexity.

## Consequences
- Automated lifecycle management with minimal operator overhead.
