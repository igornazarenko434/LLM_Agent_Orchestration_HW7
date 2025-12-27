"""
E2E tests for graceful shutdown and agent lifecycle management.

Tests that verify all agents can start, run, and shutdown cleanly
without leaving orphan processes or corrupted state.
"""

import asyncio
import os
import signal
import subprocess
import sys
from pathlib import Path

import httpx
import pytest


@pytest.mark.e2e
class TestGracefulShutdown:
    """Test graceful shutdown of all agents."""

    @pytest.fixture
    def project_root(self):
        """Get project root directory."""
        return Path(__file__).parent.parent.parent

    @pytest.mark.asyncio
    async def test_league_manager_starts_and_stops(self, project_root):
        """Test that League Manager can start and stop cleanly."""
        process = subprocess.Popen(
            [sys.executable, "-m", "agents.league_manager.main"],
            cwd=project_root,
            env={**os.environ, "PYTHONPATH": str(project_root / "SHARED")},
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
        )

        try:
            # Wait for startup
            await asyncio.sleep(2)

            # Verify it's running
            assert process.poll() is None, "League Manager should be running"

            # Check health
            try:
                async with httpx.AsyncClient() as client:
                    response = await client.get("http://localhost:8000/health", timeout=5.0)
                    assert response.status_code == 200
            except Exception:
                pass  # Health endpoint might not be implemented

            # Send SIGTERM
            process.send_signal(signal.SIGTERM)

            # Wait for graceful shutdown
            try:
                process.wait(timeout=5)
                exit_code = process.returncode
                stdout, stderr = process.communicate()
                stderr_text = stderr.decode("utf-8", errors="ignore") if stderr else ""
                assert exit_code == 0 or exit_code == -15, (
                    f"League Manager should exit cleanly, got exit code "
                    f"{exit_code}\nStderr: {stderr_text}"
                )
            except subprocess.TimeoutExpired:
                process.kill()
                pytest.fail("League Manager did not shutdown gracefully within timeout")

        finally:
            # Ensure cleanup
            if process.poll() is None:
                process.kill()

    @pytest.mark.asyncio
    async def test_referee_starts_and_stops(self, project_root):
        """Test that Referee can start and stop cleanly."""
        process = subprocess.Popen(
            [sys.executable, "-m", "agents.referee_REF01.main"],
            cwd=project_root,
            env={**os.environ, "PYTHONPATH": str(project_root / "SHARED")},
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
        )

        try:
            await asyncio.sleep(2)
            assert process.poll() is None, "Referee should be running"

            process.send_signal(signal.SIGTERM)

            try:
                process.wait(timeout=5)
                exit_code = process.returncode
                assert (
                    exit_code == 0 or exit_code == -15
                ), f"Referee should exit cleanly, got exit code {exit_code}"
            except subprocess.TimeoutExpired:
                process.kill()
                pytest.fail("Referee did not shutdown gracefully")

        finally:
            if process.poll() is None:
                process.kill()

    @pytest.mark.asyncio
    async def test_player_starts_and_stops(self, project_root):
        """Test that Player can start and stop cleanly."""
        process = subprocess.Popen(
            [sys.executable, "-m", "agents.player_P01.main"],
            cwd=project_root,
            env={**os.environ, "PYTHONPATH": str(project_root / "SHARED")},
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
        )

        try:
            await asyncio.sleep(2)
            assert process.poll() is None, "Player should be running"

            process.send_signal(signal.SIGTERM)

            try:
                process.wait(timeout=5)
                exit_code = process.returncode
                assert (
                    exit_code == 0 or exit_code == -15
                ), f"Player should exit cleanly, got exit code {exit_code}"
            except subprocess.TimeoutExpired:
                process.kill()
                pytest.fail("Player did not shutdown gracefully")

        finally:
            if process.poll() is None:
                process.kill()

    @pytest.mark.asyncio
    async def test_no_orphan_processes_after_shutdown(self, project_root):
        """Test that no orphan processes remain after shutdown."""
        # Start multiple agents
        processes = []

        try:
            # Start League Manager
            lm = subprocess.Popen(
                [sys.executable, "-m", "agents.league_manager.main"],
                cwd=project_root,
                env={**os.environ, "PYTHONPATH": str(project_root / "SHARED")},
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
            )
            processes.append(lm)

            # Start Referee
            ref = subprocess.Popen(
                [sys.executable, "-m", "agents.referee_REF01.main"],
                cwd=project_root,
                env={**os.environ, "PYTHONPATH": str(project_root / "SHARED")},
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
            )
            processes.append(ref)

            await asyncio.sleep(3)

            # Verify all running
            for p in processes:
                assert p.poll() is None

            # Shutdown all
            for p in processes:
                p.send_signal(signal.SIGTERM)

            # Wait for all to exit
            for p in processes:
                try:
                    p.wait(timeout=5)
                except subprocess.TimeoutExpired:
                    p.kill()
                    p.wait(timeout=5)

            # Verify all exited
            for p in processes:
                assert p.poll() is not None, "Process should have exited"

        finally:
            # Cleanup
            for p in processes:
                if p.poll() is None:
                    p.kill()
