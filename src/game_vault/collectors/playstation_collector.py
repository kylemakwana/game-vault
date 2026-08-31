"""Collect and cache raw data from the PlayStation Network API."""

import json
import time
from datetime import datetime, timedelta
from enum import Enum
from pathlib import Path

from psnawp_api.models.client import Client


class PlayStationCollector:
    """Collect PlayStation account data and serialize it as JSON."""

    def __init__(
        self,
        client: Client,
        raw_dir: Path = Path("data/playstation/raw"),
    ) -> None:
        """Initialize the collector and create its cache directories.

        :param client: Authenticated PlayStation Network account client.
        :param raw_dir: Directory in which raw API responses are cached.
        """
        self.client = client
        self.raw_dir = raw_dir
        self.trophy_dir = self.raw_dir / "trophies"

        self.raw_dir.mkdir(parents=True, exist_ok=True)
        self.trophy_dir.mkdir(parents=True, exist_ok=True)

    @staticmethod
    def _write_json(path: Path, data: dict | list) -> None:
        """Serialize data to an indented UTF-8 JSON file.

        :param path: Destination file path.
        :param data: JSON-compatible dictionary or list to serialize.
        :raises OSError: If the destination cannot be written.
        """
        path.write_text(
            json.dumps(data, indent=2),
            encoding="utf-8",
        )

    def to_jsonable(self, value):
        """Recursively convert API values into JSON-compatible values.

        Datetimes become ISO 8601 strings, timedeltas become whole seconds, enums
        become their values, and objects are represented by their attributes.

        :param value: Value returned by the PlayStation API.
        :return: JSON-compatible representation of ``value``.
        """
        if isinstance(value, datetime):
            return value.isoformat()

        if isinstance(value, timedelta):
            return int(value.total_seconds())

        if isinstance(value, Enum):
            return value.value

        if isinstance(value, frozenset):
            return [self.to_jsonable(item) for item in value]

        if isinstance(value, list):
            return [self.to_jsonable(item) for item in value]

        if isinstance(value, tuple):
            return [self.to_jsonable(item) for item in value]

        if isinstance(value, dict):
            return {key: self.to_jsonable(item) for key, item in value.items()}

        if hasattr(value, "__dict__"):
            return {key: self.to_jsonable(item) for key, item in vars(value).items()}

        return value

    def collect_profile(self) -> None:
        """Collect and cache the legacy account profile."""
        profile = self.client.get_profile_legacy()

        self._write_json(
            self.raw_dir / "profile.json",
            profile,
        )

    def collect_devices(self) -> None:
        """Collect and cache devices associated with the account."""
        devices = self.client.get_account_devices()

        self._write_json(
            self.raw_dir / "devices.json",
            devices,
        )

    def collect_played_titles(self) -> None:
        """Collect and cache the account's played-title history."""
        titles = list(self.client.title_stats())

        self._write_json(
            self.raw_dir / "played_titles.json",
            self.to_jsonable(titles),
        )

    def collect_trophy_titles(self) -> list:
        """Collect and cache the account's trophy-title summaries.

        :return: Trophy-title objects returned by the PlayStation API.
        """
        titles = list(self.client.trophy_titles())

        self._write_json(
            self.raw_dir / "trophy_titles.json",
            self.to_jsonable(titles),
        )

        return titles

    def collect_trophies_for_title(
        self,
        trophy_title,
        force: bool = False,
    ) -> None:
        """Collect and cache detailed trophies for one title.

        :param trophy_title: API trophy-title object to collect.
        :param force: Whether to replace an existing cached response.
        """
        output_path = self.trophy_dir / f"{trophy_title.np_communication_id}.json"

        if output_path.exists() and not force:
            print(f"Skipping {trophy_title.title_name} - already cached")
            return

        platform = next(iter(trophy_title.title_platform))

        trophies = list(
            self.client.trophies(
                np_communication_id=trophy_title.np_communication_id,
                platform=platform,
                include_progress=True,
                trophy_group_id="all",
            )
        )

        self._write_json(
            output_path,
            self.to_jsonable(trophies),
        )

    def collect_all_trophies(
        self,
        trophy_titles: list,
        force: bool = False,
    ) -> None:
        """Collect detailed trophies for a sequence of titles.

        Individual title failures are reported and do not stop the remaining
        collection.

        :param trophy_titles: API trophy-title objects to collect.
        :param force: Whether to replace existing cached responses.
        """
        total = len(trophy_titles)

        for index, trophy_title in enumerate(
            trophy_titles,
            start=1,
        ):
            print(f"[{index}/{total}] {trophy_title.title_name}")

            try:
                self.collect_trophies_for_title(
                    trophy_title,
                    force=force,
                )
            except Exception as exc:
                print(f"Failed to collect {trophy_title.title_name}: {exc}")
                continue

            time.sleep(0.5)

    def collect_all(self) -> None:
        """Collect and cache every supported PlayStation account dataset."""
        print("Collecting profile... [1/5]")
        self.collect_profile()
        print("Profile collected\n")

        print("Collecting devices... [2/5]")
        self.collect_devices()
        print("Devices collected\n")

        print("Collecting played titles... [3/5]")
        self.collect_played_titles()
        print("Played titles collected\n")

        print("Collecting trophy titles... [4/5]")
        trophy_titles = self.collect_trophy_titles()
        print("Trophy titles collected\n")

        print("Collecting trophy details... [5/5]")
        self.collect_all_trophies(trophy_titles)
        print("Trophy details collected\n")
        print("All information collected\n")
