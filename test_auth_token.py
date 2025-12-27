#!/usr/bin/env python3
"""Test auth_token serialization in GameInvitation."""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent / "SHARED"))

from league_sdk.protocol import GameInvitation  # noqa: E402

# Test 1: Create GameInvitation with auth_token
print("=" * 60)
print("TEST 1: GameInvitation with explicit auth_token")
print("=" * 60)

invitation = GameInvitation(
    sender="referee:REF01",
    timestamp="2025-12-26T14:00:00Z",
    conversation_id="test-conv",
    auth_token="abcdef1234567890" * 2,  # 32 chars
    league_id="test_league",
    round_id=1,
    match_id="R1M1",
    game_type="even_odd",
    role_in_match="PLAYER_A",
    opponent_id="P02",
)

dumped = invitation.model_dump()

print(f"auth_token in object: {invitation.auth_token!r}")
print(f"auth_token in dumped: {dumped.get('auth_token')!r}")
print(f"auth_token length in dumped: {len(dumped.get('auth_token', ''))}")
print(f"All keys in dumped: {sorted(dumped.keys())}")

# Test 2: Create GameInvitation WITHOUT explicit auth_token
print("\n" + "=" * 60)
print("TEST 2: GameInvitation WITHOUT explicit auth_token")
print("=" * 60)

invitation2 = GameInvitation(
    sender="referee:REF01",
    timestamp="2025-12-26T14:00:00Z",
    conversation_id="test-conv",
    league_id="test_league",
    round_id=1,
    match_id="R1M1",
    game_type="even_odd",
    role_in_match="PLAYER_A",
    opponent_id="P02",
    # NO auth_token parameter
)

dumped2 = invitation2.model_dump()

print(f"auth_token in object: {invitation2.auth_token!r}")
print(f"auth_token in dumped: {dumped2.get('auth_token')!r}")
print(f"auth_token length in dumped: {len(dumped2.get('auth_token', ''))}")
print(f"'auth_token' key exists: {'auth_token' in dumped2}")

# Test 3: Check if empty string fails validation
print("\n" + "=" * 60)
print("TEST 3: Validation check")
print("=" * 60)

for test_val in [None, "", "token123"]:
    result = "PASS" if test_val else "FAIL"
    print(f"  not {test_val!r:20} = {not test_val!r:5} -> {result}")
