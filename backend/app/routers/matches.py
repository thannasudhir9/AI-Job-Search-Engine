from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import func, or_
from sqlalchemy.orm import Session

from ..db import get_db
from ..models import Application, Job, Match
from ..schemas import JobOut
from ..services.matching import recompute_matches
from ..utils import (
    COUNTRY_RULES,
    ROLE_RULES,
    content_flags,
    country_of,
    currency_for_country,
    role_family,
)

router = APIRouter()


def _country_condition(country: str):
    keys = [k for ks, c in COUNTRY_RULES if c.lower() == country.lower() for k in ks]
    return or_(*[Job.location.ilike(f"%{k}%") for k in keys]) if keys else None


def _role_condition(role: str):
    by_key = dict(ROLE_RULES)
    words = by_key.get(role.lower())
    if not words:
        return None
    return or_(*[func.lower(Job.title).like(f"%{w}%") for w in words])


@router.get("/matches", response_model=list[JobOut])
def get_matches(
    q: str = "",
    limit: int = Query(200, le=500),
    offset: int = 0,
    min_score: float = 0.0,
    country: str = "",
    role: str = "",
    company: str = "",
    min_salary: int = 0,
    sort: str = Query("score", description="score | newest | salary"),
    db: Session = Depends(get_db),
):
    """Score-ordered matches. All filtering happens in SQL; max `limit` rows leave the DB."""
    query = (
        db.query(Job, Match)
        .join(Match, Match.job_id == Job.id)
        .filter(Match.dismissed.is_(False), Match.score >= min_score)
    )

    ql = q.lower().strip()
    if ql:
        like = f"%{ql}%"
        query = query.filter(or_(Job.title.ilike(like), Job.company_name.ilike(like)))
    cond = _country_condition(country) if country else None
    if cond is not None:
        query = query.filter(cond)
    cond = _role_condition(role) if role else None
    if cond is not None:
        query = query.filter(cond)
    if company.strip():
        query = query.filter(func.lower(Job.company_name) == company.strip().lower())
    if min_salary:
        query = query.filter(
            func.coalesce(Job.salary_max, Job.salary_min, 0) >= min_salary
        )

    if sort == "newest":
        query = query.order_by(Job.posted_at.desc().nullslast(), Job.created_at.desc())
    elif sort == "salary":
        query = query.order_by(
            func.coalesce(Job.salary_max, Job.salary_min, 0).desc(),
            Match.score.desc(),
        )
    else:
        query = query.order_by(Match.score.desc(), Job.created_at.desc())

    rows = query.offset(offset).limit(limit).all()

    # single lookup instead of one query per row (was the page-load bottleneck)
    applied_ids = {jid for (jid,) in db.query(Application.job_id).all()}

    out = []
    for job, m in rows:
        ctry = country_of(job.location)
        scam, work_auth = content_flags(job.title, job.description)
        out.append(
            JobOut(
                id=job.id,
                company_name=job.company_name,
                source=job.source,
                title=job.title,
                location=job.location,
                url=job.url,
                posted_at=job.posted_at,
                created_at=job.created_at,
                score=m.score,
                reasons=m.reasons or [],
                applied=job.id in applied_ids,
                country=ctry,
                role_family=role_family(job.title),
                salary_min=job.salary_min,
                salary_max=job.salary_max,
                salary_currency=job.salary_currency or currency_for_country(ctry),
                scam_flags=scam,
                work_auth_flags=work_auth,
            )
        )
    return out


@router.get("/matches/facets")
def facets(db: Session = Depends(get_db)):
    rows = db.query(Job.location, Job.company_name).join(Match, Match.job_id == Job.id).filter(Match.dismissed.is_(False)).all()
    countries = sorted({c for loc, _ in rows if (c := country_of(loc))})
    companies = sorted({name for _, name in rows})
    return {"countries": countries, "companies": companies}


@router.post("/matches/{job_id}/dismiss")
def dismiss(job_id: int, db: Session = Depends(get_db)):
    m = db.query(Match).filter(Match.job_id == job_id).first()
    if not m:
        return {"ok": False}
    m.dismissed = True
    db.commit()
    return {"ok": True}


@router.post("/matches/recompute")
def recompute(db: Session = Depends(get_db)):
    n = recompute_matches(db)
    return {"scored": n}
