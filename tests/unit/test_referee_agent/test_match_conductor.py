import asyncio
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from league_sdk.repositories import MatchRepository

from agents.referee_REF01.match_conductor import MatchConductor


@pytest.fixture
def mock_logger():
    return MagicMock()


@pytest.fixture
def match_conductor(mock_logger):
    with patch("agents.referee_REF01.match_conductor.MatchRepository") as MockRepo, patch(
        "agents.referee_REF01.match_conductor.load_system_config"
    ) as mock_sys_conf, patch(
        "agents.referee_REF01.match_conductor.load_agents_config"
    ) as mock_agents_conf, patch(
        "agents.referee_REF01.match_conductor.load_json_file"
    ) as mock_league_conf:
        # Setup mocks
        mock_repo_instance = MockRepo.return_value

        # Configure system config with required timeouts/retries
        sys_conf = MagicMock()
        sys_conf.timeouts.game_join_ack_sec = 0.1
        sys_conf.timeouts.parity_choice_sec = 0.1
        sys_conf.timeouts.game_over_sec = 0.1
        sys_conf.timeouts.match_result_sec = 0.1
        sys_conf.retry_policy.max_retries = 1
        sys_conf.retry_policy.initial_delay_sec = 0.01
        sys_conf.retry_policy.max_delay_sec = 0.02
        sys_conf.network.request_timeout_sec = 0.1
        mock_sys_conf.return_value = sys_conf

        # Configure agents config
        mock_agents_conf.return_value = {
            "players": [
                {"agent_id": "P01", "endpoint": "http://p1"},
                {"agent_id": "P02", "endpoint": "http://p2"},
            ],
            "league_manager": {"endpoint": "http://lm"},
        }

        mock_league_conf.return_value = {"game_type": "even_odd"}

        conductor = MatchConductor("REF01", "token", "league_1", mock_logger)
        conductor.match_repo = mock_repo_instance  # Explicitly set mock repo instance
        return conductor


@pytest.mark.asyncio
async def test_conduct_match_initializes_repository(match_conductor):
    """Test that conduct_match calls create_match on the repository."""

    match_id = "M1"
    round_id = 1
    p1 = "P01"
    p2 = "P02"
    conv_id = "conv-1"
    queue = asyncio.Queue()

    # Mock _send_invitations to fail immediately to stop execution early
    # but after create_match should have been called
    with patch.object(match_conductor, "_send_invitations", return_value=None):
        result = await match_conductor.conduct_match(match_id, round_id, p1, p2, conv_id, queue)

    # Verify create_match was called
    match_conductor.match_repo.create_match.assert_called_once_with(
        match_id=match_id,
        league_id="league_1",
        round_id=round_id,
        game_type="even_odd",
        player_a_id=p1,
        player_b_id=p2,
        referee_id="REF01",
    )


@pytest.mark.asyncio
async def test_conduct_match_saves_result(match_conductor):
    """Test that conduct_match saves the final result."""

    # Fully mock the flow to reach the end
    match_id = "M1"
    round_id = 1
    p1 = "P01"
    p2 = "P02"
    conv_id = "conv-1"
    queue = asyncio.Queue()

    with patch.object(
        match_conductor, "_send_invitations", return_value={p1: True, p2: True}
    ), patch.object(
        match_conductor, "_wait_for_join_acks", return_value={p1: "ack", p2: "ack"}
    ), patch.object(
        match_conductor, "_send_parity_calls"
    ), patch.object(
        match_conductor, "_wait_for_parity_choices", return_value={p1: "even", p2: "odd"}
    ), patch.object(
        match_conductor, "_send_game_over"
    ), patch.object(
        match_conductor, "_send_match_result_to_league_manager"
    ):
        # Mock game logic to be deterministic
        match_conductor.game_logic.draw_random_number = MagicMock(return_value=2)  # Even
        match_conductor.game_logic.check_parity = MagicMock(return_value="even")
        match_conductor.game_logic.determine_winner = MagicMock(return_value=(p1, "WIN", "LOSS"))
        match_conductor.game_logic.get_points = MagicMock(return_value=3)

        await match_conductor.conduct_match(match_id, round_id, p1, p2, conv_id, queue)

        # Verify save was called
        match_conductor.match_repo.save.assert_called()
        args = match_conductor.match_repo.save.call_args
        assert args[0][0] == match_id
        assert args[0][1]["winner"] == p1


# ============================================================================
# ERROR PATH TESTS - Phase 1.2
# ============================================================================


