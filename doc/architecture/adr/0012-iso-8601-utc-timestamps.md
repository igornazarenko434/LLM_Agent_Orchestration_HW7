# ADR-0012: ISO 8601 UTC Timestamps with 'Z' Suffix

Status: Accepted
Date: 2025-12-27

## Context
Logs and message envelopes require consistent timestamps for tracing and audit.
Mixed timezone formats cause parsing and comparison issues.

## Decision
Use ISO 8601 UTC timestamps with a `Z` suffix across all agents and data.

## Alternatives
- Local time with offsets: harder to compare across systems.
- Epoch timestamps: less human-readable.

## Consequences
- Consistent parsing in logs and stored JSON.
- Easier correlation across agents and tools.
