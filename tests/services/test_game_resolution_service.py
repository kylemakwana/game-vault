from unittest.mock import create_autospec

import pytest

from game_vault.config import (
    PlatformEnum,
    PlayStationPlatformEnum,
    SourceTypeMappingEnum,
)
from game_vault.databases.external_identifier_repository import (
    ExternalIdentifierRepository,
)
from game_vault.databases.source_game_mapping_repository import (
    SourceGameMappingRepository,
)
from game_vault.models.mapping import SourceGameMapping
from game_vault.models.playstation import (
    PlayStationSourceKey,
    PlayStationTitleCandidate,
)
from game_vault.models.resolution import (
    MatchMethodEnum,
    ResolutionResult,
    ResolutionStatusEnum,
)
from game_vault.services.game_resolution_service import GameResolutionService


@pytest.fixture
def candidate():
    return PlayStationTitleCandidate(
        source_key=[
            PlayStationSourceKey.model_validate(
                {"source_type": "Played Title", "source_id": "PPSA001"}
            ),
            PlayStationSourceKey.model_validate(
                {"source_type": "Trophy Title", "source_id": "NPWR001"}
            ),
        ],
        names=["Test Game"],
        platforms=[PlayStationPlatformEnum("PS5")],
        title_ids=["PPSA001"],
        np_communication_ids=["NPWR001"],
        np_title_ids=["NP001"],
    )


@pytest.fixture
def source_repository():
    repository = create_autospec(SourceGameMappingRepository, instance=True)
    repository.get.return_value = None
    return repository


@pytest.fixture
def identifier_repository():
    repository = create_autospec(ExternalIdentifierRepository, instance=True)
    repository.find_game_release_ids.return_value = []
    return repository


@pytest.fixture
def service(source_repository, identifier_repository):
    return GameResolutionService(source_repository, identifier_repository)


def mapping(source_id, release_id):
    return SourceGameMapping(
        source=PlatformEnum.PLAYSTATION,
        source_id=source_id,
        game_release_id=release_id,
        match_method=MatchMethodEnum.MANUAL,
    )


def test_resolve_returns_unmatched_when_no_evidence_matches(service, candidate):
    assert service.resolve(candidate) == ResolutionResult(
        status=ResolutionStatusEnum("unmatched")
    )


def test_resolve_matches_existing_source_mapping(service, candidate, source_repository):
    source_repository.get.side_effect = [mapping("PPSA001", "game-ps5"), None]
    assert service.resolve(candidate) == ResolutionResult(
        status=ResolutionStatusEnum.MATCHED,
        game_release_id="game-ps5",
        match_method=MatchMethodEnum.SOURCE_MAPPING,
        confidence=1.0,
        matched_values=["PPSA001"],
    )
    source_repository.get.assert_any_call(
        source=SourceTypeMappingEnum.PLAYSTATION_TITLE, source_id="PPSA001"
    )
    source_repository.get.assert_any_call(
        source=SourceTypeMappingEnum.PLAYSTATION_TROPHY_SET, source_id="NPWR001"
    )


def assert_identifier_match(service, candidate, repository, identifier_type, value):
    def find(*, service, identifier_type, value):
        return ["game-ps5"] if (service, identifier_type, value) == expected else []

    expected = ("PlayStation", identifier_type, value)
    repository.find_game_release_ids.side_effect = find
    assert service.resolve(candidate) == ResolutionResult(
        status=ResolutionStatusEnum.MATCHED,
        game_release_id="game-ps5",
        match_method=MatchMethodEnum.EXTERNAL_IDENTIFIER,
        confidence=1.0,
        matched_values=[value],
    )
    repository.find_game_release_ids.assert_any_call(
        service=PlatformEnum.PLAYSTATION,
        identifier_type=identifier_type,
        value=value,
    )


def test_resolve_matches_external_title_id(service, candidate, identifier_repository):
    assert_identifier_match(
        service, candidate, identifier_repository, "TITLE_ID", "PPSA001"
    )


def test_resolve_matches_np_communication_id(service, candidate, identifier_repository):
    assert_identifier_match(
        service, candidate, identifier_repository, "NP_COMMUNICATION_ID", "NPWR001"
    )


def test_resolve_matches_np_title_id(service, candidate, identifier_repository):
    assert_identifier_match(
        service, candidate, identifier_repository, "NP_TITLE_ID", "NP001"
    )


