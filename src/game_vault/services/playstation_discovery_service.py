"""Discover candidate game releases from PlayStation snapshot data."""

from game_vault.config import (
    IdentifierTypeEnum,
    PlayStationPlatformEnum,
    PlayStationTitleCategoryEnum,
)
from game_vault.models.playstation import (
    PlayStationPlayedTitle,
    PlayStationSnapshot,
    PlayStationSourceKey,
    PlayStationTitleCandidate,
    PlaystationTrophyTitle,
)


class PlayStationDiscoveryService:
    """Discover candidate game releases from PlayStation snapshot data."""

    def discover(
        self,
        snapshot: PlayStationSnapshot,
    ) -> list[PlayStationTitleCandidate]:
        """Discover candidate game releases from PlayStation snapshot data."""
        candidates = [
            self._candidate_from_played_title(played_title)
            for played_title in snapshot.played_titles
            if played_title.content_type == "game"
        ]

        for trophy_title in snapshot.trophy_titles:
            matching_candidate = next(
                (
                    candidate
                    for candidate in candidates
                    if (
                        candidate.played_title is not None
                        and candidate.trophy_title is None
                        and self._same_candidate(
                            candidate.played_title,
                            trophy_title,
                        )
                    )
                ),
                None,
            )

            if matching_candidate is None:
                candidates.append(self._candidate_from_trophy_title(trophy_title))
                continue

            self._merge_trophy_title(
                matching_candidate,
                trophy_title,
            )

        return candidates

    def _same_candidate(
        self,
        played: PlayStationPlayedTitle,
        trophy: PlaystationTrophyTitle,
    ) -> bool:
        """
        Return whether two PlayStation records likely represent one release.

        :param played: A ``PlayStationPlayedTitle`` record.
        :param trophy: A ``PlaystationTrophyTitle`` record.
        :return: Whether the records appear to represent the same release.
        """
        if not self._platforms_overlap(played, trophy):
            return False

        return self._normalise_title(played.name) == self._normalise_title(
            trophy.title_name
        )

    def _candidate_from_played_title(
        self,
        played_title: PlayStationPlayedTitle,
    ) -> PlayStationTitleCandidate:
        """
        Create a candidate from a ``PlayStationPlayedTitle`` record.

        :param played_title: The ``PlayStationPlayedTitle`` record.
        :return: A ``PlayStationTitleCandidate`` record.
        """
        platform = self._platform_from_category(played_title.reported_category)

        return PlayStationTitleCandidate(
            source_key=[
                PlayStationSourceKey(
                    source_type=IdentifierTypeEnum.PLAYED_TITLE.value,
                    source_id=played_title.title_id,
                )
            ],
            names=[played_title.name],
            platforms=[platform],
            product_ids=self._optional_list(played_title.title_id),
            np_communication_ids=[],
            np_title_ids=[],
            played_title=played_title,
            trophy_title=None,
        )

    def _candidate_from_trophy_title(
        self,
        trophy_title: PlaystationTrophyTitle,
    ) -> PlayStationTitleCandidate:
        """
        Create a candidate from a ``PlaystationTrophyTitle`` record.

        :param trophy_title: A ``PlaystationTrophyTitle`` record.
        :return: A ``PlayStationTitleCandidate`` record.
        """
        platforms: list[PlayStationPlatformEnum] = []

        for raw_platform in trophy_title.platforms:
            platform = self._map_platform(raw_platform)

            if platform not in platforms:
                platforms.append(platform)

        return PlayStationTitleCandidate(
            source_key=[
                PlayStationSourceKey(
                    source_type=IdentifierTypeEnum.TROPHY_TITLE.value,
                    source_id=trophy_title.np_communication_id,
                )
            ],
            names=[trophy_title.title_name],
            platforms=platforms,
            product_ids=[],
            np_communication_ids=[trophy_title.np_communication_id],
            np_title_ids=self._optional_list(trophy_title.np_title_id),
            played_title=None,
            trophy_title=trophy_title,
        )

    def _merge_trophy_title(
        self,
        candidate: PlayStationTitleCandidate,
        trophy_title: PlaystationTrophyTitle,
    ) -> None:
        """
        Merge trophy title evidence into an existing candidate record.

        :param candidate: The ``PlayStationTitleCandidate`` record.
        :param trophy_title: The ``PlaystationTrophyTitle`` record.
        """
        candidate.trophy_title = trophy_title

        # Add the trophy title name if PlayStation reports a different name.
        if trophy_title.title_name not in candidate.names:
            candidate.names.append(trophy_title.title_name)

        # Add any platforms we have not already recorded.
        for raw_platform in trophy_title.platforms:
            platform = self._map_platform(raw_platform)

            if platform not in candidate.platforms:
                candidate.platforms.append(platform)

        # Add the trophy-set identifier.
        if trophy_title.np_communication_id not in candidate.np_communication_ids:
            candidate.np_communication_ids.append(trophy_title.np_communication_id)

        # np_title_id is optional.
        if (
            trophy_title.np_title_id is not None
            and trophy_title.np_title_id not in candidate.np_title_ids
        ):
            candidate.np_title_ids.append(trophy_title.np_title_id)

        # Remember that this trophy record contributed to the candidate.
        candidate.source_key.append(
            PlayStationSourceKey(
                source_type=IdentifierTypeEnum.TROPHY_TITLE.value,
                source_id=trophy_title.np_communication_id,
            )
        )

    @staticmethod
    def _optional_list(
        value: str | None,
    ) -> list[str]:
        """Convert an optional string value into a list."""
        return [value] if value is not None else []

    @staticmethod
    def _platform_from_category(
        category: str,
    ) -> PlayStationPlatformEnum:
        """Map a played-title category to a PlayStation console."""
        match category:
            case PlayStationTitleCategoryEnum.PS5_NATIVE_GAME:
                return PlayStationPlatformEnum.PS5

            case PlayStationTitleCategoryEnum.PS4_GAME:
                return PlayStationPlatformEnum.PS4

            case _:
                return PlayStationPlatformEnum.UNKNOWN

    @staticmethod
    def _map_platform(
        platform: str | PlayStationPlatformEnum,
    ) -> PlayStationPlatformEnum:
        """Map a trophy platform to a PlayStation console enum."""
        if isinstance(platform, PlayStationPlatformEnum):
            return platform

        match platform.upper():
            case "PSPC":
                return PlayStationPlatformEnum.PSPC
            case "PS5":
                return PlayStationPlatformEnum.PS5

            case "PS4":
                return PlayStationPlatformEnum.PS4

            case "PS3":
                return PlayStationPlatformEnum.PS3

            case _:
                return PlayStationPlatformEnum.UNKNOWN

    def _platforms_overlap(
        self,
        played_title: PlayStationPlayedTitle,
        trophy_title: PlaystationTrophyTitle,
    ) -> bool:
        """
        Return whether two PlayStation records share a platform.

        :param played_title: A ``PlayStationPlayedTitle`` record.
        :param trophy_title: A ``PlaystationTrophyTitle`` record.
        :return: ``True`` if both records share a platform.
        """
        played_platform = self._platform_from_category(played_title.reported_category)

        trophy_platforms = [
            self._map_platform(platform) for platform in trophy_title.platforms
        ]

        return played_platform in trophy_platforms

    @staticmethod
    def _normalise_title(title: str) -> str:
        """Normalise a PlayStation title for comparison."""
        title = title.casefold()

        title = title.replace("™", "")
        title = title.replace("®", "")

        return " ".join(title.split())
