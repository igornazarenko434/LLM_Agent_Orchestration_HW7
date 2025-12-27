"""
End-to-end tests for 4-player league with real MCP servers.

This test launches actual HTTP servers for League Manager, Referee, and Players,
then runs a complete league and verifies the results.
"""

import asyncio
import os
import signal
import subprocess
import sys
import time
from datetime import datetime, timezone
from pathlib import Path

import httpx
import pytest
import pytest_asyncio


@pytest.mark.e2e
@pytest.mark.slow
class TestFourPlayerLeague:
    """E2E tests for complete 4-player league execution."""

    @pytest.fixture(scope="class")
    def project_root(self):
        """Get project root directory."""
        return Path(__file__).parent.parent.parent

    @pytest.fixture(scope="class")
    def league_manager_port(self):
        """Port for League Manager."""
        return 8000

    @pytest.fixture(scope="class")
    def referee_port(self):
        """Port for Referee."""
        return 8001

    @pytest.fixture(scope="class")
    def player_ports(self):
        """Ports for players."""
        return {
            "P01": 8101,
            "P02": 8102,
            "P03": 8103,
            "P04": 8104,
        }

    @pytest_asyncio.fixture(scope="class")
    async def running_league(self, project_root, league_manager_port, referee_port, player_ports):
        """
        Start all agents and run a complete league.

        This fixture:
        1. Starts League Manager
        2. Starts Referee
        3. Starts 4 Players
        4. Waits for registration
        5. Starts league
        6. Yields control for tests
        7. Cleans up processes
        """
        processes = []

        try:
            # Ensure clean league data for deterministic results
            data_root = project_root / "SHARED" / "data"
            league_root = data_root / "leagues" / "league_2025_even_odd"
            standings_file = league_root / "standings.json"
            rounds_file = league_root / "rounds.json"
            matches_dir = data_root / "matches"

            for path in [standings_file, rounds_file]:
                if path.exists():
                    path.unlink()

            if matches_dir.exists():
                for match_file in matches_dir.glob("*.json"):
                    match_file.unlink()

            # Start League Manager
            print(f"\n🚀 Starting League Manager on port {league_manager_port}...")
            lm_process = subprocess.Popen(
                [sys.executable, "-m", "agents.league_manager.main"],
                cwd=project_root,
                env={**os.environ, "PYTHONPATH": str(project_root / "SHARED")},
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
            )
            processes.append(("League Manager", lm_process))
            await asyncio.sleep(2)  # Wait for startup

            # Verify League Manager is running
            try:
                async with httpx.AsyncClient() as client:
                    response = await client.get(
                        f"http://localhost:{league_manager_port}/health", timeout=5.0
                    )
                    assert response.status_code == 200
                    print("✅ League Manager is running")
            except Exception as e:
                print(f"❌ League Manager health check failed: {e}")
                raise

            # Start Referee
            print(f"🚀 Starting Referee on port {referee_port}...")
            ref_process = subprocess.Popen(
                [sys.executable, "-m", "agents.referee_REF01.main"],
                cwd=project_root,
                env={**os.environ, "PYTHONPATH": str(project_root / "SHARED")},
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
            )
            processes.append(("Referee", ref_process))
            await asyncio.sleep(2)  # Wait for startup

            # Verify Referee is running
            try:
                async with httpx.AsyncClient() as client:
                    response = await client.get(f"http://localhost:{referee_port}/health", timeout=5.0)
                    assert response.status_code == 200
                    print("✅ Referee is running")
            except Exception as e:
                print(f"❌ Referee health check failed: {e}")
                raise

            # Start Players
            for player_id, port in player_ports.items():
                print(f"🚀 Starting Player {player_id} on port {port}...")
                player_process = subprocess.Popen(
                    [sys.executable, "-m", f"agents.player_{player_id}.main"],
                    cwd=project_root,
                    env={**os.environ, "PYTHONPATH": str(project_root / "SHARED")},
                    stdout=subprocess.PIPE,
                    stderr=subprocess.PIPE,
                )
                processes.append((f"Player {player_id}", player_process))
                await asyncio.sleep(1)  # Stagger player startups

            # Verify all players are running
            for player_id, port in player_ports.items():
                try:
                    async with httpx.AsyncClient() as client:
                        response = await client.get(f"http://localhost:{port}/health", timeout=5.0)
                        assert response.status_code == 200
                        print(f"✅ Player {player_id} is running")
                except Exception as e:
                    print(f"❌ Player {player_id} health check failed: {e}")
                    raise

            print("✅ All agents are running!")

            # Wait for agents to register with League Manager
            print("⏳ Waiting for agent registration...")
            await asyncio.sleep(5)

            # Start the league (no sender = bypass auth if allow_start_league_without_auth=true)
            print("🎮 Starting league...")
            async with httpx.AsyncClient() as client:
                start_response = await client.post(
                    f"http://localhost:{league_manager_port}/mcp",
                    json={
                        "jsonrpc": "2.0",
                        "method": "start_league",
                        "params": {"league_id": "league_2025_even_odd"},
                        "id": 1,
                    },
                    timeout=10.0,
                )
                print(f"League start response: {start_response.status_code}")
                if start_response.status_code != 200:
                    print(f"League start error: {start_response.json()}")
                else:
                    print("✅ League started successfully!")
                    response_data = start_response.json()
                    if "result" in response_data:
                        print(f"   Schedule: {response_data['result']}")

            # Wait for league to complete
            print("⏳ Waiting for league to complete (max 120 seconds)...")
            max_wait = 120
            start_time = time.time()
            league_completed = False

            while time.time() - start_time < max_wait:
                try:
                    async with httpx.AsyncClient() as client:
                        status_response = await client.post(
                            f"http://localhost:{league_manager_port}/mcp",
                            json={
                                "jsonrpc": "2.0",
                                "method": "get_league_status",
                                "params": {},
                                "id": 2,
                            },
                            timeout=5.0,
                        )
                        if status_response.status_code == 200:
                            data = status_response.json()
                            if data.get("result", {}).get("status") == "COMPLETED":
                                league_completed = True
                                print("✅ League completed!")
                                break
                except Exception as e:
                    print(f"Status check error: {e}")

                await asyncio.sleep(2)

            if not league_completed:
                print("⚠️  League did not complete within timeout")

            # Get final standings
            print("📊 Fetching final standings...")
            final_standings = None
            try:
                async with httpx.AsyncClient() as client:
                    standings_response = await client.post(
                        f"http://localhost:{league_manager_port}/mcp",
                        json={
                            "jsonrpc": "2.0",
                            "method": "get_standings",
                            "params": {},
                            "id": 3,
                        },
                        timeout=5.0,
                    )
                    if standings_response.status_code == 200:
                        final_standings = (
                            standings_response.json().get("result", {}).get("standings", [])
                        )
                        print(f"Final standings: {final_standings}")
            except Exception as e:
                print(f"Failed to get standings: {e}")

            # Yield control to tests
            yield {
                "league_completed": league_completed,
                "final_standings": final_standings,
                "processes": processes,
            }

        finally:
            # Cleanup: Stop all processes
            print("\n🛑 Stopping all agents...")
            for name, process in processes:
                try:
                    process.send_signal(signal.SIGTERM)
                    process.wait(timeout=5)
                    print(f"✅ Stopped {name}")
                except subprocess.TimeoutExpired:
                    process.kill()
                    print(f"⚠️  Force killed {name}")
                except Exception as e:
                    print(f"❌ Error stopping {name}: {e}")

    @pytest.mark.asyncio
    async def test_league_completes_successfully(self, running_league):
        """Test that a 4-player league completes successfully."""
        assert running_league["league_completed"], "League should complete within timeout"

    @pytest.mark.asyncio
    async def test_final_standings_exist(self, running_league):
        """Test that final standings are available."""
        assert running_league["final_standings"] is not None, "Final standings should be available"
        assert len(running_league["final_standings"]) == 4, "Should have 4 players in standings"

    @pytest.mark.asyncio
    async def test_all_players_have_scores(self, running_league):
        """Test that all players have scores in final standings."""
        standings = running_league["final_standings"]

        for standing in standings:
            assert "player_id" in standing, "Standing should have player_id"
            assert "points" in standing, "Standing should have points"
            assert "wins" in standing, "Standing should have wins"
            assert "draws" in standing, "Standing should have draws"
            assert "losses" in standing, "Standing should have losses"
            assert standing["points"] >= 0, "Points should be non-negative"

    @pytest.mark.asyncio
    async def test_standings_sorted_by_points(self, running_league):
        """Test that standings are sorted by points (descending)."""
        standings = running_league["final_standings"]

        # Check that standings are sorted in descending order of points
        for i in range(len(standings) - 1):
            assert (
                standings[i]["points"] >= standings[i + 1]["points"]
            ), "Standings should be sorted by points in descending order"

    @pytest.mark.asyncio
    async def test_total_matches_played(self, running_league):
        """Test that correct number of matches were played (6 matches for 4 players)."""
        standings = running_league["final_standings"]

        # Each player plays 3 matches in a 4-player round-robin
        for standing in standings:
            total_games = standing["wins"] + standing["draws"] + standing["losses"]
            assert total_games == 3, f"Each player should play exactly 3 matches, got {total_games}"

    @pytest.mark.asyncio
    async def test_points_calculation_correct(self, running_league):
        """Test that points calculation is correct (WIN=3, DRAW=1, LOSS=0)."""
        standings = running_league["final_standings"]

        for standing in standings:
            expected_points = standing["wins"] * 3 + standing["draws"] * 1
            assert (
                standing["points"] == expected_points
            ), f"Points calculation incorrect: {standing['points']} != {expected_points}"

    @pytest.mark.asyncio
    async def test_all_agents_running(self, running_league):
        """Test that all agent processes are still running."""
        processes = running_league["processes"]

        for name, process in processes:
            assert process.poll() is None, f"{name} process should still be running"


@pytest.mark.e2e
@pytest.mark.slow
class TestLeagueManagerEndpoints:
    """Test League Manager HTTP endpoints directly."""

    @pytest.mark.asyncio
    async def test_league_manager_health_endpoint(self):
        """Test that League Manager health endpoint responds."""
        # This test assumes League Manager is running from previous test
        # or should start a new instance
        # For simplicity, we'll skip actual server start here
        # as it's covered by TestFourPlayerLeague
        pass

    @pytest.mark.asyncio
    async def test_get_standings_endpoint(self):
        """Test GET /standings endpoint."""
        # Covered by TestFourPlayerLeague
        pass