class TestMatchConductorTimeoutScenarios:
    """Test timeout enforcement and error handling."""

    @pytest.mark.asyncio
    async def test_both_players_timeout_on_join(self, match_conductor):
        """Both players timeout on GAME_JOIN_ACK -> technical loss for both."""
        match_id, round_id = "M1", 1
        p1, p2 = "P01", "P02"
        conv_id = "conv-1"
        queue = asyncio.Queue()

        with patch.object(
            match_conductor, "_send_invitations", return_value={p1: True, p2: True}
        ), patch.object(match_conductor, "_wait_for_join_acks", return_value={p1: None, p2: None}):
            result = await match_conductor.conduct_match(match_id, round_id, p1, p2, conv_id, queue)

            # Should return technical loss result
            assert result["winner"] == "NONE"
            assert result["technical_loss"] is True
            assert "Both players timed out" in result["reason"]

    @pytest.mark.asyncio
    async def test_player_a_timeout_on_join(self, match_conductor):
        """Player A timeouts on GAME_JOIN_ACK -> Player B wins."""
        match_id, round_id = "M1", 1
        p1, p2 = "P01", "P02"
        conv_id = "conv-1"
        queue = asyncio.Queue()

        with patch.object(
            match_conductor, "_send_invitations", return_value={p1: True, p2: True}
        ), patch.object(
            match_conductor, "_wait_for_join_acks", return_value={p1: None, p2: "ack"}
        ), patch.object(
            match_conductor, "_finish_match_with_technical_loss", return_value={"winner": p2}
        ) as mock_finish:
            # Mock game logic for technical loss
            match_conductor.game_logic.award_technical_loss = MagicMock(
                return_value=(p2, "TECHNICAL_LOSS", "WIN")
            )

            result = await match_conductor.conduct_match(match_id, round_id, p1, p2, conv_id, queue)

            # Verify technical loss was awarded
            match_conductor.game_logic.award_technical_loss.assert_called_once_with(p1, p2)
            mock_finish.assert_called_once()

    @pytest.mark.asyncio
    async def test_player_b_timeout_on_join(self, match_conductor):
        """Player B timeouts on GAME_JOIN_ACK -> Player A wins."""
        match_id, round_id = "M1", 1
        p1, p2 = "P01", "P02"
        conv_id = "conv-1"
        queue = asyncio.Queue()

        with patch.object(
            match_conductor, "_send_invitations", return_value={p1: True, p2: True}
        ), patch.object(
            match_conductor, "_wait_for_join_acks", return_value={p1: "ack", p2: None}
        ), patch.object(
            match_conductor, "_finish_match_with_technical_loss", return_value={"winner": p1}
        ) as mock_finish:
            match_conductor.game_logic.award_technical_loss = MagicMock(
                return_value=(p1, "TECHNICAL_LOSS", "WIN")
            )

            result = await match_conductor.conduct_match(match_id, round_id, p1, p2, conv_id, queue)

            match_conductor.game_logic.award_technical_loss.assert_called_once_with(p2, p1)
            mock_finish.assert_called_once()

    @pytest.mark.asyncio
    async def test_both_players_timeout_on_parity_choice(self, match_conductor):
        """Both players timeout on CHOOSE_PARITY -> technical loss for both."""
        match_id, round_id = "M1", 1
        p1, p2 = "P01", "P02"
        conv_id = "conv-1"
        queue = asyncio.Queue()

        with patch.object(
            match_conductor, "_send_invitations", return_value={p1: True, p2: True}
        ), patch.object(
            match_conductor, "_wait_for_join_acks", return_value={p1: "ack", p2: "ack"}
        ), patch.object(
            match_conductor, "_send_parity_calls"
        ), patch.object(
            match_conductor, "_wait_for_parity_choices", return_value={p1: None, p2: None}
        ):
            result = await match_conductor.conduct_match(match_id, round_id, p1, p2, conv_id, queue)

            assert result["winner"] == "NONE"
            assert result["technical_loss"] is True
            assert "parity choice" in result["reason"]

    @pytest.mark.asyncio
    async def test_player_a_timeout_on_parity_choice(self, match_conductor):
        """Player A timeouts on CHOOSE_PARITY -> Player B wins."""
        match_id, round_id = "M1", 1
        p1, p2 = "P01", "P02"
        conv_id = "conv-1"
        queue = asyncio.Queue()

        with patch.object(
            match_conductor, "_send_invitations", return_value={p1: True, p2: True}
        ), patch.object(
            match_conductor, "_wait_for_join_acks", return_value={p1: "ack", p2: "ack"}
        ), patch.object(
            match_conductor, "_send_parity_calls"
        ), patch.object(
            match_conductor, "_wait_for_parity_choices", return_value={p1: None, p2: "even"}
        ), patch.object(
            match_conductor, "_finish_match_with_technical_loss", return_value={"winner": p2}
        ) as mock_finish:
            match_conductor.game_logic.award_technical_loss = MagicMock(
                return_value=(p2, "TECHNICAL_LOSS", "WIN")
            )

            result = await match_conductor.conduct_match(match_id, round_id, p1, p2, conv_id, queue)

            mock_finish.assert_called_once()

    @pytest.mark.asyncio
    async def test_player_b_timeout_on_parity_choice(self, match_conductor):
        """Player B timeouts on CHOOSE_PARITY -> Player A wins."""
        match_id, round_id = "M1", 1
        p1, p2 = "P01", "P02"
        conv_id = "conv-1"
        queue = asyncio.Queue()

        with patch.object(
            match_conductor, "_send_invitations", return_value={p1: True, p2: True}
        ), patch.object(
            match_conductor, "_wait_for_join_acks", return_value={p1: "ack", p2: "ack"}
        ), patch.object(
            match_conductor, "_send_parity_calls"
        ), patch.object(
            match_conductor, "_wait_for_parity_choices", return_value={p1: "odd", p2: None}
        ), patch.object(
            match_conductor, "_finish_match_with_technical_loss", return_value={"winner": p1}
        ) as mock_finish:
            match_conductor.game_logic.award_technical_loss = MagicMock(
                return_value=(p1, "TECHNICAL_LOSS", "WIN")
            )

            result = await match_conductor.conduct_match(match_id, round_id, p1, p2, conv_id, queue)

            mock_finish.assert_called_once()


