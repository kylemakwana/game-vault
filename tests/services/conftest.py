import json
from copy import deepcopy

import pytest

from game_vault.services.playstation_snapshot_builder import (
    PlayStationSnapshotBuilder,
)


@pytest.fixture
def snapshot_profile(
    mock_profile,
    mock_trophy_titles,
):
    profile = deepcopy(mock_profile)

    profile["profile"]["trophySummary"]["earnedTrophies"] = deepcopy(
        mock_trophy_titles[0]["earned_trophies"]
    )

    return profile


@pytest.fixture
def raw_dir(
    tmp_path,
    snapshot_profile,
    mock_devices,
    mock_played_titles,
    mock_trophy_titles,
    mock_collected_trophies,
):
    raw_dir = tmp_path / "raw"
    trophy_dir = raw_dir / "trophies"

    trophy_dir.mkdir(parents=True)

    (raw_dir / "profile.json").write_text(
        json.dumps(snapshot_profile),
        encoding="utf-8",
    )

    (raw_dir / "devices.json").write_text(
        json.dumps(mock_devices),
        encoding="utf-8",
    )

    (raw_dir / "played_titles.json").write_text(
        json.dumps(mock_played_titles),
        encoding="utf-8",
    )

    (raw_dir / "trophy_titles.json").write_text(
        json.dumps(mock_trophy_titles),
        encoding="utf-8",
    )

    communication_id = mock_trophy_titles[0]["np_communication_id"]

    (trophy_dir / f"{communication_id}.json").write_text(
        json.dumps(mock_collected_trophies),
        encoding="utf-8",
    )

    return raw_dir


@pytest.fixture
def snapshot_builder(raw_dir):
    return PlayStationSnapshotBuilder(raw_dir=raw_dir)
