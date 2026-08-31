"""Load environment-backed configuration for Game Vault."""

import os

from dotenv import load_dotenv

load_dotenv()

PSN_NPSSO = os.environ["PSN_NPSSO"]