def test_resolve_source_mapping_takes_priority_over_identifier(
    service,
    candidate,
    source_repository,
    identifier_repository,
):
    source_repository.get.side_effect = [mapping("PPSA001", "game-ps5"), None]
    identifier_repository.find_game_release_ids.return_value = ["game-ps5"]
    assert service.resolve(candidate) == ResolutionResult(
        status=ResolutionStatusEnum.MATCHED,
        game_release_id="game-ps5",
        match_method=MatchMethodEnum.SOURCE_MAPPING,
        confidence=1.0,
        matched_values=["PPSA001"],
    )


def test_resolve_returns_ambiguous_for_conflicting_source_mappings(
    service,
    candidate,
    source_repository,
):
    source_repository.get.side_effect = [
        mapping("PPSA001", "z-game"),
        mapping("NPWR001", "a-game"),
    ]
    assert service.resolve(candidate) == ResolutionResult(
        status=ResolutionStatusEnum.AMBIGUOUS,
        candidate_release_ids=["a-game", "z-game"],
        matched_values=["PPSA001", "NPWR001"],
    )


def test_resolve_returns_ambiguous_when_identifiers_match_different_releases(
    service,
    candidate,
    identifier_repository,
):
    identifier_repository.find_game_release_ids.side_effect = [
        ["z-game"],
        ["a-game"],
        [],
    ]
    assert service.resolve(candidate) == ResolutionResult(
        status=ResolutionStatusEnum.AMBIGUOUS,
        candidate_release_ids=["a-game", "z-game"],
        matched_values=["PPSA001", "NPWR001"],
    )


def test_resolve_returns_ambiguous_when_identifier_contradicts_source_mapping(
    service,
    candidate,
    source_repository,
    identifier_repository,
):
    source_repository.get.side_effect = [mapping("PPSA001", "z-game"), None]
    identifier_repository.find_game_release_ids.side_effect = [[], ["a-game"], []]
    assert service.resolve(candidate) == ResolutionResult(
        status=ResolutionStatusEnum.AMBIGUOUS,
        candidate_release_ids=["a-game", "z-game"],
        matched_values=["PPSA001", "NPWR001"],
    )


def test_resolve_returns_ambiguous_when_one_identifier_matches_multiple_releases(
    service,
    candidate,
    identifier_repository,
):
    identifier_repository.find_game_release_ids.side_effect = [
        ["z-game", "a-game"],
        [],
        [],
    ]
    result = service.resolve(candidate)
    assert result == ResolutionResult(
        status=ResolutionStatusEnum.AMBIGUOUS,
        candidate_release_ids=["a-game", "z-game"],
        matched_values=["PPSA001", "PPSA001"],
    )


def test_resolve_combines_agreeing_source_evidence(
    service, candidate, source_repository
):
    source_repository.get.side_effect = [
        mapping("PPSA001", "game-ps5"),
        mapping("NPWR001", "game-ps5"),
    ]
    result = service.resolve(candidate)
    assert result.game_release_id == "game-ps5"
    assert result.matched_values == ["PPSA001", "NPWR001"]
    assert result.status == ResolutionStatusEnum.MATCHED


def test_resolve_combines_agreeing_identifiers_without_mutating_candidate(
    service,
    candidate,
    identifier_repository,
):
    before = candidate.model_dump()
    identifier_repository.find_game_release_ids.return_value = ["game-ps5"]
    assert service.resolve(candidate) == ResolutionResult(
        status=ResolutionStatusEnum.MATCHED,
        game_release_id="game-ps5",
        match_method=MatchMethodEnum.EXTERNAL_IDENTIFIER,
        confidence=1.0,
        matched_values=["PPSA001", "NPWR001", "NP001"],
    )
    assert candidate.model_dump() == before


def test_resolve_empty_evidence_does_not_query_repositories(
    service,
    candidate,
    source_repository,
    identifier_repository,
):
    candidate.source_key = []
    candidate.title_ids = []
    candidate.np_communication_ids = []
    candidate.np_title_ids = []
    assert service.resolve(candidate) == ResolutionResult(
        status=ResolutionStatusEnum.UNMATCHED
    )
    source_repository.get.assert_not_called()
    identifier_repository.find_game_release_ids.assert_not_called()
