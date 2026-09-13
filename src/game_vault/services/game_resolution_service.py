"""Resolve discovered source game candidates against the Game Vault catalogue."""

from game_vault.config import (
    IdentifierTypeEnum,
    PlatformEnum,
    PlayStationSourceTypeEnum,
    SourceTypeMappingEnum,
)
from game_vault.databases.external_identifier_repository import (
    ExternalIdentifierRepository,
)
from game_vault.databases.source_game_mapping_repository import (
    SourceGameMappingRepository,
)
from game_vault.models.playstation import PlayStationTitleCandidate
from game_vault.models.resolution import (
    MatchMethodEnum,
    ResolutionResult,
    ResolutionStatusEnum,
)


class GameResolutionService:
    """Resolve source title candidates to existing Game Vault releases."""

    def __init__(
        self,
        source_game_mapping_repository: SourceGameMappingRepository,
        external_identifier_repository: ExternalIdentifierRepository,
    ) -> None:
        self.source_game_mapping_repository = source_game_mapping_repository
        self.external_identifier_repository = external_identifier_repository

    def resolve(
        self,
        candidate: PlayStationTitleCandidate,
    ) -> ResolutionResult:
        """
        Resolve a PlayStation title candidate to an existing game release.

        Resolution uses strongest evidence first:

        1. Existing source game mappings.
        2. Existing external identifiers.
        3. Otherwise, the candidate remains unresolved.

        :param candidate: Candidate discovered from PlayStation data.
        :return: The resolution result.
        """
        source_matches = self._find_source_mapping_matches(candidate)
        identifier_matches = self._find_identifier_matches(candidate)

        # Existing source mappings are our strongest evidence.
        if source_matches:
            return self._resolve_source_matches(
                source_matches,
                identifier_matches,
            )

        # If no mapping exists, identifiers are our next best evidence.
        if identifier_matches:
            return self._resolve_identifier_matches(identifier_matches)

        return ResolutionResult(
            status=ResolutionStatusEnum.UNMATCHED,
        )

    def _find_source_mapping_matches(
        self,
        candidate: PlayStationTitleCandidate,
    ) -> dict[str, list[str]]:
        """
        Find existing mappings for all source records on a candidate.

        Returns:

            {
                "minecraft-ps5": [
                    "PPSA17221_00",
                    "NPWR41319_00",
                ]
            }
        """
        matches: dict[str, list[str]] = {}

        source_namespaces = {
            PlayStationSourceTypeEnum.PLAYED_TITLE: (
                SourceTypeMappingEnum.PLAYSTATION_TITLE
            ),
            PlayStationSourceTypeEnum.TROPHY_TITLE: (
                SourceTypeMappingEnum.PLAYSTATION_TROPHY_SET
            ),
        }

        for source_key in candidate.source_key:
            mapping = self.source_game_mapping_repository.get(
                source=source_namespaces[source_key.source_type],
                source_id=source_key.source_id,
            )

            if mapping is None:
                continue

            matches.setdefault(
                mapping.game_release_id,
                [],
            ).append(source_key.source_id)

        return matches

    def _find_identifier_matches(
        self,
        candidate: PlayStationTitleCandidate,
    ) -> dict[str, list[str]]:
        """
        Find releases matching identifiers discovered from PlayStation.

        Returns release IDs mapped to the identifier values that matched.
        """
        matches: dict[str, list[str]] = {}

        identifiers = [
            *[
                (
                    IdentifierTypeEnum.TITLE_ID.value,
                    value,
                )
                for value in candidate.title_ids
            ],
            *[
                (
                    IdentifierTypeEnum.NP_COMMUNICATION_ID.value,
                    value,
                )
                for value in candidate.np_communication_ids
            ],
            *[
                (
                    IdentifierTypeEnum.NP_TITLE_ID.value,
                    value,
                )
                for value in candidate.np_title_ids
            ],
        ]

        for identifier_type, value in identifiers:
            release_ids = self.external_identifier_repository.find_game_release_ids(
                service=PlatformEnum.PLAYSTATION.value,
                identifier_type=identifier_type,
                value=value,
            )

            for release_id in release_ids:
                matches.setdefault(
                    release_id,
                    [],
                ).append(value)

        return matches

    @staticmethod
    def _resolve_source_matches(
        source_matches: dict[str, list[str]],
        identifier_matches: dict[str, list[str]],
    ) -> ResolutionResult:
        """Resolve matches found through existing source mappings."""
        release_ids = set(source_matches)

        if len(release_ids) > 1:
            return ResolutionResult(
                status=ResolutionStatusEnum.AMBIGUOUS,
                candidate_release_ids=sorted(release_ids),
                matched_values=[
                    value for values in source_matches.values() for value in values
                ],
            )

        release_id = next(iter(release_ids))

        # Check that external identifiers don't contradict
        # the authoritative source mapping.
        conflicting_identifier_ids = set(identifier_matches) - {release_id}

        if conflicting_identifier_ids:
            candidate_ids = {
                release_id,
                *conflicting_identifier_ids,
            }

            return ResolutionResult(
                status=ResolutionStatusEnum.AMBIGUOUS,
                candidate_release_ids=sorted(candidate_ids),
                matched_values=[
                    value
                    for values in (
                        *source_matches.values(),
                        *identifier_matches.values(),
                    )
                    for value in values
                ],
            )

        return ResolutionResult(
            status=ResolutionStatusEnum.MATCHED,
            game_release_id=release_id,
            match_method=MatchMethodEnum.SOURCE_MAPPING,
            confidence=1.0,
            matched_values=source_matches[release_id],
        )

    @staticmethod
    def _resolve_identifier_matches(
        identifier_matches: dict[str, list[str]],
    ) -> ResolutionResult:
        """Resolve matches found through external identifiers."""
        release_ids = set(identifier_matches)

        if len(release_ids) > 1:
            return ResolutionResult(
                status=ResolutionStatusEnum.AMBIGUOUS,
                candidate_release_ids=sorted(release_ids),
                matched_values=[
                    value for values in identifier_matches.values() for value in values
                ],
            )

        release_id = next(iter(release_ids))

        return ResolutionResult(
            status=ResolutionStatusEnum.MATCHED,
            game_release_id=release_id,
            match_method=MatchMethodEnum.EXTERNAL_IDENTIFIER,
            confidence=1.0,
            matched_values=identifier_matches[release_id],
        )
