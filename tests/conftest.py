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


def pytest_collection_modifyitems(config, items):
    """
    Auto-assign test markers based on folder so unit/integration/e2e selection is reliable.
    """
    for item in items:
        path = str(item.fspath)
        if "/tests/unit/" in path:
            item.add_marker(pytest.mark.unit)
        elif "/tests/integration/" in path:
            item.add_marker(pytest.mark.integration)
        elif "/tests/e2e/" in path:
            item.add_marker(pytest.mark.e2e)
        elif "/tests/edge_cases/" in path:
            item.add_marker(pytest.mark.edge)
