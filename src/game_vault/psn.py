# src/game_vault/psn.py

import os

from dotenv import load_dotenv
from psnawp_api import PSNAWP


def create_psn_client():
    load_dotenv()

    npsso = os.environ["PSN_NPSSO"]

    psnawp = PSNAWP(npsso)

    return psnawp.me()
