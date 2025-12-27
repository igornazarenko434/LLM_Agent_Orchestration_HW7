# ADR-0005: Retry policy and circuit breaker

Status: Accepted
Date: 2025-12-27

## Context
Transient failures are common in distributed systems (timeouts, connection
errors). We need resilience without manual intervention.

## Decision
Implement exponential backoff retry with a circuit breaker in
`league_sdk.retry`.

## Alternatives
- No retries: brittle behavior.
- Fixed-delay retry: less effective under burst failures.

## Consequences
- Improved resilience and fewer manual restarts.
- Slightly increased latency under failure conditions.
