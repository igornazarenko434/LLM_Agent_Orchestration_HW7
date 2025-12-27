# ADR-0006: Method alias compatibility layer

Status: Accepted
Date: 2025-12-27

## Context
The assignment PDF uses tool-style names (e.g., `handle_game_invitation`) while
the implementation uses message types (e.g., `GAME_INVITATION`).

## Decision
Add a compatibility layer in `league_sdk/method_aliases.py` to translate PDF
tool names to internal message types.

## Alternatives
- Implement only message types: breaks PDF examples.
- Duplicate handlers for each name: higher maintenance cost.

## Consequences
- Backwards-compatible interface with minimal code duplication.
