from app.services.auth import authenticate
from app.core.config import get_settings


def test_development_login_is_disabled_by_default(monkeypatch):
    monkeypatch.setattr(get_settings(), "enable_dev_login", False)
    assert authenticate("admin@hirelens.local", "change-me-before-production") is False