class TestMatchConductorInvalidMoves:
    """Test invalid parity choice handling."""

    @pytest.mark.asyncio
    async def test_player_a_invalid_parity_choice(self, match_conductor):
        """Player A makes invalid choice (not 'even' or 'odd') -> technical loss."""
        match_id, round_id = "M1", 1
        p1, p2 = "P01", "P02"
        conv_id = "conv-1"
        queue = asyncio.Queue()

        with patch.object(
            match_conductor, "_send_invitations", return_value={p1: True, p2: True}
        ), patch.object(
            match_conductor, "_wait_for_join_acks", return_value={p1: "ack", p2: "ack"}
        ), patch.object(
            match_conductor, "_send_parity_calls"
        ), patch.object(
            match_conductor, "_wait_for_parity_choices", return_value={p1: "invalid", p2: "even"}
        ):
            result = await match_conductor.conduct_match(match_id, round_id, p1, p2, conv_id, queue)

            assert result["technical_loss"] is True
            assert "invalid choice" in result["reason"].lower()
            assert p1 in result["reason"]
            assert result.get("offending_player") == p1

    @pytest.mark.asyncio
    async def test_player_b_invalid_parity_choice(self, match_conductor):
        """Player B makes invalid choice -> technical loss."""
        match_id, round_id = "M1", 1
        p1, p2 = "P01", "P02"
        conv_id = "conv-1"
        queue = asyncio.Queue()

        with patch.object(
            match_conductor, "_send_invitations", return_value={p1: True, p2: True}
        ), patch.object(
            match_conductor, "_wait_for_join_acks", return_value={p1: "ack", p2: "ack"}
        ), patch.object(
            match_conductor, "_send_parity_calls"
        ), patch.object(
            match_conductor, "_wait_for_parity_choices", return_value={p1: "odd", p2: "INVALID"}
        ):
            result = await match_conductor.conduct_match(match_id, round_id, p1, p2, conv_id, queue)

            assert result["technical_loss"] is True
            assert p2 in result["reason"]
            assert result.get("offending_player") == p2


class TestMatchConductorInvitationFailures:
    """Test invitation sending failures."""

    @pytest.mark.asyncio
    async def test_both_invitations_fail(self, match_conductor):
        """Both invitation sends fail -> technical loss."""
        match_id, round_id = "M1", 1
        p1, p2 = "P01", "P02"
        conv_id = "conv-1"
        queue = asyncio.Queue()

        with patch.object(match_conductor, "_send_invitations", return_value=None):
            result = await match_conductor.conduct_match(match_id, round_id, p1, p2, conv_id, queue)

            assert result["winner"] == "NONE"
            assert result["technical_loss"] is True
            assert "invitation" in result["reason"].lower()


