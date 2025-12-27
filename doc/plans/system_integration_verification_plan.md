# System Integration Verification Plan (M7.14 + Full Flow)

**Scope:** End-to-end system startup, registration, scheduling, match execution, standings, league completion, and cleanup.
**Sources:** `PRD_EvenOddLeague.md`, `PROJECT_GUIDE.md`, `HW7_Instructions_full.pdf`, and current code in `agents/` + `SHARED/league_sdk/`.
**Principle:** Verify only what is implemented. If a step fails, log evidence and stop to fix before proceeding.

---

## 0) Preconditions (Static Verification)

**Verify configs and capabilities are consistent with runtime behavior**
- Files to inspect:
  - `SHARED/config/system.json`
  - `SHARED/config/agents/agents_config.json`
  - `SHARED/config/leagues/league_2025_even_odd.json`
  - `SHARED/config/games/games_registry.json`
- Confirm:
  - `system.timeouts` values match protocol expectations (5s join, 30s parity, 10s registration, etc.).
  - `security.require_auth` is true (current default).
  - `agents_config.json` endpoints/ports match each agent instance.
  - `agents_config.json` `metadata.auto_register` is set explicitly per agent (players/referees).

**Verify method-compatibility layer is available**
- Confirm `league_sdk/method_aliases.py` is used in LM, Player, and Referee servers.
- This allows PDF-style methods (e.g., `register_referee`, `handle_game_invitation`) to map to message types (e.g., `REFEREE_REGISTER_REQUEST`, `GAME_INVITATION`).

**Capability cross-check (config vs code)**
- League Manager capabilities in `agents_config.json`:
  - `register_referee`, `register_player`, `report_match_result`, `get_standings`, `start_league`, `league_query`.
- League Manager methods implemented in code:
  - `REFEREE_REGISTER_REQUEST`, `LEAGUE_REGISTER_REQUEST`, `MATCH_RESULT_REPORT`, `get_standings`, `start_league`, `LEAGUE_QUERY` (compat layer covers tool names).
- Referee capabilities in `agents_config.json`:
  - `conduct_match`, `enforce_timeouts`, `determine_winner`, `report_results`, `get_match_state`.
- Referee methods implemented in code:
  - `START_MATCH`, `GAME_JOIN_ACK`, `CHOOSE_PARITY_RESPONSE`, `get_match_state`, plus registration tools.
- Player capabilities in `agents_config.json`:
  - `handle_game_invitation`, `choose_parity`, `notify_match_result`, `get_player_state`.
- Player methods implemented in code:
  - `GAME_INVITATION`, `CHOOSE_PARITY_CALL`, `GAME_OVER`, `MATCH_RESULT_REPORT`, `get_player_state`, plus registration tools.

---

## 1) Launch League Manager (LM01)

**Action:** Start `agents/league_manager/main.py`.

**Expected LM state/data changes**
- `league_state`: `INIT` → still `INIT` (until start_league).
- `registered_referees`: empty dict (in-memory).
- `registered_players`: empty dict (in-memory).
- `standings_processor`: started and ready.
- Cleanup scheduler:
  - `run_full_cleanup()` runs on startup.
  - Scheduler task starts (daily 2 AM UTC per config).

**Verify (LM-specific)**
- `/health` responds 200: `http://localhost:8000/health`
- Logs (LM):
  - Startup log entry.
  - Cleanup started/completed logs (if retention enabled).
  - `MESSAGE_SENT`/`MESSAGE_RECEIVED` entries only begin once requests arrive.
- File outputs:
  - No standings/rounds yet unless previous run exists.

**Repository writes**
- None expected yet (unless cleanup modifies archive/log files).

---

## 2) Launch Referees (REF01, REF02)

**Action:** Start `agents/referee_REF01/main.py` and `agents/referee_REF02/main.py`.

**Expected Referee state/data changes**
- `state`: `INIT` → `REGISTERED` (after registration).
- `auth_token`: populated from `REFEREE_REGISTER_RESPONSE`.
- `referee_id`: set (e.g., `REF01`).
- `match_conductor`: initialized once registered.

**Expected message flow**
- REF → LM: `REFEREE_REGISTER_REQUEST`
- LM → REF: `REFEREE_REGISTER_RESPONSE` (includes `auth_token`)

