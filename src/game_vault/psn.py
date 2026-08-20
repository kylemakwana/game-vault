from pathlib import Path

from dotenv import load_dotenv

from game_vault.services.playstation_snapshot_builder import PlayStationSnapshotBuilder

load_dotenv()

builder = PlayStationSnapshotBuilder()
snapshot = builder.build()

output_path = Path("data/playstation/snapshot-2.json")
output_path.parent.mkdir(parents=True, exist_ok=True)
#
output_path.write_text(
    snapshot.model_dump_json(indent=4),
    encoding="utf-8",
)

print(f"Snapshot written to {output_path}")
