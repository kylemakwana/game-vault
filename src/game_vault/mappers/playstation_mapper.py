from dataclasses import dataclass, field

from game_vault.models.achievement import (
    Achievement,
    AchievementGroup,
    AchievementProgress,
    AchievementSet,
)
from game_vault.models.activity import PlayActivity
from game_vault.models.game import (
    Game,
    GameRelease,
)
from game_vault.models.mapping import SourceGameMapping
from game_vault.models.platform import PlatformAccount
from game_vault.models.playstation import PlayStationSnapshot
from game_vault.models.series import GameSeries, GameSeriesMembership


@dataclass
class PlaystationMappedData:
    games: list[Game]
    releases: list[GameRelease] = field(default_factory=list)

    series: list[GameSeries] = field(default_factory=list)
    series_membership: list[GameSeriesMembership] = field(default_factory=list)

    activities: list[PlayActivity] = field(default_factory=list)

    achievement_sets: list[AchievementSet] = field(default_factory=list)
    achievement_groups: list[AchievementGroup] = field(default_factory=list)
    achievements: list[Achievement] = field(default_factory=list)
    achievement_progress: list[AchievementProgress] = field(default_factory=list)

    mappings: list[SourceGameMapping] = field(default_factory=list)
    account: PlatformAccount | None = None


