# Round-Robin Scheduling Algorithm

**Version:** 1.0.0
**Date:** 2025-01-15
**Algorithm:** Circle Method
**Project Context:** League Manager Scheduling

---

## 1. Overview

The Round-Robin scheduling algorithm ensures that every participant in a tournament plays every other participant exactly once (in a single round-robin setup). This project utilizes the **Circle Method**, a standard algorithm for fair and efficient schedule generation.

## 2. Core Requirements

Based on the project's PRD and Mission specifications:
*   **Participants:** $N$ players (where $N \ge 2$).
*   **Matches:** Total matches $M = N \times (N-1) / 2$.
*   **Rounds:** Matches must be distributed across rounds to allow parallel execution.
*   **Fairness:** Each player should play once per round (if $N$ is even) or have a bye (if $N$ is odd).

## 3. Algorithm: The Circle Method

### 3.1 Concept
Imagine the players are points on a circle.
1.  **Fix one player** (the "anchor") at the top of the circle.
2.  **Rotate** the remaining $N-1$ players clockwise for each round.
3.  **Pair** the anchor with the player opposite them, and then pair the remaining players top-to-bottom in parallel lines.

### 3.2 Logic for Even $N$ Players
Let players be indices $0$ to $N-1$.
1.  **Round 1:**
    *   Pair index $0$ vs index $N-1$.
    *   Pair index $1$ vs index $N-2$.
    *   Pair index $2$ vs index $N-3$, and so on.
2.  **Next Rounds:**
    *   Keep index $0$ fixed.
    *   Rotate indices $1$ to $N-1$ by one position.
    *   Repeat pairing logic.
3.  **Total Rounds:** $N-1$.

### 3.3 Logic for Odd $N$ Players
1.  Add a "dummy" or "bye" player to make count $N+1$ (even).
2.  Run the Even $N$ logic.
3.  Whoever is paired with the "dummy" player gets a **bye** (no match) for that round.
4.  **Total Rounds:** $N$.

### 3.4 Implementation Pseudocode (Python-style)

```python
def generate_schedule(players):
    """
    Generates a round-robin schedule for a list of players.
    
    Args:
        players: List of player IDs.
        
    Returns:
        List of rounds, where each round is a list of (p1, p2) tuples.
    """
    n = len(players)
    
    # Handle odd number of players
    if n % 2 == 1:
        players.append(None) # None represents a bye
        n += 1
        
    rounds = []
    # Indices for rotation: keep 0 fixed, rotate 1 to n-1
    rotation_indices = list(range(n))
    
    # Total rounds for single round-robin is n-1
    for r in range(n - 1):
        current_round = []
        
        # Pair players
        for i in range(n // 2):
            p1_idx = rotation_indices[i]
            p2_idx = rotation_indices[n - 1 - i]
            
            p1 = players[p1_idx]
            p2 = players[p2_idx]
            
            # If neither is a bye, schedule the match
            if p1 is not None and p2 is not None:
                current_round.append((p1, p2))
                
        rounds.append(current_round)
        
        # Rotate indices: keep [0], take last element and insert at [1]
        # [0, 1, 2, 3] -> [0, 3, 1, 2] -> [0, 2, 3, 1]
        rotation_indices = [rotation_indices[0]] + [rotation_indices[-1]] + rotation_indices[1:-1]
        
    return rounds
```

## 4. Integration with League Manager

The League Manager Agent will use this algorithm to populate the `data/leagues/<id>/rounds.json` file.

### 4.1 Referee Assignment
*   Matches in a round are distributed among available Referees.
*   Simple modulo assignment: `referee = referees[match_index % num_referees]`
*   Load balancing ensures no single referee is overwhelmed if `max_concurrent_matches` constraint allows.

### 4.2 Match ID Generation
*   Format: `R{round_id}M{match_num}` (e.g., `R1M1`, `R1M2`).
*   This ensures unique identification across the league.

