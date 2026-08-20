import os

from dotenv import load_dotenv
from psnawp_api import PSNAWP

from game_vault.collectors.playstation_collector import (
    PlayStationCollector,
)

load_dotenv()

psnawp = PSNAWP(os.environ["PSN_NPSSO"])
client = psnawp.me()

playstation_collector = PlayStationCollector(client)
playstation_collector.collect_all()

# builder = PlayStationSnapshotBuilder(psnawp)
#
# snapshot = builder.build()
#
# output_path = Path("data/playstation/snapshot.json")
# output_path.parent.mkdir(parents=True, exist_ok=True)
#
# output_path.write_text(
#     snapshot.model_dump_json(indent=4),
#     encoding="utf-8",
# )
#
# print(f"Snapshot written to {output_path}")
