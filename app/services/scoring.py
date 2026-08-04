import re


def _normalize(value: str) -> str:
    return re.sub(r"[^a-z0-9+#.]", "", value.lower())


def score_candidate(job, extracted: dict) -> tuple[float, dict]:
    candidate_skills = {_normalize(skill) for skill in extracted.get("skills", [])}
    required = [skill for skill in job.required_skills if _normalize(skill)]
    preferred = [skill for skill in job.preferred_skills if _normalize(skill)]
    matched_required = [skill for skill in required if _normalize(skill) in candidate_skills]
    matched_preferred = [skill for skill in preferred if _normalize(skill) in candidate_skills]
    years = float(extracted.get("years_of_experience") or 0)
    required_score = len(matched_required) / len(required) * 50 if required else 50
    experience_score = (min(years / job.minimum_years_experience, 1) * 30) if job.minimum_years_experience else 30
    preferred_score = len(matched_preferred) / len(preferred) * 20 if preferred else 20
    total = round(required_score + experience_score + preferred_score, 2)
    return total, {"required": round(required_score, 2), "experience": round(experience_score, 2), "preferred": round(preferred_score, 2), "matched_required": matched_required, "missing_required": [skill for skill in required if skill not in matched_required], "matched_preferred": matched_preferred}
