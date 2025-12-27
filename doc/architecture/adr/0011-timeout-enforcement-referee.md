# ADR-0011: Timeout Enforcement at Referee Level

Status: Accepted
Date: 2025-12-27

## Context
Match timeouts (join ACK, parity choice, game over) must be enforced reliably.
Options include League Manager enforcement or Referee enforcement.

## Decision
Enforce timeouts in the Referee match conductor using configured thresholds
from `SHARED/config/system.json`.

## Alternatives
- League Manager timeout enforcement: centralizes logic but adds orchestration
  latency and state coupling.

## Consequences
- Referee has full control over match lifecycle and timeouts.
- Cleaner separation of orchestration vs match execution.
