# psn.py
from psnawp_api import PSNAWP

from game_vault.config import PSN_NPSSO

psnawp = PSNAWP(PSN_NPSSO)
user = psnawp.me()
