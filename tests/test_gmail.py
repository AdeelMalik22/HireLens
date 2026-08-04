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


def test_gmail_walk_parts_preserves_attachment_metadata():
    part = {"filename": "cv.pdf", "mimeType": "application/pdf", "body": {"attachmentId": "attachment-1"}}
    result = list(gmail._walk_parts([part]))
    assert result == [part]


def test_gmail_walk_parts_flattens_multiple_nested_levels():
    parts = [{"parts": [{"parts": [{"filename": "deep.pdf", "body": {"attachmentId": "deep-1"}}]}]}]
    result = list(gmail._walk_parts(parts))
    assert result[0]["body"]["attachmentId"] == "deep-1"


def test_gmail_walk_parts_returns_parts_without_nested_children():
    part = {"filename": "resume.docx", "body": {"attachmentId": "doc-1"}, "parts": []}
    assert list(gmail._walk_parts([part])) == [part]


def test_gmail_client_decrypts_encrypted_token(monkeypatch):
    from cryptography.fernet import Fernet
    from app.models.email_account import EmailAccount

    key = Fernet.generate_key().decode()
    monkeypatch.setattr(gmail.get_settings(), "token_encryption_key", key)
    token_json = '{"token":"token","refresh_token":"refresh","token_uri":"https://oauth2.googleapis.com/token","client_id":"client","client_secret":"secret","scopes":[]}'
    account = EmailAccount(token_data=gmail.encrypt_secret(token_json), email_address="candidate@example.com", provider="gmail")
    monkeypatch.setattr(gmail, "build", lambda *args, **kwargs: "gmail-client")

    assert gmail._gmail_client(account) == "gmail-client"


def test_gmail_authorization_state_contains_verifier(monkeypatch):
    import json
    from urllib.parse import parse_qs, urlparse

    settings = gmail.get_settings()
    monkeypatch.setattr(settings, "google_client_id", "client-id.apps.googleusercontent.com")
    monkeypatch.setattr(settings, "google_client_secret", "client-secret")
    url = gmail.authorization_url()
    state = parse_qs(urlparse(url).query)["state"][0]
    payload = json.loads(gmail._signer().unsign(state, max_age=600))

    assert payload["code_verifier"]


def test_gmail_scopes_include_read_only_access():
    assert "https://www.googleapis.com/auth/gmail.readonly" in gmail.GMAIL_SCOPES


def test_gmail_scopes_do_not_request_send_access():
    assert "https://www.googleapis.com/auth/gmail.send" not in gmail.GMAIL_SCOPES


def test_gmail_oauth_state_has_nonce(monkeypatch):
    import json
    from urllib.parse import parse_qs, urlparse
    settings = gmail.get_settings()
    monkeypatch.setattr(settings, "google_client_id", "client-id.apps.googleusercontent.com")
    monkeypatch.setattr(settings, "google_client_secret", "client-secret")
    state = parse_qs(urlparse(gmail.authorization_url()).query)["state"][0]
    payload = json.loads(gmail._signer().unsign(state, max_age=600))
    assert payload["nonce"]


def test_gmail_client_rejects_corrupt_encrypted_token(monkeypatch):
    from app.models.email_account import EmailAccount
    from cryptography.fernet import Fernet
    monkeypatch.setattr(gmail.get_settings(), "token_encryption_key", Fernet.generate_key().decode())
    account = EmailAccount(token_data="gAAAA-corrupt", email_address="candidate@example.com", provider="gmail")
    with pytest.raises(ValueError, match="decrypt"):
        gmail._gmail_client(account)


def test_gmail_scopes_include_openid_identity_scope():
    assert "openid" in gmail.GMAIL_SCOPES


def test_gmail_authorization_url_uses_configured_client(monkeypatch):
    from urllib.parse import parse_qs, urlparse
    settings = gmail.get_settings()
    monkeypatch.setattr(settings, "google_client_id", "configured-client.apps.googleusercontent.com")
    monkeypatch.setattr(settings, "google_client_secret", "configured-secret")
    params = parse_qs(urlparse(gmail.authorization_url()).query)
    assert params["client_id"][0] == "configured-client.apps.googleusercontent.com"


def test_gmail_authorization_url_uses_configured_redirect_uri(monkeypatch):
    from urllib.parse import parse_qs, urlparse
    settings = gmail.get_settings()
    monkeypatch.setattr(settings, "google_client_id", "client-id.apps.googleusercontent.com")
    monkeypatch.setattr(settings, "google_client_secret", "client-secret")
    monkeypatch.setattr(settings, "google_redirect_uri", "http://localhost:9000/gmail/callback")
    params = parse_qs(urlparse(gmail.authorization_url()).query)
    assert params["redirect_uri"][0] == "http://localhost:9000/gmail/callback"


def test_gmail_authorization_url_uses_google_authorization_endpoint(monkeypatch):
    settings = gmail.get_settings()
    monkeypatch.setattr(settings, "google_client_id", "client-id.apps.googleusercontent.com")
    monkeypatch.setattr(settings, "google_client_secret", "client-secret")
    assert gmail.authorization_url().startswith("https://accounts.google.com/o/oauth2/auth?")
