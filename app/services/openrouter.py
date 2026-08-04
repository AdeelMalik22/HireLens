import json

import httpx

from app.core.config import get_settings
from app.services.exceptions import RetryableAIError, ServiceError


class AIExtractionError(ServiceError):
    pass


async def extract_resume_data(text: str) -> dict:
    settings = get_settings()
    if not settings.openrouter_api_key:
        raise AIExtractionError("OpenRouter API key is not configured")
    prompt = """Extract resume data as strict JSON with these keys: candidate_name, candidate_email, skills (array of strings), years_of_experience (number), work_experience (array), education (array), certifications (array), projects (array), technologies (array), summary. Do not invent facts. Resume text:\n""" + text[:30000]
    body = {"model": settings.openrouter_model, "messages": [{"role": "user", "content": prompt}], "response_format": {"type": "json_object"}}
    try:
        async with httpx.AsyncClient(timeout=settings.openrouter_timeout_seconds) as client:
            response = await client.post(f"{settings.openrouter_base_url}/chat/completions", headers={"Authorization": f"Bearer {settings.openrouter_api_key}", "Content-Type": "application/json"}, json=body)
            if response.status_code == 429 or response.status_code >= 500:
                raise RetryableAIError(f"OpenRouter temporarily unavailable ({response.status_code})")
            response.raise_for_status()
            content = response.json()["choices"][0]["message"]["content"]
            return json.loads(content)
    except RetryableAIError:
        raise
    except Exception as error:
        raise AIExtractionError("Unable to extract resume data with OpenRouter") from error