**Verify (Referee + LM)**
- Ref logs show:
  - `MESSAGE_SENT` for registration request.
  - `State transition` to `REGISTERED`.
  - Retry logs if LM is unavailable (registration attempts and failures are logged).
- LM logs show:
  - `MESSAGE_RECEIVED` for `REFEREE_REGISTER_REQUEST`.
  - `MESSAGE_SENT` for response.
- LM in-memory registry contains each referee (id, endpoint, auth_token).

**Manual tools (referee)**
- `get_registration_status`: verify `state`, `auth_token`, attempt stats.
- `manual_register`: force registration if needed.

**Repository writes**
- None expected yet.

---

## 3) Launch Players (P01–P04)

**Action:** Start `agents/player_P01/main.py` through `player_P04/main.py`.

**Expected Player state/data changes**
- `state`: `INIT` → `REGISTERED` (after registration).
- `auth_token`: populated from `LEAGUE_REGISTER_RESPONSE`.
- Player history repository initialized (empty at this stage).

**Expected message flow**
- Player → LM: `LEAGUE_REGISTER_REQUEST`
- LM → Player: `LEAGUE_REGISTER_RESPONSE` (includes `auth_token`)

**Verify (Player + LM)**
- Player logs show:
  - `MESSAGE_SENT` for registration request.
  - `State transition` to `REGISTERED`.
  - Retry logs if LM is unavailable (registration attempts and failures are logged).
- LM logs show:
  - `MESSAGE_RECEIVED` for `LEAGUE_REGISTER_REQUEST`.
  - `MESSAGE_SENT` for response.
- LM in-memory registry contains all 4 players.

**Manual tools (player)**
- `get_registration_status`: verify `state`, `auth_token`, attempt stats.
- `manual_register`: force registration if needed.
- `get_player_state`: should show empty match history at this stage.

**Repository writes**
- Player history repo (`SHARED/data/players/<player_id>/history.json`) may be created but empty.

---

## 4) Start League Orchestration

**Action:** Trigger `start_league` on LM (debug tool).

**Expected LM state/data changes**
- `league_state`: `INIT` → `ACTIVE`.
- Round-robin schedule created (6 matches / 3 rounds for 4 players).
- `rounds.json` created/updated with matches and status `PENDING`.
- `current_round_id` set to 1.

**Round-robin scheduling details (per code + PDF)**
- **Player count check:** `min_players` from league config (default 2). League starts only if `registered_players >= min_players` and `registered_referees >= 1`.\n+- **Match count:** for `n` players, schedule is `n*(n-1)/2` matches; for `n=4`, total is 6 matches over 3 rounds.\n+- **Referee assignment:** each match is assigned a referee in rotation from the registered set. This is logged as `MATCH_ASSIGNED` with `match_id`, `round_id`, `player_a_id`, `player_b_id`, `referee_id`.\n+- **How players learn their rounds:** players receive `ROUND_ANNOUNCEMENT` with each match listing `player_A_id`, `player_B_id`, and `referee_endpoint`.\n+- **How referees learn which match to run:** LM sends `START_MATCH` directly to the assigned referee endpoint with `match_id`, `round_id`, `player_a_id`, `player_b_id`, and `conversation_id`. This is the trigger to start the match conductor.\n+
**Expected message flow**
- LM → Players: `ROUND_ANNOUNCEMENT` (Round 1).
- LM → Referees: `START_MATCH` for each match in round.

**Verify (LM)**
- LM logs:
  - Schedule creation summary.
  - `MESSAGE_SENT` for `ROUND_ANNOUNCEMENT`.
  - `MESSAGE_SENT` for `START_MATCH` per match.
  - `MATCH_ASSIGNED` entries per match (round-robin assignment evidence).
  - Retry logs for any failed broadcast (per-recipient failures logged via `PLAYER_NOT_AVAILABLE`).
- Round data:
  - `SHARED/data/leagues/league_2025_even_odd/rounds.json` contains rounds 1–3.

**Verify (Players)**
- Player logs:
  - `MESSAGE_RECEIVED` for `ROUND_ANNOUNCEMENT`.
  - Verify sender is `league_manager:LM01`.
- Note: Player validation requires auth_token for all messages. LM broadcasts currently do **not** set auth_token. If auth is required, players will emit `AUTH_TOKEN_INVALID`. This is an important verification checkpoint.

