import httpx
import pytest

from app.services import openrouter


@pytest.mark.asyncio
async def test_openrouter_parses_structured_response(monkeypatch):
    class FakeResponse:
        def raise_for_status(self):
            return None

        def json(self):
            return {"choices": [{"message": {"content": '{"skills":["Python"]}'}}]}

    class FakeClient:
        async def __aenter__(self):
            return self

        async def __aexit__(self, *args):
            return None

        async def post(self, *args, **kwargs):
            return FakeResponse()

    monkeypatch.setattr(openrouter.httpx, "AsyncClient", lambda **kwargs: FakeClient())
    monkeypatch.setattr(openrouter.get_settings(), "openrouter_api_key", "test-key")
    result = await openrouter.extract_resume_data("Python developer")
    assert result["skills"] == ["Python"]


@pytest.mark.asyncio
async def test_openrouter_requires_api_key(monkeypatch):
    monkeypatch.setattr(openrouter.get_settings(), "openrouter_api_key", None)

    with pytest.raises(openrouter.AIExtractionError, match="API key"):
        await openrouter.extract_resume_data("resume text")


@pytest.mark.asyncio
async def test_openrouter_rejects_malformed_json(monkeypatch):
    class FakeResponse:
        def raise_for_status(self):
            return None

        def json(self):
            return {"choices": [{"message": {"content": "not-json"}}]}

    class FakeClient:
        async def __aenter__(self): return self
        async def __aexit__(self, *args): return None
        async def post(self, *args, **kwargs): return FakeResponse()

    monkeypatch.setattr(openrouter.httpx, "AsyncClient", lambda **kwargs: FakeClient())
    monkeypatch.setattr(openrouter.get_settings(), "openrouter_api_key", "test-key")
    with pytest.raises(openrouter.AIExtractionError):
        await openrouter.extract_resume_data("resume text")


@pytest.mark.asyncio
async def test_openrouter_raises_retryable_error_on_rate_limit(monkeypatch):
    class FakeResponse:
        status_code = 429
        def raise_for_status(self):
            raise AssertionError("rate-limit responses should be handled first")

    class FakeClient:
        async def __aenter__(self): return self
        async def __aexit__(self, *args): return None
        async def post(self, *args, **kwargs): return FakeResponse()

    monkeypatch.setattr(openrouter.httpx, "AsyncClient", lambda **kwargs: FakeClient())
    monkeypatch.setattr(openrouter.get_settings(), "openrouter_api_key", "test-key")
    with pytest.raises(openrouter.RetryableAIError):
        await openrouter.extract_resume_data("resume text")