class PlaystationMapper:
    SERVICE_ID = "playstation_network"

    def __init__(
        self,
        snapshot: PlayStationSnapshot,
        mappings: list[SourceGameMapping],
        releases: list[GameRelease],
        games: list[Game],
        series: list[GameSeries],
        series_memberships: list[GameSeriesMembership],
    ):
        self.snapshot = snapshot
        self.mappings = mappings
        self.releases: dict[str, GameRelease] = {
            release.id: release for release in releases
        }
        self.games: dict[str, Game] = {game.id: game for game in games}
        self.series: dict[str, GameSeries] = {serie.id: serie for serie in series}
        self.series_memberships = series_memberships

    def _find_release_mapping(
        self,
        source_id: str,
        source: str,
    ) -> SourceGameMapping | None:
        return next(
            (
                mapping
                for mapping in self.mappings
                if mapping.source_id == source_id and mapping.source == source
            ),
            None,
        )

    def _mapped_releases(self) -> list[GameRelease]:
        release_ids = {mapping.game_release_id for mapping in self.mappings}

        return [
            release
            for release_id, release in self.releases.items()
            if release_id in release_ids
        ]

    def _mapped_games(self) -> list[Game]:
        game_ids = {release.game_id for release in self._mapped_releases()}

        return [game for game_id, game in self.games.items() if game_id in game_ids]

    def _mapped_series_memberships(
        self,
        games: list[Game],
    ) -> list[GameSeriesMembership]:
        game_ids = {game.id for game in games}

        return [
            membership
            for membership in self.series_memberships
            if membership.game_id in game_ids
        ]

    def _mapped_series(
        self,
        memberships: list[GameSeriesMembership],
    ) -> list[GameSeries]:
        series_ids = {membership.series_id for membership in memberships}

        return [
            series
            for series_id, series in self.series.items()
            if series_id in series_ids
        ]

    def _map_account(self) -> PlatformAccount:
        account = self.snapshot.account

        return PlatformAccount(
            id=f"psn:{account.account_id}",
            service_id=self.SERVICE_ID,
            username=account.online_id,
            external_account_id=account.account_id,
            avatar_url=account.avatar_url,
        )

    def _map_played_titles(
        self,
        account: PlatformAccount,
    ) -> list[PlayActivity]:
        activities: list[PlayActivity] = []

        for title in self.snapshot.played_titles:
            if title.content_type != "game":
                continue

            mapping = self._find_release_mapping(
                source_id=title.title_id,
                source="playstation_title",
            )

            if mapping is None:
                continue

            release = self.releases.get(mapping.game_release_id)

            if release is None:
                continue

            activities.append(
                PlayActivity(
                    id=f"psn-activity:{title.title_id}",
                    account_id=account.id,
                    game_release_id=release.id,
                    playtime_seconds=title.play_duration_seconds,
                    first_played_at=title.first_played_at,
                    last_played_at=title.last_played_at,
                    source=self.SERVICE_ID,
                )
            )

        return activities

    @staticmethod
    def _platform_from_category(category: str) -> str:
        match category:
            case "ps5_native_game":
                return "ps5"
            case "ps4_game":
                return "ps4"
            case _:
                return "playstation_unknown"

    def _map_trophy_title(
        self,
        trophy_title,
        account: PlatformAccount,
    ) -> (
        tuple[
            AchievementSet,
            list[AchievementGroup],
            list[Achievement],
            list[AchievementProgress],
        ]
        | None
    ):
        mapping = self._find_release_mapping(
            source_id=trophy_title.np_communication_id,
            source="playstation_trophy_set",
        )

        if mapping is None:
            return None

        achievement_set_id = f"psn-trophy-set:{trophy_title.np_communication_id}"

        achievement_set = AchievementSet(
            id=achievement_set_id,
            game_release_id=mapping.game_release_id,
            service_id=self.SERVICE_ID,
            name=trophy_title.title_name,
            external_identifier=trophy_title.np_communication_id,
        )

        groups: list[AchievementGroup] = []
        achievements: list[Achievement] = []
        progress_records: list[AchievementProgress] = []

        for trophy_group in trophy_title.groups:
            group_id = f"{achievement_set_id}:{trophy_group.group_id}"

            group = AchievementGroup(
                id=group_id,
                achievement_set_id=achievement_set_id,
                external_group_id=trophy_group.group_id,
                name=trophy_group.name,
            )

            groups.append(group)

            for trophy in trophy_group.trophies:
                achievement_id = f"{achievement_set_id}:{trophy.trophy_id}"
                achievement = Achievement(
                    id=achievement_id,
                    achievement_set_id=achievement_set_id,
                    group_id=group_id,
                    external_id=str(trophy.trophy_id),
                    name=trophy.name,
                    description=trophy.detail,
                    icon_url=trophy.icon_url,
                    hidden=trophy.hidden,
                    achievement_type=trophy.type,
                    rarity=trophy.rarity,
                    global_unlock_percentage=trophy.earn_rate,
                    progress_target=trophy.progress_target_value,
                )

                achievements.append(achievement)

                user_progress = trophy.user_progress

                progress = AchievementProgress(
                    achievemnt_id=achievement_id,
                    account_id=account.id,
                    unlocked=user_progress.earned,
                    unlocked_at=user_progress.earned_at,
                    progress=user_progress.progress,
                    progress_percentage=user_progress.progress_rate,
                    progresssed_at=user_progress.progressed_at,
                )

                progress_records.append(progress)

        return achievement_set, groups, achievements, progress_records

    def _map_trophy_titles(
        self,
        account: PlatformAccount,
    ) -> tuple[
        list[AchievementSet],
        list[AchievementGroup],
        list[Achievement],
        list[AchievementProgress],
    ]:
        sets = []
        groups = []
        achievements = []
        progress_records = []

        for trophy_title in self.snapshot.trophy_titles:
            mapped = self._map_trophy_title(trophy_title, account)

            if mapped is None:
                continue

            (
                achievement_set,
                mapped_groups,
                mapped_achievements,
                mapped_progress,
            ) = mapped

            sets.append(achievement_set)
            groups.extend(mapped_groups)
            achievements.extend(mapped_achievements)
            progress_records.extend(mapped_progress)

        return (
            sets,
            groups,
            achievements,
            progress_records,
        )

    def map(self) -> PlaystationMappedData:
        account = self._map_account()

        releases = self._mapped_releases()
        games = self._mapped_games()
        series_memberships = self._mapped_series_memberships(games)
        series = self._mapped_series(series_memberships)

        activities = self._map_played_titles(account)

        (achievement_sets, achievement_groups, achievements, achievement_progress) = (
            self._map_trophy_titles(account)
        )

        return PlaystationMappedData(
            account=account,
            games=games,
            releases=releases,
            series=series,
            series_membership=series_memberships,
            activities=activities,
            achievement_sets=achievement_sets,
            achievement_groups=achievement_groups,
            achievements=achievements,
            achievement_progress=achievement_progress,
            mappings=self.mappings,
        )
