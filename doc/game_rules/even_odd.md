# Even/Odd Game Rules

**Version:** 1.0.0
**Date:** 2025-01-15
**Game Type:** even_odd

---

## 1. Overview

The Even/Odd game is a simple two-player game of chance and prediction. In this league implementation, it serves as the core mechanism for agent competition. Players must choose a parity ("even" or "odd") for a randomly drawn number.

## 2. Game Logic

The game flow consists of three main steps:
1.  **Choice:** Two players (Player A and Player B) independently choose a parity: `"even"` or `"odd"`.
2.  **Draw:** The Referee draws a random integer $N$ where $1 \le N \le 10$ (inclusive).
3.  **Determination:** The winner is determined based on whether the parity of $N$ matches the players' choices.

### 2.1 Parity Definition
-   **Even:** A number is even if it is divisible by 2 with no remainder.
    -   Set: $\{2, 4, 6, 8, 10\}$
-   **Odd:** A number is odd if it is not divisible by 2.
    -   Set: $\{1, 3, 5, 7, 9\}$

---

## 3. Winner Determination

The outcome of a match depends on the combination of the players' choices and the parity of the drawn number.

**Condition:** A player wins if their chosen parity matches the parity of the drawn number $N$.

### 3.1 Outcome Scenarios

There are four possible choice combinations, intersecting with two possible number parities.

| Scenario | Player A Choice | Player B Choice | Drawn Number Parity | Outcome | Reason |
| :--- | :--- | :--- | :--- | :--- | :--- |
| **1** | `"even"` | `"odd"` | **Even** | **Player A Wins** | A matched, B did not. |
| **2** | `"even"` | `"odd"` | **Odd** | **Player B Wins** | B matched, A did not. |
| **3** | `"odd"` | `"even"` | **Even** | **Player B Wins** | B matched, A did not. |
| **4** | `"odd"` | `"even"` | **Odd** | **Player A Wins** | A matched, B did not. |
| **5** | `"even"` | `"even"` | **Any** | **DRAW** | Both players matched (or both missed). |
| **6** | `"odd"` | `"odd"` | **Any** | **DRAW** | Both players matched (or both missed). |

**Note on Draws:**
Unlike some variants where a draw occurs only if both miss, in this implementation, if **both players choose the same parity**, the game is immediately declared a **DRAW**, regardless of the number drawn. This prevents a scenario where both players "win" simultaneously.

---

## 4. Scoring System

Points are awarded based on the match outcome:

| Result | Points | Description |
| :--- | :---: | :--- |
| **WIN** | **3** | Player correctly guessed the parity (and opponent did not). |
| **DRAW** | **1** | Both players chose the same parity. |
| **LOSS** | **0** | Player failed to guess the parity (and opponent did). |

---

## 5. Technical Loss

A **Technical Loss** is a special administrative outcome awarded by the Referee if a player fails to adhere to the protocol constraints.

**Triggers:**
*   **Timeout:** Failure to send `GAME_JOIN_ACK` within 5 seconds.
*   **Timeout:** Failure to send `CHOOSE_PARITY_RESPONSE` within 30 seconds.
*   **Invalid Move:** Sending a choice other than `"even"` or `"odd"`.

**Scoring:**
*   **Offending Player:** 0 points (recorded as LOSS)
*   **Opponent:** 3 points (recorded as WIN)

---

## 6. Protocol-Aligned Match Flow (league.v2 over JSON-RPC)

1) **Invitation**: Referee sends `GAME_INVITATION` (JSON-RPC method `GAME_INVITATION`) to both players with `match_id`, `league_id`, `conversation_id`, and timestamp.
2) **Join Ack**: Each player must respond with `GAME_JOIN_ACK` within **5s**. Missing/late → `E001` timeout and technical loss for the offender.
3) **Parity Choice**: Referee issues `CHOOSE_PARITY_CALL` to each player; players respond with `CHOOSE_PARITY_RESPONSE` including `"even"` or `"odd"` within **30s**. Invalid choice → `E010 INVALID_MOVE`; timeout → `E001` and technical loss.
4) **Draw Number**: Referee draws integer `N` in `[1,10]` using cryptographic randomness (see §7).
5) **Determine Outcome**: Apply rules in §3 and scoring in §4.
6) **Notify Players**: Referee sends `GAME_OVER` to both players with drawn number, choices, winner/draw flag, and applied error codes if any.
7) **Report Upstream**: Referee sends `MATCH_RESULT_REPORT` to League Manager; LM updates standings and broadcasts `LEAGUE_STANDINGS_UPDATE` and round/league announcements when applicable.

All messages must include the league.v2 envelope fields (`protocol`, `message_type`, `sender`, `timestamp`, `conversation_id`, `auth_token` post-registration). See `SHARED/league_sdk/protocol.py` for exact schemas.

---

## 7. Randomness Requirements

- **Range**: Uniform random integer 1–10 inclusive.
- **Method**: Use a cryptographically secure generator (`secrets.randbelow` + 1) to avoid bias and comply with PRD fairness expectations.
- **Logging**: Referee logs the drawn number and derived parity in match logs (JSONL) with `match_id` and `conversation_id`.
- **Reproducibility for Tests**: Allow an optional test hook/seed in non-production mode only; production flow must remain crypto-random.

---

## 8. Validation & Error Codes

- **Valid choices**: `"even"` or `"odd"` only (case-sensitive). Anything else → `E010 INVALID_MOVE`.
- **Envelope**: Missing/invalid envelope fields → `E002 INVALID_MESSAGE_FORMAT`.
- **Authentication**: Missing/invalid `auth_token` after registration → `E012 AUTH_TOKEN_INVALID`; unregistered sender → `E004 AGENT_NOT_REGISTERED`.
- **Timeouts**: `E001 TIMEOUT_ERROR` for late `GAME_JOIN_ACK` or `CHOOSE_PARITY_RESPONSE`.
- **Protocol version**: Mismatch → `E011 PROTOCOL_VERSION_MISMATCH`.
- **Duplicate conversation**: If a duplicate `conversation_id` is detected for the same `match_id`, treat as no-op and log once.

---

## 9. Data Persistence & Observability

- **Match transcripts**: Persisted under `data/matches/<league_id>/<match_id>.json` with lifecycle state, choices, drawn number, winner, and any error codes.
- **Player history**: Players append to `data/players/<player_id>/history.json` upon `GAME_OVER`, updating stats (wins, losses, draws, technical losses).
- **Logging**: All agents write append-only JSONL logs (`logs/agents/<agent_id>.log.jsonl`) with `conversation_id` and `match_id` for correlation; never log auth tokens.
- **Metrics**: Track response times for invitation ack and parity choice to ensure SLA (<5s, <30s) and support KPIs.

---

## 10. Compliance Checklist (M5.2 Gate)

- Uses crypto-random draw in [1,10]; parity sets match `games_registry.json`.
- Enforces timeouts: 5s join, 30s choice; late → technical loss and `E001`.
- Validates choices strictly; invalid → `E010`; missing auth → `E012`.
- Draw when both players choose the same parity, regardless of drawn number (per PRD FR-012).
- All messages carry league.v2 envelope; protocol version mismatches return `E011`.
- Logging and data persistence follow 3-layer architecture (config/data/logs).
- Referee reports results upstream and notifies both players; LM updates standings using Win=3, Draw=1, Loss=0.
