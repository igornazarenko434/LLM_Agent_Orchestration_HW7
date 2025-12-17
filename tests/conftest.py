"""
Shared test fixtures for the Even/Odd League project.
"""

from unittest.mock import MagicMock

import pytest


@pytest.fixture
def mock_mcp_server():
    """
    Fixture for a mock MCP server.

    Returns a MagicMock object simulating an MCP server interface
    that can be used to test agent interactions without a real network.
    """
    mock = MagicMock()
    # Configure default behavior for common MCP methods if needed
    mock.start.return_value = None
    mock.stop.return_value = None
    return mock
