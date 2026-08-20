from collections import defaultdict
from datetime import UTC, datetime

from psnawp_api import PSNAWP

from game_vault.models.playstation import (
    DeviceActivation,
    PlayedTitle,
    PlayStationAccount,
    PlayStationDevice,
    PlayStationSnapshot,
    SnapshotMetadata,
    Trophy,
    TrophyCounts,
    TrophyGroup,
    TrophySummary,
    TrophyTitle,
    UserTrophyProgress,
    ValidationResult,
)


NON_GAME_TITLES = {
    "Sky Go",
    "Spotify",
    "Channel 4",
    "Disney+",
    "YouTube",
    "Netflix",
    "Plex",
    "Twitch",
    "BBC iPlayer",
    "Prime Video",
    "Headset Companion",
}

class PlayStationSnapshotBuilder:
    def __init__(self, psnawp: PSNAWP):
        self.psnawp = psnawp
        self.client = psnawp.me()

    def build(self) -> PlayStationSnapshot:
        legacy_profile = self.client.get_profile_legacy()

        account = self._build_account(legacy_profile)
        trophy_summary = self._build_trophy_summary(legacy_profile)

        devices = self._build_devices()
        played_titles = self._build_played_titles()
        trophy_titles = self._build_trophy_titles()

        validation = self._build_validation(
            trophy_summary=trophy_summary,
            trophy_titles=trophy_titles,
        )

        return PlayStationSnapshot(
            snapshot=SnapshotMetadata(
                generated_at=datetime.now(UTC),
            ),
            account=account,
            trophy_summary=trophy_summary,
            devices=devices,
            played_titles=played_titles,
            trophy_titles=trophy_titles,
            validation=validation,
        )

    def _build_account(self, legacy_profile: dict) -> PlayStationAccount:
        profile = legacy_profile["profile"]

        avatar_urls = profile.get("avatarUrls", [])

        avatar_url = None

        if avatar_urls:
            avatar_url = avatar_urls[0].get("avatarUrl")

        return PlayStationAccount(
            online_id=profile["onlineId"],
            account_id=profile["accountId"],
            np_id=profile.get("npId"),
            languages=profile.get("languagesUsed", []),
            avatar_url=avatar_url,
        )

    def _build_trophy_summary(
        self,
        legacy_profile: dict,
    ) -> TrophySummary:
        summary = legacy_profile["profile"]["trophySummary"]
        earned = summary["earnedTrophies"]

        return TrophySummary(
            level=summary["level"],
            level_progress=summary["progress"],
            earned=TrophyCounts(
                bronze=earned["bronze"],
                silver=earned["silver"],
                gold=earned["gold"],
                platinum=earned["platinum"],
            ),
        )

    def _build_devices(self) -> list[PlayStationDevice]:
        raw_devices = self.client.get_account_devices()

        grouped_devices: dict[str, list[dict]] = defaultdict(list)

        for device in raw_devices:
            grouped_devices[device["deviceId"]].append(device)

        devices = []

        for device_id, records in grouped_devices.items():
            first = records[0]

            activations = [
                DeviceActivation(
                    activation_type=record["activationType"],
                    activation_date=datetime.fromisoformat(
                        record["activationDate"].replace("Z", "+00:00")
                    ),
                )
                for record in records
            ]

            devices.append(
                PlayStationDevice(
                    device_id=device_id,
                    device_name=first.get("deviceName"),
                    device_type=first["deviceType"],
                    account_device_vector=first.get(
                        "accountDeviceVector"
                    ),
                    activations=activations,
                )
            )

        return devices

    @staticmethod
    def _classify_title(title) -> tuple[str, str]:
        if title.category.value in {
            "ps4_game",
            "ps5_native_game",
        }:
            return "game", "playstation_category"

        if title.name in NON_GAME_TITLES:
            return "application", "known_application"

        return "game", "unknown_category_assumed_game"

    def _build_played_titles(self) -> list[PlayedTitle]:
        titles = []

        for title in self.client.title_stats():
            content_type, classification_source = (
                self._classify_title(title)
            )

            titles.append(
                PlayedTitle(
                    title_id=title.title_id,
                    name=title.name,
                    image_url=title.image_url,
                    reported_category=title.category.value,
                    content_type=content_type,
                    classification_source=classification_source,
                    play_count=title.play_count,
                    play_duration_seconds=int(
                        title.play_duration.total_seconds()
                    ),
                    first_played_at=title.first_played_date_time,
                    last_played_at=title.last_played_date_time,
                )
            )

        return titles

    def _build_trophy_titles(self) -> list[TrophyTitle]:
        result = []

        for psn_title in list(self.client.trophy_titles())[:3]:
            groups = self._build_trophy_groups(psn_title)

            result.append(
                TrophyTitle(
                    np_communication_id=psn_title.np_communication_id,
                    np_service_name=psn_title.np_service_name,
                    np_title_id=psn_title.np_title_id,
                    trophy_set_version=psn_title.trophy_set_version,
                    title_name=psn_title.title_name,
                    title_detail=psn_title.title_detail,
                    title_icon_url=psn_title.title_icon_url,
                    platforms=[
                        platform.value
                        for platform in psn_title.title_platform
                    ],
                    has_trophy_groups=psn_title.has_trophy_groups,
                    hidden=psn_title.hidden_flag,
                    progress=psn_title.progress,
                    earned_trophies=self._convert_trophy_counts(
                        psn_title.earned_trophies
                    ),
                    defined_trophies=self._convert_trophy_counts(
                        psn_title.defined_trophies
                    ),
                    last_updated_at=(
                        psn_title.last_updated_datetime
                    ),
                    groups=groups,
                )
            )

        return result

    @staticmethod
    def _convert_trophy_counts(psn_counts) -> TrophyCounts:
        return TrophyCounts(
            bronze=psn_counts.bronze,
            silver=psn_counts.silver,
            gold=psn_counts.gold,
            platinum=psn_counts.platinum,
        )

    def _build_trophy_groups(
        self,
        psn_title,
    ) -> list[TrophyGroup]:
        platform = next(iter(psn_title.title_platform))

        trophies = list(
            self.client.trophies(
                np_communication_id=psn_title.np_communication_id,
                platform=platform,
                include_progress=True,
                trophy_group_id="all",
            )
        )

        grouped: dict[str, list] = defaultdict(list)

        for trophy in trophies:
            grouped[trophy.trophy_group_id].append(trophy)

        return [
            TrophyGroup(
                group_id=group_id,
                trophies=[
                    self._build_trophy(trophy)
                    for trophy in group_trophies
                ],
            )
            for group_id, group_trophies in grouped.items()
        ]

    def _build_trophy(self, trophy) -> Trophy:
        rarity = None

        if trophy.trophy_rarity is not None:
            rarity = trophy.trophy_rarity.name.lower()

        earn_rate = None

        if trophy.trophy_earn_rate is not None:
            earn_rate = float(trophy.trophy_earn_rate)

        return Trophy(
            trophy_id=trophy.trophy_id,
            trophy_set_version=trophy.trophy_set_version,
            name=trophy.trophy_name,
            detail=trophy.trophy_detail,
            type=trophy.trophy_type.value,
            hidden=trophy.trophy_hidden,
            icon_url=trophy.trophy_icon_url,
            rarity=rarity,
            earn_rate=earn_rate,
            progress_target_value=(
                trophy.trophy_progress_target_value
            ),
            reward_name=trophy.trophy_reward_name,
            reward_image_url=trophy.trophy_reward_img_url,
            user_progress=UserTrophyProgress(
                earned=trophy.earned,
                earned_at=trophy.earned_date_time,
                progress=trophy.progress,
                progress_rate=trophy.progress_rate,
                progressed_at=trophy.progressed_date_time,
            ),
        )

    def _build_validation(
        self,
        trophy_summary: TrophySummary,
        trophy_titles: list[TrophyTitle],
    ) -> ValidationResult:
        imported = TrophyCounts()

        for title in trophy_titles:
            imported.bronze += title.earned_trophies.bronze
            imported.silver += title.earned_trophies.silver
            imported.gold += title.earned_trophies.gold
            imported.platinum += title.earned_trophies.platinum


        profile = trophy_summary.earned
        is_complete = imported.total == profile.total
        trophy_totals_match: bool = False

        if is_complete:
            trophy_totals_match = (
                profile.bronze == imported.bronze
                and profile.silver == imported.silver
                and profile.gold == imported.gold
                and profile.platinum == imported.platinum
            )

        warnings = []

        if not trophy_totals_match:
            if not is_complete:
                warnings.append(
                    "Trophy import is partial; "
                    "profile totals cannot yet be "
                    "validated"
                )
            else:
                warnings.append(
                    "Imported trophy counts do not match "
                    "PlayStation profile totals."
                )

        return ValidationResult(
            profile_trophy_totals=profile,
            imported_trophy_totals=imported,
            trophy_totals_match=trophy_totals_match,
            warnings=warnings,
        )
