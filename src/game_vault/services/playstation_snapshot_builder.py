import json
from collections import defaultdict
from datetime import UTC, datetime
from pathlib import Path

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
    def __init__(self, raw_dir: Path = Path("data/playstation/raw")):
        self.raw_dir = raw_dir
        self.trophy_dir = raw_dir / "trophies"

    @staticmethod
    def _read_json(path: Path):
        return json.loads(path.read_text(encoding="utf-8"))

    def build(self) -> PlayStationSnapshot:
        profile = self._read_json(self.raw_dir / "profile.json")
        devices = self._read_json(self.raw_dir / "devices.json")
        played_titles = self._read_json(self.raw_dir / "played_titles.json")
        trophy_titles = self._read_json(self.raw_dir / "trophy_titles.json")
        built_trophy_titles = self._build_trophy_titles(trophy_titles)
        trophy_summary = self._build_trophy_summary(profile)
        imported_trophy_detail_sets_count = self._count_cached_trophy_titles(
            trophy_titles
        )

        validation = self._build_validation(
            trophy_summary=trophy_summary,
            trophy_titles=built_trophy_titles,
            expected_trophy_titles_count=len(trophy_titles),
            imported_trophy_detail_sets_count=imported_trophy_detail_sets_count,
        )

        return PlayStationSnapshot(
            snapshot=SnapshotMetadata(
                generated_at=datetime.now(UTC),
            ),
            account=self._build_account(profile),
            trophy_summary=trophy_summary,
            devices=self._build_devices(devices),
            played_titles=self._build_played_titles(played_titles),
            trophy_titles=self._build_trophy_titles(trophy_titles),
            validation=validation,
        )

    def validate(self) -> ValidationResult:
        profile = self._read_json(self.raw_dir / "profile.json")
        trophy_summary = self._build_trophy_summary(profile)
        trophy_titles = self._read_json(self.raw_dir / "trophy_titles.json")
        built_trophy_titles = self._build_trophy_titles(trophy_titles)
        imported_trophy_detail_sets_count = self._count_cached_trophy_titles(
            trophy_titles
        )

        return self._build_validation(
            trophy_summary=trophy_summary,
            trophy_titles=built_trophy_titles,
            expected_trophy_titles_count=len(trophy_titles),
            imported_trophy_detail_sets_count=imported_trophy_detail_sets_count,
        )


    @staticmethod
    def _build_account(legacy_profile: dict) -> PlayStationAccount:
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

    @staticmethod
    def _build_trophy_summary(
        profile: dict,
    ) -> TrophySummary:
        trophy_summary = profile["profile"]["trophySummary"]
        earned = trophy_summary["earnedTrophies"]

        return TrophySummary(
            level=trophy_summary["level"],
            level_progress=trophy_summary["progress"],
            earned=TrophyCounts(
                bronze=earned["bronze"],
                silver=earned["silver"],
                gold=earned["gold"],
                platinum=earned["platinum"],
            ),
        )

    @staticmethod
    def _build_devices(devices: list[dict]) -> list[PlayStationDevice]:
        grouped_devices: dict[str, list[dict]] = defaultdict(list)

        for device in devices:
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
                    account_device_vector=first.get("accountDeviceVector"),
                    activations=activations,
                )
            )

        return devices

    @staticmethod
    def _classify_title(title) -> tuple[str, str]:
        category = title.get("category", "")
        name = title.get("name", "")

        if category in {
            "ps4_game",
            "ps5_native_game",
        }:
            return "game", "playstation_category"

        if name in NON_GAME_TITLES:
            return "application", "known_application"

        return "game", "unknown_category_assumed_game"

    def _build_played_titles(
        self,
        played_titles: list[dict],
    ) -> list[PlayedTitle]:
        titles = []

        for title in played_titles:
            content_type, classification_source = self._classify_title(title)

            titles.append(
                PlayedTitle(
                    title_id=title["title_id"],
                    name=title["name"],
                    image_url=title["image_url"],
                    reported_category=title["category"],
                    content_type=content_type,
                    classification_source=classification_source,
                    play_count=title["play_count"],
                    play_duration_seconds=int(title["play_duration"]),
                    first_played_at=title["first_played_date_time"],
                    last_played_at=title["last_played_date_time"],
                )
            )

        return titles

    def _build_trophy_titles(self, trophy_titles: list[dict]) -> list[TrophyTitle]:
        result = []

        for title in trophy_titles:
            communication_id = title["np_communication_id"]

            trophy_path = self.trophy_dir / f"{communication_id}.json"

            if trophy_path.exists():
                trophies = self._read_json(trophy_path)
            else:
                trophies = []

            groups = self._build_trophy_groups(trophies)

            result.append(
                TrophyTitle(
                    np_communication_id=communication_id,
                    np_service_name=title["np_service_name"],
                    np_title_id=title["np_title_id"],
                    trophy_set_version=title["trophy_set_version"],
                    title_name=title["title_name"],
                    title_detail=title["title_detail"],
                    title_icon_url=title["title_icon_url"],
                    platforms=[platform for platform in title["title_platform"]],
                    has_trophy_groups=title["has_trophy_groups"],
                    hidden=title["hidden_flag"],
                    progress=title["progress"],
                    earned_trophies=self._convert_trophy_counts(
                        title["earned_trophies"]
                    ),
                    defined_trophies=self._convert_trophy_counts(
                        title["defined_trophies"]
                    ),
                    last_updated_at=title["last_updated_datetime"],
                    groups=groups,
                ),
            )

        return result

    @staticmethod
    def _convert_trophy_counts(psn_counts: dict) -> TrophyCounts:
        return TrophyCounts(
            bronze=psn_counts["bronze"],
            silver=psn_counts["silver"],
            gold=psn_counts["gold"],
            platinum=psn_counts["platinum"],
        )

    def _build_trophy_groups(
        self,
        trophies: list[dict],
    ) -> list[TrophyGroup]:
        grouped: dict[str, list[dict]] = defaultdict(list)

        for trophy in trophies:
            grouped[trophy["trophy_group_id"]].append(trophy)

        return [
            TrophyGroup(
                group_id=group_id,
                trophies=[self._build_trophy(trophy) for trophy in group_trophies],
            )
            for group_id, group_trophies in grouped.items()
        ]

    @staticmethod
    def _build_trophy(trophy: dict) -> Trophy:
        rarity = None

        if trophy["trophy_rarity"] is not None:
            rarity = trophy["trophy_type"].lower()

        earn_rate = None

        if trophy["trophy_earn_rate"] is not None:
            earn_rate = float(trophy["trophy_earn_rate"])

        return Trophy(
            trophy_id=trophy["trophy_id"],
            trophy_set_version=trophy["trophy_set_version"],
            name=trophy["trophy_name"],
            detail=trophy["trophy_detail"],
            type=trophy["trophy_type"].lower(),
            hidden=trophy["trophy_hidden"],
            icon_url=trophy["trophy_icon_url"],
            rarity=rarity,
            earn_rate=earn_rate,
            progress_target_value=trophy["trophy_progress_target_value"],
            reward_name=trophy["trophy_reward_name"],
            reward_image_url=trophy["trophy_reward_img_url"],
            user_progress=UserTrophyProgress(
                earned=trophy["earned"],
                earned_at=trophy["earned_date_time"],
                progress=trophy["progress"],
                progress_rate=trophy["progress_rate"],
                progressed_at=trophy["progressed_date_time"],
            ),
        )

    def _count_cached_trophy_titles(
        self,
        trophy_titles: list[dict],
    ) -> int:
        return sum(
            1
            for title in trophy_titles
            if (self.trophy_dir / f"{title['np_communication_id']}.json").exists()
        )

    @staticmethod
    def _build_validation(
        trophy_summary: TrophySummary,
        trophy_titles: list[TrophyTitle],
        expected_trophy_titles_count: int,
        imported_trophy_detail_sets_count: int,
    ) -> ValidationResult:
        profile_totals = trophy_summary.earned

        imported_totals = TrophyCounts(
            bronze=sum(title.earned_trophies.bronze for title in trophy_titles),
            silver=sum(title.earned_trophies.silver for title in trophy_titles),
            gold=sum(title.earned_trophies.gold for title in trophy_titles),
            platinum=sum(title.earned_trophies.platinum for title in trophy_titles),
        )

        imported_trophy_titles_count = len(trophy_titles)

        trophy_title_summary_complete = (
            imported_trophy_titles_count == expected_trophy_titles_count
        )

        trophy_detail_import_complete = (
            imported_trophy_detail_sets_count == expected_trophy_titles_count
        )

        trophy_totals_match = (
            profile_totals.bronze == imported_totals.bronze
            and profile_totals.silver == imported_totals.silver
            and profile_totals.gold == imported_totals.gold
            and profile_totals.platinum == imported_totals.platinum
        )

        warnings: list[str] = []

        if not trophy_title_summary_complete:
            warnings.append(
                "Trophy title summary import is incomplete; "
                f"{imported_trophy_titles_count} of "
                f"{expected_trophy_titles_count} titles were imported."
            )

        if not trophy_detail_import_complete:
            warnings.append(
                "Detailed trophy import is incomplete; "
                f"{imported_trophy_detail_sets_count} of "
                f"{expected_trophy_titles_count} trophy sets were imported."
            )

        if trophy_title_summary_complete and not trophy_totals_match:
            warnings.append(
                "Imported trophy summary totals do not match "
                "the PlayStation profile totals."
            )

        return ValidationResult(
            trophy_title_summary_complete=trophy_title_summary_complete,
            trophy_detail_import_complete=trophy_detail_import_complete,
            expected_trophy_titles_count=expected_trophy_titles_count,
            imported_trophy_titles_count=imported_trophy_titles_count,
            expected_trophy_detail_sets_count=expected_trophy_titles_count,
            imported_trophy_detail_sets_count=imported_trophy_detail_sets_count,
            profile_trophy_totals=profile_totals,
            imported_trophy_totals=imported_totals,
            trophy_totals_match=trophy_totals_match,
            warnings=warnings,
        )
