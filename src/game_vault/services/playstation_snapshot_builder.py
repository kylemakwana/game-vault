"""Build and validate normalized PlayStation snapshots from cached JSON."""

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
    PlaystationTrophyGroup,
    PlaystationTrophyTitle,
    SnapshotMetadata,
    Trophy,
    TrophyCounts,
    TrophySummary,
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

TROPHY_RARITY_MAP = {
    0: "ultra_rare",
    1: "very_rare",
    2: "rare",
    3: "common",
}


class PlayStationSnapshotBuilder:
    """Transform cached PlayStation API responses into domain models."""

    def __init__(self, raw_dir: Path = Path("data/playstation/raw")):
        """Initialize the snapshot builder.

        :param raw_dir: Directory containing cached PlayStation JSON responses.
        """
        self.raw_dir = raw_dir
        self.trophy_dir = raw_dir / "trophies"

    @staticmethod
    def _read_json(path: Path):
        """Read and decode a UTF-8 JSON file.

        :param path: JSON file to read.
        :return: Decoded JSON value.
        :raises OSError: If the file cannot be read.
        :raises json.JSONDecodeError: If the file contains invalid JSON.
        """
        return json.loads(path.read_text(encoding="utf-8"))

    def build(self) -> PlayStationSnapshot:
        """Build a normalized snapshot from all cached PlayStation data.

        :return: Complete normalized PlayStation snapshot.
        """
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
            trophy_titles=built_trophy_titles,
            validation=validation,
        )

    def validate(self) -> ValidationResult:
        """Validate cached trophy data without building a complete snapshot.

        :return: Trophy import completeness and consistency results.
        """
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
        """Build an account model from a legacy profile response.

        :param legacy_profile: Legacy PlayStation profile response.
        :return: Normalized PlayStation account.
        """
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
        """Build a trophy summary from a profile response.

        :param profile: Legacy PlayStation profile response.
        :return: Normalized trophy summary.
        """
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
        """Group device activation records into normalized devices.

        :param devices: Raw device activation records.
        :return: Normalized PlayStation devices.
        """
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
        """Classify a played title as a game or application.

        :param title: Raw played-title record.
        :return: Content type and the classification method used.
        """
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
        """Build normalized played-title records.

        :param played_titles: Raw played-title records.
        :return: Normalized played titles.
        """
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

    def _build_trophy_titles(
        self, trophy_titles: list[dict]
    ) -> list[PlaystationTrophyTitle]:
        """Build trophy-title models and attach cached trophy details.

        :param trophy_titles: Raw trophy-title summary records.
        :return: Normalized trophy titles.
        """
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
                PlaystationTrophyTitle(
                    np_communication_id=communication_id,
                    np_service_name=title["np_service_name"],
                    np_title_id=title["np_title_id"],
                    trophy_set_version=title["trophy_set_version"],
                    title_name=title["title_name"],
                    title_detail=title["title_detail"],
                    title_icon_url=title["title_icon_url"],
                    platforms=[platform for platform in title["title_platform"]],
                    has_trophy_groups=bool(title.get("has_trophy_groups")),
                    hidden=bool(title.get("hidden_flag")),
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
        """Convert PlayStation trophy counts into a normalized model.

        :param psn_counts: Mapping of trophy types to counts.
        :return: Normalized trophy counts.
        """
        return TrophyCounts(
            bronze=psn_counts["bronze"],
            silver=psn_counts["silver"],
            gold=psn_counts["gold"],
            platinum=psn_counts["platinum"],
        )

    def _build_trophy_groups(
        self,
        trophies: list[dict],
    ) -> list[PlaystationTrophyGroup]:
        """Group raw trophy records by their PlayStation group identifier.

        :param trophies: Raw trophy-detail records.
        :return: Normalized trophy groups.
        """
        grouped: dict[str, list[dict]] = defaultdict(list)

        for trophy in trophies:
            grouped[trophy["trophy_group_id"]].append(trophy)

        return [
            PlaystationTrophyGroup(
                group_id=group_id,
                trophies=[self._build_trophy(trophy) for trophy in group_trophies],
            )
            for group_id, group_trophies in grouped.items()
        ]

    @staticmethod
    def _build_trophy(trophy: dict) -> Trophy:
        """Build a normalized trophy from a raw detail record.

        :param trophy: Raw trophy-detail record.
        :return: Normalized trophy model.
        """
        earn_rate: str | None = trophy.get("trophy_earn_rate")

        rarity_value: int | None = trophy.get("trophy_rarity")

        rarity = (
            TROPHY_RARITY_MAP.get(rarity_value) if rarity_value is not None else None
        )

        return Trophy(
            trophy_id=trophy["trophy_id"],
            trophy_set_version=trophy["trophy_set_version"],
            name=trophy["trophy_name"],
            detail=trophy.get("trophy_detail"),
            type=trophy["trophy_type"],
            hidden=trophy["trophy_hidden"],
            icon_url=trophy.get("trophy_icon_url"),
            rarity=rarity,
            earn_rate=float(earn_rate) if earn_rate is not None else None,
            progress_target_value=trophy.get("trophy_progress_target_value"),
            reward_name=trophy.get("trophy_reward_name"),
            reward_image_url=trophy.get("trophy_reward_img_url"),
            user_progress=UserTrophyProgress(
                earned=trophy["earned"],
                earned_at=trophy.get("earned_date_time"),
                progress=trophy.get("progress"),
                progress_rate=trophy.get("progress_rate"),
                progressed_at=trophy.get("progressed_date_time"),
            ),
        )

    def _count_cached_trophy_titles(
        self,
        trophy_titles: list[dict],
    ) -> int:
        """Count trophy titles with cached detail files.

        :param trophy_titles: Raw trophy-title summary records.
        :return: Number of titles with cached trophy details.
        """
        return sum(
            1
            for title in trophy_titles
            if (self.trophy_dir / f"{title['np_communication_id']}.json").exists()
        )

    @staticmethod
    def _build_validation(
        trophy_summary: TrophySummary,
        trophy_titles: list[PlaystationTrophyTitle],
        expected_trophy_titles_count: int,
        imported_trophy_detail_sets_count: int,
    ) -> ValidationResult:
        """Build completeness and trophy-total validation results.

        :param trophy_summary: Trophy totals reported by the account profile.
        :param trophy_titles: Imported trophy-title summaries.
        :param expected_trophy_titles_count: Number of expected title summaries.
        :param imported_trophy_detail_sets_count: Number of cached detail sets.
        :return: Snapshot validation result and any warnings.
        """
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
