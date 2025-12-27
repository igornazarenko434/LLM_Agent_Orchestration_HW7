# ADR-0008: Separate Referee Agents for Match Execution

Status: Accepted
Date: 2025-12-27

## Context
Match execution can be handled by the League Manager or delegated to dedicated
referee agents. We need scalable parallel match execution and clear separation
of responsibilities.

## Decision
Use separate Referee agents to conduct matches and report results to the League
Manager.

## Alternatives
- League Manager runs matches directly (simpler but less scalable).
- Player self-refereeing (trust issues, inconsistent results).

## Consequences
- Parallel match execution across multiple referees.
- Clear orchestration vs execution separation.
