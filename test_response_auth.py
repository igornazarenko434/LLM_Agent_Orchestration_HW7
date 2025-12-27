#!/usr/bin/env python3
"""Test auth_token in RefereeRegisterResponse."""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent / "SHARED"))

from league_sdk.protocol import RefereeRegisterResponse  # noqa: E402

# Test: Create RefereeRegisterResponse with auth_token
print("=" * 60)
print("TEST: RefereeRegisterResponse with auth_token")
print("=" * 60)

response = RefereeRegisterResponse(
    sender="league_manager:LM01",
    timestamp="2025-12-26T14:00:00Z",
    conversation_id="test-conv",
    status="ACCEPTED",
    referee_id="REF01",
    auth_token="test_token_32_characters_long!",  # Explicit auth_token
    league_id="test_league",
)

dumped = response.model_dump()

print(f"auth_token in object: {response.auth_token!r}")
print(f"auth_token in dumped: {dumped.get('auth_token')!r}")
print(f"auth_token length: {len(dumped.get('auth_token', ''))}")
print("'auth_token' in dumped: {'auth_token' in dumped}")
print("\nAll fields in dumped:")
for key, value in sorted(dumped.items()):
    if key == "auth_token":
        print(f"  {key}: {value!r} <--- THIS IS THE KEY FIELD")
    else:
        print(f"  {key}: {value!r}")
