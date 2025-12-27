# ADR-0010: Round-Robin Scheduling for League Matches

Status: Accepted
Date: 2025-12-27

## Context
We need a fair scheduling algorithm for leagues with small to medium player
counts. Options include single elimination, Swiss, and round-robin.

## Decision
Use round-robin scheduling (each player faces every other player once).

## Alternatives
- Single elimination: fewer matches, less fairness.
- Swiss system: more complex pairing rules.

## Consequences
- Predictable total matches: n*(n-1)/2.
- Fairness and complete coverage of opponents.
