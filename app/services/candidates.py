from sqlalchemy.orm import Session

from app.models.resume import Resume
from app.services.exceptions import NotFoundError


def get_candidate(db: Session, candidate_id: int, user_id: int) -> Resume:
    candidate = db.get(Resume, candidate_id)
    if candidate is None or candidate.user_id != user_id:
        raise NotFoundError("Candidate not found")
    return candidate


def update_review_status(db: Session, candidate_id: int, user_id: int, review_status: str) -> Resume:
    if review_status not in {"pending", "shortlisted", "rejected"}:
        raise ValueError("Invalid review status")
    candidate = get_candidate(db, candidate_id, user_id)
    candidate.review_status = review_status
    db.commit()
    db.refresh(candidate)
    return candidate
