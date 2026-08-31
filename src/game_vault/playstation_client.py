"""Create authenticated PlayStation Network API clients."""

from config import PSN_NPSSO
from dotenv import load_dotenv
from psnawp_api import PSNAWP


def create_psn_client():
    """Create an authenticated client for the configured PlayStation account.

    :return: Authenticated PlayStation account client.
    :raises KeyError: If ``PSN_NPSSO`` was unavailable when configuration loaded.
    """
    load_dotenv()

    psnawp = PSNAWP(PSN_NPSSO)

    return psnawp.me()
