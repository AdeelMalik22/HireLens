from types import SimpleNamespace

from app.services.scoring import score_candidate


def test_score_matches_job_requirements():
    job = SimpleNamespace(required_skills=["Python", "FastAPI"], preferred_skills=["Docker"], minimum_years_experience=2)
    score, breakdown = score_candidate(job, {"skills": ["Python", "FastAPI", "Docker"], "years_of_experience": 2})
    assert score == 100
    assert breakdown["missing_required"] == []


def test_score_reports_missing_required_skill():
    job = SimpleNamespace(required_skills=["Python", "FastAPI"], preferred_skills=[], minimum_years_experience=0)
    _, breakdown = score_candidate(job, {"skills": ["Python"], "years_of_experience": 0})
    assert breakdown["missing_required"] == ["FastAPI"]


def test_score_full_match_returns_100():
    job = SimpleNamespace(required_skills=["Python"], preferred_skills=["Docker"], minimum_years_experience=3)
    score, _ = score_candidate(job, {"skills": ["Python", "Docker"], "years_of_experience": 3})
    assert score == 100


def test_score_missing_required_skill_reduces_score():
    job = SimpleNamespace(required_skills=["Python", "FastAPI"], preferred_skills=[], minimum_years_experience=0)
    score, breakdown = score_candidate(job, {"skills": ["Python"], "years_of_experience": 0})
    assert score == 75
    assert breakdown["missing_required"] == ["FastAPI"]


def test_score_no_preferred_skills_awards_preferred_component():
    job = SimpleNamespace(required_skills=["Python"], preferred_skills=[], minimum_years_experience=0)
    score, breakdown = score_candidate(job, {"skills": ["Python"], "years_of_experience": 0})
    assert score == 100
    assert breakdown["preferred"] == 20


def test_score_experience_is_capped_at_maximum():
    job = SimpleNamespace(required_skills=[], preferred_skills=[], minimum_years_experience=2)
    score, breakdown = score_candidate(job, {"skills": [], "years_of_experience": 10})
    assert score == 100
    assert breakdown["experience"] == 30
