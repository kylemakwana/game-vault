"""Create authenticated PlayStation Network API clients."""

import os

from dotenv import load_dotenv
from psnawp_api import PSNAWP


def create_psn_client():
    """Create an authenticated client for the configured PlayStation account.

    :return: Authenticated PlayStation account client.
    :raises KeyError: If ``PSN_NPSSO`` is unavailable after loading dotenv.
    """
    load_dotenv()

    psnawp = PSNAWP(os.environ["PSN_NPSSO"])

    return psnawp.me()