**Verify (Referees)**
- Ref logs:
  - `MESSAGE_RECEIVED` for `START_MATCH`.
  - `MATCH_STARTED` ack returned.
- Expected `START_MATCH` params: `match_id`, `round_id`, `player_a_id`, `player_b_id`, `conversation_id`.

**Repository writes**
- `RoundsRepository.add_round()` writes `SHARED/data/leagues/league_2025_even_odd/rounds.json` with `PENDING` match statuses.

---

## 5) Match Execution (Per Match, by Referee)

**Match execution is fully asynchronous in the referee.**

**Referee state/data changes**
- `message_queues[conversation_id]` created for the match.
- `match_repo` creates match entry at start; updates saved at end.
- Match lifecycle state (logged):
  - `WAITING_FOR_PLAYERS` → `COLLECTING_CHOICES` → `DRAWING_NUMBER` → `FINISHED` (or `FAILED`).

**Expected message flow**
1. REF → Players: `GAME_INVITATION`
2. Players → REF: `GAME_JOIN_ACK` (within 5s)
3. REF → Players: `CHOOSE_PARITY_CALL`
4. Players → REF: `CHOOSE_PARITY_RESPONSE` (within 30s)
5. REF → Players: `GAME_OVER`
6. REF → LM: `MATCH_RESULT_REPORT`

**Verify (Referee)**
- Logs show `MESSAGE_SENT` for each outgoing message and `MESSAGE_RECEIVED` for responses.
- If timeouts occur: `GAME_ERROR` sent to player with `E001` and retries according to config.
- `match_repo` file created/updated: `SHARED/data/matches/<match_id>.json`.
- `get_match_state` tool returns stored match record.
 - Retry logging: `call_with_retry` failures are logged in referee logs and should correlate with retry count and timeout in `system.json`.

**Verify (Players)**
- `GAME_INVITATION` received and `GAME_JOIN_ACK` returned.
- `CHOOSE_PARITY_CALL` received and `CHOOSE_PARITY_RESPONSE` returned.
- `GAME_OVER` received; history updated.
- `get_player_state` shows new history and stats.
 - Retry logging: timeouts or missing auth_token should emit `AUTH_TOKEN_INVALID` or timeout errors.

**Verify (LM)**
- LM receives `MATCH_RESULT_REPORT` and enqueues for sequential processing.
- If auth is required, token must match registered referee token.
 - Retry logging: `call_with_retry` around LM → referee START_MATCH should log failures (if any).

**Repository writes**
- `MatchRepository.create_match()` and `MatchRepository.save()` write `SHARED/data/matches/<match_id>.json`.
- Player history repo: `SHARED/data/players/<player_id>/history.json` updated with match entry.

---

## 6) Standings Update (Per Match)

**LM data changes**
- `StandingsRepository.update_player()` updates standings in `standings.json`.
- `_broadcast_standings_update()` sends `LEAGUE_STANDINGS_UPDATE` to all players.

**Verify**
- LM logs include `STANDINGS_UPDATE` event.
- `SHARED/data/leagues/league_2025_even_odd/standings.json` updated with:
  - `played`, `wins`, `draws`, `losses`, `points` per player.
- Player logs show `LEAGUE_STANDINGS_UPDATE` received.
- Note: LM broadcast currently omits `auth_token`. If auth required, players will log `AUTH_TOKEN_INVALID` and reject. This is a key checkpoint.

**Repository writes**
- `StandingsRepository.save()` overwrites standings file with updated rankings.

---

## 7) Round Completion

**LM data changes**
- Round status updated to `COMPLETED` in `rounds.json` when all matches complete.
- `ROUND_COMPLETED` sent to all players with summary.

**Verify**
- LM logs: `Round <id> completed`.
- Player logs: `ROUND_COMPLETED` received.
- Next round automatically started by `manage_round(next_round_id)`.
 - Retry logging: broadcast failures logged with `PLAYER_NOT_AVAILABLE`.

**Repository writes**
- `RoundsRepository.update_round_status()` updates round status to `COMPLETED`.
- `RoundsRepository.add_round()` overwrites round list with updated match statuses.

---

## 8) League Completion

**LM data changes**
- After all rounds complete:
  - `league_state`: `ACTIVE` → `COMPLETED`.
  - `LEAGUE_COMPLETED` broadcast to all players.
  - Cleanup triggered via `_on_league_completed_cleanup()`.

