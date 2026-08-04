import pytest

from app.services import gmail


def test_gmail_authorization_requires_oauth_credentials(monkeypatch):
    settings = gmail.get_settings()
    monkeypatch.setattr(settings, "google_client_id", None)
    monkeypatch.setattr(settings, "google_client_secret", None)

    with pytest.raises(gmail.GmailConfigurationError, match="credentials"):
        gmail.authorization_url()


def test_gmail_authorization_url_contains_pkce_challenge(monkeypatch):
    settings = gmail.get_settings()
    monkeypatch.setattr(settings, "google_client_id", "client-id.apps.googleusercontent.com")
    monkeypatch.setattr(settings, "google_client_secret", "client-secret")

    url = gmail.authorization_url()

    assert "code_challenge=" in url
    assert "state=" in url


def test_gmail_callback_rejects_invalid_signed_state():
    class FakeDB:
        def rollback(self):
            return None

    with pytest.raises(gmail.GmailConfigurationError, match="Invalid or expired"):
        gmail.complete_authorization(FakeDB(), "fake-code", "invalid-state")


def test_gmail_walk_parts_returns_leaf_attachments():
    parts = [{"filename": "resume.pdf", "body": {"attachmentId": "a1"}}, {"parts": [{"filename": "resume.docx", "body": {"attachmentId": "a2"}}]}]

    result = list(gmail._walk_parts(parts))

    assert [part["filename"] for part in result] == ["resume.pdf", "resume.docx"]
