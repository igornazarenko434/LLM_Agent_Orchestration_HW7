# ADR-0009: Shared SDK in SHARED/ Directory

Status: Accepted
Date: 2025-12-27

## Context
Multiple agents share protocol models, config loading, retry logic, logging, and
repositories. Duplicating this code per agent increases drift and bugs.

## Decision
Create a shared SDK under `SHARED/league_sdk` used by all agents.

## Alternatives
- Separate repositories per agent (high duplication).
- No SDK (copy/paste common utilities).

## Consequences
- Single source of truth for protocol and utilities.
- Easier maintenance and testing.
