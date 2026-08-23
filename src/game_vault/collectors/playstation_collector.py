import json
import time
from datetime import datetime, timedelta
from enum import Enum
from pathlib import Path

from psnawp_api.models.client import Client


class PlayStationCollector:
    def __init__(
        self,
        client: Client,
        raw_dir: Path = Path("data/playstation/raw"),
    ) -> None:
        self.client = client
        self.raw_dir = raw_dir
        self.trophy_dir = self.raw_dir / "trophies"

        self.raw_dir.mkdir(parents=True, exist_ok=True)
        self.trophy_dir.mkdir(parents=True, exist_ok=True)

    @staticmethod
    def _write_json(path: Path, data: dict | list) -> None:
        path.write_text(
            json.dumps(data, indent=2),
            encoding="utf-8",
        )

    def to_jsonable(self, value):
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
        profile = self.client.get_profile_legacy()

        self._write_json(
            self.raw_dir / "profile.json",
            profile,
        )

    def collect_devices(self) -> None:
        devices = self.client.get_account_devices()

        self._write_json(
            self.raw_dir / "devices.json",
            devices,
        )

    def collect_played_titles(self) -> None:
        titles = list(self.client.title_stats())

        self._write_json(
            self.raw_dir / "played_titles.json",
            self.to_jsonable(titles),
        )

    def collect_trophy_titles(self) -> list:
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