## 5. Constraints & Edge Cases

*   **Minimum Players:** $N=2$. The algorithm generates 1 round with 1 match.
*   **Large Leagues:** For $N=100$, rounds = 99, matches/round = 50. Total = 4950 matches. This is within the capability of our file-based storage.
*   **Concurrency:** All matches in a single round list are eligible to start simultaneously, bounded only by the number of Referees.

---

## 6. Project Alignment & Best Practices (league_2025_even_odd)

- **Single round-robin** per PRD (no home/away). Total matches = `n*(n-1)/2`.
- **Player source of truth**: Use registered/active players from `SHARED/config/leagues/league_2025_even_odd.json` combined with runtime registry (no matches for inactive players).
- **Fairness ordering**: Shuffle initial player order with a deterministic seed (e.g., `seed = hash(league_id)`) to avoid bias while keeping reproducibility for tests.
- **Odd player handling**: Insert bye; a bye does not produce a match and does not affect standings (no points).
- **Uniqueness**: Each pair appears exactly once; no player appears in two matches in the same round.
- **Protocol compliance**: Each generated match must carry `league_id`, `round_id`, unique `match_id`, and later `conversation_id` when the match is executed by a referee.

## 7. Referee Assignment (Load-Balanced)

Use simple modulo to distribute matches evenly while respecting configured referees (from `agents_config.json`) and their `max_concurrent_matches` where applicable.

```python
def assign_referees(rounds, referees):
    assigned = []
    for round_matches in rounds:
        annotated = []
        for idx, match in enumerate(round_matches):
            ref = referees[idx % len(referees)]
            annotated.append({"players": match, "referee_id": ref})
        assigned.append(annotated)
    return assigned
```

If `max_concurrent_matches` is smaller than matches in a round, stagger start times or split into micro-batches while keeping round identity intact.

## 8. Serialization & IDs

- **Match IDs**: `R{round_index+1}M{within_round+1}` (e.g., `R3M2`), consistent with PRD and tests.
- **Round storage**: Persist to `data/leagues/<league_id>/rounds.json` with schema:
  ```json
  {
    "league_id": "league_2025_even_odd",
    "rounds": [
      {
        "round_id": 1,
        "matches": [
          {"match_id": "R1M1", "players": ["P01","P02"], "referee_id": "REF01"},
          {"match_id": "R1M2", "players": ["P03","P04"], "referee_id": "REF02"}
        ]
      }
    ]
  }
  ```
- **Conversation IDs**: Generated at execution time (not during schedule build) to avoid collisions when rerunning schedules.

## 9. Error Handling & Validation

- Validate player list length ≥2; if fewer, abort scheduling with `E008 LEAGUE_NOT_FOUND`-style domain error at LM layer.
- Ensure no duplicate player IDs; dedupe or raise `INVALID_MESSAGE_FORMAT (E002)` at schedule build time.
- For odd counts, ensure byes do not leak into match generation or standings.
- Log scheduling decisions via JSONL logger with `round_id`, `match_id`, and `referee_id` for traceability.

## 10. Compliance Checklist (M5.3)

- Uses Circle Method; total matches = `n*(n-1)/2`; rounds = `n-1` (even) or `n` (odd with bye).
- Deterministic shuffle of initial ordering to prevent bias, with reproducible seed.
- One match per player per round; no duplicate pairings across rounds.
- Referee assignment is balanced and respects configured referee list.
- IDs follow `R{round}M{match}` format; persisted under `data/leagues/<league_id>/rounds.json`.
- Compatible with league.v2 flow: matches ready for `GAME_INVITATION`/`MATCH_RESULT_REPORT` lifecycle.

---

**References:**
*   [Wikipedia: Round-robin tournament](https://en.wikipedia.org/wiki/Round-robin_tournament#Scheduling_algorithm)
*   Standard "Circle Method" implementation.
