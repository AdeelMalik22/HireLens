from cryptography.fernet import Fernet

from app.services import crypto


def test_secret_encryption_round_trip(monkeypatch):
    monkeypatch.setattr(crypto.get_settings(), "token_encryption_key", Fernet.generate_key().decode())
    encrypted = crypto.encrypt_secret("private-token")
    assert encrypted != "private-token"
    assert crypto.decrypt_secret(encrypted) == "private-token"


def test_secret_decryption_rejects_tampered_token(monkeypatch):
    monkeypatch.setattr(crypto.get_settings(), "token_encryption_key", Fernet.generate_key().decode())
    encrypted = crypto.encrypt_secret("private-token")

    try:
        crypto.decrypt_secret(encrypted[:-2] + "xx")
    except ValueError as error:
        assert "decrypt" in str(error)
    else:
        raise AssertionError("tampered token was accepted")


def test_secret_decryption_rejects_invalid_ciphertext(monkeypatch):
    monkeypatch.setattr(crypto.get_settings(), "token_encryption_key", Fernet.generate_key().decode())

    try:
        crypto.decrypt_secret("not-a-fernet-token")
    except ValueError as error:
        assert "decrypt" in str(error)
    else:
        raise AssertionError("invalid ciphertext was accepted")


def test_secret_encryption_requires_configured_key(monkeypatch):
    monkeypatch.setattr(crypto.get_settings(), "token_encryption_key", None)

    try:
        crypto.encrypt_secret("private-token")
    except ValueError as error:
        assert "TOKEN_ENCRYPTION_KEY" in str(error)
    else:
        raise AssertionError("encryption worked without a key")
