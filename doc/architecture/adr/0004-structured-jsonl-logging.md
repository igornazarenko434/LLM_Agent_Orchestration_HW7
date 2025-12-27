# ADR-0004: Structured JSONL logging

Status: Accepted
Date: 2025-12-27

## Context
We need traceable logs across multiple agents and message flows.

## Decision
Use JSON Lines (one JSON object per line) via `league_sdk.logger`.

## Alternatives
- Plain text logs: harder to parse and correlate.
- External logging stack: out of scope for local development.

## Consequences
- Machine-friendly logs for analysis scripts.
- Consistent fields: message_type, sender, conversation_id.
