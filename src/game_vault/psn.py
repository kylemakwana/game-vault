import os
from pathlib import Path

from dotenv import load_dotenv
from psnawp_api import PSNAWP

from game_vault.services.playstation_snapshot_builder import (
    PlayStationSnapshotBuilder,
)

load_dotenv()

psnawp = PSNAWP(os.environ["PSN_NPSSO"])

builder = PlayStationSnapshotBuilder(psnawp)

snapshot = builder.build()

output_path = Path("data/playstation/snapshot.json")
output_path.parent.mkdir(parents=True, exist_ok=True)

output_path.write_text(
    snapshot.model_dump_json(indent=4),
    encoding="utf-8",
)

print(f"Snapshot written to {output_path}")