**Verify**
- LM logs show `LEAGUE_COMPLETED` broadcast and cleanup run.
- Player logs show `LEAGUE_COMPLETED` received.
- `standings.json` final ranking matches sum of match results.
 - Cleanup logs show archive actions and failures (if any).

**Repository writes**
- No new standings writes beyond final update unless cleanup modifies archival files.

---

## 9) Manual Verification Tools (Runtime)

**League Manager**
- `league_query` (GET_STANDINGS): requires sender + auth_token unless config allows unauth.
- `get_standings`: debug tool; auth required unless `security.allow_start_league_without_auth` allows missing sender/auth.
- `start_league`: debug tool to trigger orchestration.

**Referee**
- `get_match_state`: returns stored match record by match_id.
- `get_registration_status`: returns state + auth_token.
- `manual_register`: triggers registration (optional force).

**Player**
- `get_player_state`: returns match history + stats.
- `get_registration_status`: returns state + auth_token.
- `manual_register`: triggers registration (optional force).

**Health**
- `/health` endpoint for all agents (BaseAgent).

---

## 10) Auth Token Verification Checklist

**Where auth_token must appear**
- Referee → LM: `MATCH_RESULT_REPORT` includes referee token.
- Referee → Players: `GAME_INVITATION`, `CHOOSE_PARITY_CALL`, `GAME_OVER` include referee token.
- Players → Referee: `GAME_JOIN_ACK`, `CHOOSE_PARITY_RESPONSE` include player token.

**Known strictness in current code**
- Player validates `auth_token` on every incoming message when `require_auth=true`.
- LM validates referee token on `MATCH_RESULT_REPORT`.
- Referee validates `auth_token` for responses it receives based on `require_auth`.

**Verification action**
- Inspect logs for `AUTH_TOKEN_INVALID` or `Missing auth token` events.
- If those appear in LM broadcast phases (ROUND/LEAGUE updates), it indicates broadcasts lack tokens and are rejected by players.

---

## 11) Log Coverage Checklist (Structured Logging)

Use `SHARED/logs/` JSONL files from `logger.py`.
- `MESSAGE_RECEIVED` and `MESSAGE_SENT` appear for each protocol exchange.
- `STATE_TRANSITION` appears for registration transitions (player/referee).
- `STANDINGS_UPDATE`, `MATCH_ASSIGNED`, `ROUND_COMPLETED` events are logged by LM.
- `GAME_ERROR` (E001) appears on timeouts in referee logs.
- **Repository evidence** is written under `SHARED/data/` for rounds, standings, matches, and player history; verify those files align with logs.
 - Retry activity: `call_with_retry` emits warning/error logs on failed attempts; verify retry cadence matches `system.retry_policy` and timeouts.

---

## 12) Integration Test (M7.14 DoD)

**Command**
```
PYTHONPATH=SHARED:$PYTHONPATH pytest tests/e2e/test_4_player_league.py -v --timeout=600
```

**Expected outcome**
- All 6 matches complete.
- Standings consistent with results.
- League completes with champion.
- No protocol errors or missing auth_token failures.

---

## 13) Common Failure Points to Watch

- **Start Match missing:** If LM doesn’t send `START_MATCH`, no match starts. Verify LM `manage_round` call and referee endpoint config.
- **Auth token missing in LM broadcasts:** Players reject `ROUND_ANNOUNCEMENT`, `LEAGUE_STANDINGS_UPDATE`, `ROUND_COMPLETED`, `LEAGUE_COMPLETED` if `require_auth=true`.
- **Referee registration missing:** `START_MATCH` fails with `AGENT_NOT_REGISTERED`.
- **Queue processor not started:** `MATCH_RESULT_REPORT` will not update standings.
- **Round status not updated:** League will never complete.

---

## 14) Minimal Runtime Trace (Happy Path)

1. LM starts → cleanup runs.
2. REF01/REF02 register → tokens stored.
3. P01–P04 register → tokens stored.
4. `start_league` triggers schedule creation.
5. LM broadcasts `ROUND_ANNOUNCEMENT` and sends `START_MATCH`.
6. REF conducts match (invitation → ack → parity → game_over → report).
7. LM updates standings and broadcasts.
8. Round completes; LM advances to next round.
9. After all rounds, LM broadcasts `LEAGUE_COMPLETED` and runs cleanup.
