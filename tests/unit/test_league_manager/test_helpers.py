import pytest
from agents.league_manager.server import LeagueManager

from league_sdk.repositories import StandingsRepository


@pytest.mark.unit
def test_sender_id_extractors():
    lm = LeagueManager(agent_id="LM01", league_id="league_2025_even_odd")
    assert lm._referee_id_from_sender("referee:REF01") == "REF01"
    assert lm._referee_id_from_sender("player:P01") is None
    assert lm._player_id_from_sender("player:P01") == "P01"
    assert lm._player_id_from_sender("referee:REF01") is None


@pytest.mark.unit
def test_update_standings_uses_scoring_config(tmp_path):
    lm = LeagueManager(agent_id="LM01", league_id="league_2025_even_odd")
    lm.standings_repo = StandingsRepository(lm.league_id, data_root=tmp_path)

    result = {
        "winner": "P01",
        "score": {"P01": 3, "P02": 0},
    }
    updated = lm.update_standings(result)
    assert sorted(updated) == ["P01", "P02"]

    standings = lm.standings_repo.load()["standings"]
    points = {row["player_id"]: row["points"] for row in standings}
    assert points["P01"] == lm.league_config.scoring.points_for_win
    assert points["P02"] == lm.league_config.scoring.points_for_loss
