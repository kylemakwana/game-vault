import importlib
import sys
from types import ModuleType
from unittest.mock import Mock


def test_create_psn_client_returns_authenticated_user(monkeypatch):
    config = ModuleType("config")
    config.PSN_NPSSO = "test-token"
    monkeypatch.setitem(sys.modules, "config", config)
    sys.modules.pop("game_vault.playstation_client", None)

    playstation_client = importlib.import_module("game_vault.playstation_client")
    authenticated_user = Mock()
    psnawp = Mock()
    psnawp.me.return_value = authenticated_user
    psnawp_class = Mock(return_value=psnawp)
    load_dotenv = Mock()
    monkeypatch.setattr(playstation_client, "PSNAWP", psnawp_class)
    monkeypatch.setattr(playstation_client, "load_dotenv", load_dotenv)

    result = playstation_client.create_psn_client()

    assert result is authenticated_user
    load_dotenv.assert_called_once_with()
    psnawp_class.assert_called_once_with("test-token")
    psnawp.me.assert_called_once_with()
