# ADR-0002: Use async httpx for inter-agent calls

Status: Accepted
Date: 2025-12-27

## Context
Agents must call other MCP endpoints concurrently and without blocking the event
loop, especially for broadcasts and match flow.

## Decision
Use `httpx.AsyncClient` in `league_sdk.retry.call_with_retry`.

## Alternatives
- requests (sync): blocks and limits concurrency.
- aiohttp: extra dependency, similar outcome.

## Consequences
- Non-blocking I/O with asyncio.
- Simplifies concurrent broadcasts and retry logic.
