import pytest

from app.services import gmail


def test_gmail_authorization_requires_oauth_credentials(monkeypatch):
    settings = gmail.get_settings()
    monkeypatch.setattr(settings, "google_client_id", None)
    monkeypatch.setattr(settings, "google_client_secret", None)

    with pytest.raises(gmail.GmailConfigurationError, match="credentials"):
        gmail.authorization_url()
