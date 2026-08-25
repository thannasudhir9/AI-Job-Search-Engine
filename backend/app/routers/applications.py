from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from ..db import get_db
from ..models import Application, Job, Match, ResumeVariant
from ..schemas import ApplicationCreate, ApplicationOut, ApplicationUpdate

router = APIRouter()

VALID_STATUSES = ("draft", "applied", "interview", "offer", "rejected")


def _out(db: Session, a: Application) -> ApplicationOut:
    job = db.get(Job, a.job_id)
    variant = (
        db.query(ResumeVariant).filter(ResumeVariant.job_id == a.job_id).first()
    )
    return ApplicationOut(
        id=a.id,
        job_id=a.job_id,
        job_title=job.title if job else "",
        company_name=job.company_name if job else "",
        job_url=job.url if job else "",
        status=a.status,
        notes=a.notes or "",
        events=a.events or [],
        updated_at=a.updated_at,
        variant_id=variant.id if variant else None,
        resume_pdf_url=f"/api/tailor/{a.job_id}/pdf" if variant else None,
        resume_model=variant.model if variant else None,
    )


@router.get("/applications", response_model=list[ApplicationOut])
def list_applications(db: Session = Depends(get_db)):
    rows = db.query(Application).order_by(Application.updated_at.desc()).all()
    return [_out(db, a) for a in rows]


@router.post("/applications", response_model=ApplicationOut)
def create_application(payload: ApplicationCreate, db: Session = Depends(get_db)):
    if payload.status not in VALID_STATUSES:
        raise HTTPException(400, f"status must be one of {VALID_STATUSES}")
    job = db.get(Job, payload.job_id)
    if not job:
        raise HTTPException(404, "Job not found.")
    existing = db.query(Application).filter(Application.job_id == payload.job_id).first()
    if existing:
        raise HTTPException(409, "Already tracked.")
    now = datetime.utcnow().isoformat()
    a = Application(
        job_id=payload.job_id,
        variant_id=payload.variant_id,
        status=payload.status,
        events=[{"at": now, "status": payload.status, "note": "Added to tracker"}],
    )
    m = db.query(Match).filter(Match.job_id == payload.job_id).first()
    # keep dismissed matches out of the matches list once tracked
    if m:
        m.dismissed = True
    db.add(a)
    db.commit()
    return _out(db, a)


@router.patch("/applications/{app_id}", response_model=ApplicationOut)
def update_application(app_id: int, payload: ApplicationUpdate, db: Session = Depends(get_db)):
    a = db.get(Application, app_id)
    if not a:
        raise HTTPException(404, "Not found.")
    changed_status = False
    if payload.status is not None:
        if payload.status not in VALID_STATUSES:
            raise HTTPException(400, f"status must be one of {VALID_STATUSES}")
        if payload.status != a.status:
            a.status = payload.status
            changed_status = True
    if payload.notes is not None:
        a.notes = payload.notes
    if payload.variant_id is not None:
        a.variant_id = payload.variant_id
    if changed_status:
        events = list(a.events or [])
        events.append({"at": datetime.utcnow().isoformat(), "status": a.status, "note": ""})
        a.events = events
    db.commit()
    return _out(db, a)


@router.delete("/applications/{app_id}")
def delete_application(app_id: int, db: Session = Depends(get_db)):
    a = db.get(Application, app_id)
    if not a:
        raise HTTPException(404, "Not found.")
    db.delete(a)
    db.commit()
    return {"ok": True}
