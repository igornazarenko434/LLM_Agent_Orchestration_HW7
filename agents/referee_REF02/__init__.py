"""
Referee REF02 agent (imports from generic referee implementation).

This module provides access to the RefereeAgent class for REF02.
All implementation is shared with REF01 via the generic referee_REF01 module.
"""

from agents.referee_REF01.server import RefereeAgent

__all__ = ["RefereeAgent"]
