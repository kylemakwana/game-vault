from unittest.mock import Mock

import pytest

from game_vault import playstation_client


def test_create_psn_client_returns_authenticated_user(monkeypatch):
    monkeypatch.setenv("PSN_NPSSO", "test-token")
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


def test_create_psn_client_loads_token_from_dotenv(monkeypatch):
    monkeypatch.delenv("PSN_NPSSO", raising=False)
    monkeypatch.setattr(
        playstation_client,
        "load_dotenv",
        lambda: monkeypatch.setenv("PSN_NPSSO", "dotenv-token"),
    )
    psnawp_class = Mock()
    monkeypatch.setattr(playstation_client, "PSNAWP", psnawp_class)

    playstation_client.create_psn_client()

    psnawp_class.assert_called_once_with("dotenv-token")


def test_create_psn_client_requires_token(monkeypatch):
    monkeypatch.delenv("PSN_NPSSO", raising=False)
    monkeypatch.setattr(playstation_client, "load_dotenv", Mock())
    psnawp_class = Mock()
    monkeypatch.setattr(playstation_client, "PSNAWP", psnawp_class)

    with pytest.raises(KeyError, match="PSN_NPSSO"):
        playstation_client.create_psn_client()

    psnawp_class.assert_not_called()
