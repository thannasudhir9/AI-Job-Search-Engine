from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from ..db import get_db
from ..models import Profile
from ..schemas import ProfileOut, ProfileUpdate
from ..services.matching import recompute_matches

router = APIRouter()


def _ensure_profile(db: Session) -> Profile:
    p = db.get(Profile, 1)
    if p is None:
        p = Profile(id=1)
        db.add(p)
        db.commit()
        db.refresh(p)
    return p


@router.get("/profile", response_model=ProfileOut)
def get_profile(db: Session = Depends(get_db)):
    p = _ensure_profile(db)
    return ProfileOut(**{c.name: getattr(p, c.name) for c in Profile.__table__.columns})


@router.put("/profile", response_model=ProfileOut)
def update_profile(payload: ProfileUpdate, db: Session = Depends(get_db)):
    p = _ensure_profile(db)
    for field, value in payload.model_dump().items():
        setattr(p, field, value)
    db.commit()
    db.refresh(p)
    recompute_matches(db)  # preferences changed -> rescore everything
    return ProfileOut(**{c.name: getattr(p, c.name) for c in Profile.__table__.columns})


def ensure_profile_dep(db: Session = Depends(get_db)) -> Profile:
    p = _ensure_profile(db)
    if not (p.skills or p.desired_titles or p.summary):
        raise HTTPException(status_code=428, detail="Complete your profile first.")
    return p
