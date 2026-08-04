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


def test_gmail_client_requires_token_encryption_key(monkeypatch):
    from app.models.email_account import EmailAccount

    monkeypatch.setattr(gmail.get_settings(), "token_encryption_key", None)
    account = EmailAccount(token_data="gAAAA-encrypted-token", email_address="candidate@example.com", provider="gmail")

    with pytest.raises(ValueError, match="TOKEN_ENCRYPTION_KEY"):
        gmail._gmail_client(account)


def test_gmail_client_accepts_legacy_plaintext_token_record(monkeypatch):
    from app.models.email_account import EmailAccount

    class FakeBuild:
        pass

    monkeypatch.setattr(gmail, "build", lambda *args, **kwargs: FakeBuild())
    account = EmailAccount(token_data='{"token":"token","refresh_token":"refresh","token_uri":"https://oauth2.googleapis.com/token","client_id":"client","client_secret":"secret","scopes":[]}', email_address="candidate@example.com", provider="gmail")

    assert isinstance(gmail._gmail_client(account), FakeBuild)


def test_gmail_walk_parts_handles_empty_payload():
    assert list(gmail._walk_parts([])) == []


def test_gmail_authorization_url_requests_offline_access(monkeypatch):
    settings = gmail.get_settings()
    monkeypatch.setattr(settings, "google_client_id", "client-id.apps.googleusercontent.com")
    monkeypatch.setattr(settings, "google_client_secret", "client-secret")
    url = gmail.authorization_url()
    assert "access_type=offline" in url
