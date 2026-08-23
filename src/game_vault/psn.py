# src/game_vault/psn.py

from config import PSN_NPSSO
from dotenv import load_dotenv
from psnawp_api import PSNAWP


def create_psn_client():
    load_dotenv()

    psnawp = PSNAWP(PSN_NPSSO)

    return psnawp.me()
