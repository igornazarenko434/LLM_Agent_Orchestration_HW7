"""
League Manager agent (Missions 7.9-7.12).

Provides centralized league orchestration:
- Registration (referees, players)
- Scheduling (round-robin)
- Standings calculation
- Match result handling
"""

from agents.league_manager.server import LeagueManager

__all__ = ["LeagueManager"]