class TestMatchConductorHelperMethods:
    """Test helper methods for points and timestamps."""

    def test_points_for_status_win(self, match_conductor):
        """WIN status should return win_points (3 by default)."""
        # Setup scoring in league config
        match_conductor.scoring = {"win_points": 3, "draw_points": 1, "loss_points": 0}

        points = match_conductor._points_for_status("WIN")
        assert points == 3

    def test_points_for_status_draw(self, match_conductor):
        """DRAW status should return draw_points (1 by default)."""
        match_conductor.scoring = {"win_points": 3, "draw_points": 1, "loss_points": 0}

        points = match_conductor._points_for_status("DRAW")
        assert points == 1

    def test_points_for_status_loss(self, match_conductor):
        """LOSS status should return loss_points (0 by default)."""
        match_conductor.scoring = {"win_points": 3, "draw_points": 1, "loss_points": 0}

        points = match_conductor._points_for_status("LOSS")
        assert points == 0

    def test_points_for_status_technical_loss(self, match_conductor):
        """TECHNICAL_LOSS status should return loss_points (0)."""
        match_conductor.scoring = {"win_points": 3, "draw_points": 1, "loss_points": 0}

        points = match_conductor._points_for_status("TECHNICAL_LOSS")
        assert points == 0

    def test_timestamp_format(self, match_conductor):
        """Timestamp should be ISO 8601 with Z suffix."""
        timestamp = match_conductor._timestamp()

        # Should match format: YYYY-MM-DDTHH:MM:SSZ
        import re

        pattern = r"^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}Z$"
        assert re.match(pattern, timestamp), f"Invalid timestamp: {timestamp}"

    def test_create_technical_loss_result(self, match_conductor):
        """_create_technical_loss_result should create proper result dict."""
        match_conductor.scoring = {"win_points": 3, "draw_points": 1, "loss_points": 0}

        result = match_conductor._create_technical_loss_result(
            match_id="M1",
            round_id=1,
            player_a_id="P01",
            player_b_id="P02",
            reason="Test timeout",
            transcript=[],
        )

        assert result["match_id"] == "M1"
        assert result["round_id"] == 1
        assert result["winner"] == "NONE"
        assert result["technical_loss"] is True
        assert result["reason"] == "Test timeout"
        assert result["score"]["P01"] == 0
        assert result["score"]["P02"] == 0
        assert result["lifecycle"]["state"] == "FAILED"


class TestMatchConductorSendToPlayer:
    """Test _send_to_player error handling."""

    @pytest.mark.asyncio
    async def test_send_to_player_missing_endpoint(self, match_conductor):
        """Sending to player with no endpoint should raise ValueError with E018."""
        # Remove P01 endpoint
        match_conductor.player_endpoints = {}

        with pytest.raises(ValueError, match="not found"):
            await match_conductor._send_to_player("P01", "TEST_METHOD", {})

    @pytest.mark.asyncio
    async def test_send_to_player_success(self, match_conductor):
        """Successful send_to_player should return response."""
        with patch(
            "agents.referee_REF01.match_conductor.call_with_retry", new_callable=AsyncMock
        ) as mock_retry:
            mock_retry.return_value = {"result": "success"}

            result = await match_conductor._send_to_player("P01", "TEST", {"data": "test"})

            assert result == {"result": "success"}
            mock_retry.assert_called_once()

    @pytest.mark.asyncio
    async def test_send_to_player_connection_failure(self, match_conductor):
        """Connection failure should log E006 PLAYER_NOT_AVAILABLE."""
        with patch(
            "agents.referee_REF01.match_conductor.call_with_retry", new_callable=AsyncMock
        ) as mock_retry:
            mock_retry.side_effect = Exception("Connection refused")

            with pytest.raises(Exception):
                await match_conductor._send_to_player("P01", "TEST", {})


class TestMatchConductorSendMatchResult:
    """Test _send_match_result_to_league_manager."""

    @pytest.mark.asyncio
    async def test_send_match_result_no_endpoint(self, match_conductor):
        """Missing League Manager endpoint should log error and return."""
        match_conductor.league_manager_endpoint = None

        # Should not raise, just log error
        await match_conductor._send_match_result_to_league_manager(
            "M1", 1, "P01", "P01", "P02", "WIN", "LOSS", "conv-1"
        )

        # Verify error was logged
        match_conductor.std_logger.error.assert_called()

    @pytest.mark.asyncio
    async def test_send_match_result_success(self, match_conductor):
        """Successful match result report."""
        with patch(
            "agents.referee_REF01.match_conductor.call_with_retry", new_callable=AsyncMock
        ) as mock_retry:
            mock_retry.return_value = {"status": "ACCEPTED"}

            await match_conductor._send_match_result_to_league_manager(
                "M1", 1, "P01", "P01", "P02", "WIN", "LOSS", "conv-1"
            )

            mock_retry.assert_called_once()
            # Verify correct method was called
            assert mock_retry.call_args[1]["method"] == "MATCH_RESULT_REPORT"

    @pytest.mark.asyncio
    async def test_send_match_result_failure(self, match_conductor):
        """Failed match result report should log error but not raise."""
        with patch(
            "agents.referee_REF01.match_conductor.call_with_retry", new_callable=AsyncMock
        ) as mock_retry:
            mock_retry.side_effect = Exception("LM unavailable")

            # Should not raise, just log
            await match_conductor._send_match_result_to_league_manager(
                "M1", 1, "P01", "P01", "P02", "WIN", "LOSS", "conv-1"
            )

            match_conductor.std_logger.error.assert_called()
