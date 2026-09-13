import pytest
from pydantic import ValidationError

from game_vault.models.resolution import ResolutionResult


def test_resolution_defaults_are_independent():
    first = ResolutionResult(status="unmatched")
    second = ResolutionResult(status="unmatched")
    first.candidate_release_ids.append("game-ps5")
    first.matched_values.append("PPSA001")
    assert second.candidate_release_ids == []
    assert second.matched_values == []
    assert second.game_release_id is None
    assert second.match_method is None
    assert second.confidence is None


@pytest.mark.parametrize(
    "method", ["source_mapping", "external_identifier", "title_platform"]
)
def test_resolution_round_trips_enum_values(method):
    result = ResolutionResult(
        status="matched",
        game_release_id="game-ps5",
        match_method=method,
        confidence=1.0,
        matched_values=["PPSA001"],
    )
    assert result.status.value == "matched"
    assert result.match_method is not None
    assert result.match_method.value == method
    assert ResolutionResult.model_validate_json(result.model_dump_json()) == result


@pytest.mark.parametrize(
    "values", [{"status": "invalid"}, {"status": "matched", "match_method": "invalid"}]
)
def test_resolution_rejects_unknown_enum_values(values):
    with pytest.raises(ValidationError):
        ResolutionResult.model_validate(values)
