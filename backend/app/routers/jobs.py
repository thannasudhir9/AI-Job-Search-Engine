from datetime import datetime

from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException
from sqlalchemy.orm import Session

from ..db import SessionLocal, get_db
from ..models import Company
from ..schemas import CompanyCreate, SyncResult

router = APIRouter()


@router.post("/companies", response_model=dict)
def add_company(payload: CompanyCreate, db: Session = Depends(get_db)):
    if payload.source not in ("greenhouse", "lever", "ashby", "salesforce", "linkedin"):
        raise HTTPException(400, "source must be greenhouse | lever | ashby | salesforce | linkedin")
    exists = (
        db.query(Company)
        .filter(Company.source == payload.source, Company.slug == payload.slug)
        .first()
    )
    if exists:
        raise HTTPException(409, f"{payload.source}/{payload.slug} already added.")
    c = Company(name=payload.name, source=payload.source, slug=payload.slug.strip().lower())
    db.add(c)
    db.commit()
    return {"id": c.id, "name": c.name}


@router.delete("/companies/{company_id}")
def delete_company(company_id: int, db: Session = Depends(get_db)):
    c = db.get(Company, company_id)
    if not c:
        raise HTTPException(404, "Company not found.")
    db.delete(c)
    db.commit()
    return {"ok": True}


@router.get("/companies", response_model=list[dict])
def list_companies(db: Session = Depends(get_db)):
    from ..models import Job

    return [
        {
            "id": c.id,
            "name": c.name,
            "source": c.source,
            "slug": c.slug,
            "enabled": c.enabled,
            "priority": c.priority,
            "last_synced_at": c.last_synced_at.isoformat() if c.last_synced_at else None,
            "job_count": db.query(Job).filter(Job.company_id == c.id).count(),
        }
        for c in db.query(Company).order_by(Company.priority.desc(), Company.name).all()
    ]


@router.get("/jobs/{job_id}", response_model=dict)
def get_job(job_id: int, db: Session = Depends(get_db)):
    """Single job summary - used by the tailor page instead of loading the whole match list."""
    job = db.get(Job, job_id)
    if not job:
        raise HTTPException(404, "Job not found.")
    return {
        "id": job.id,
        "title": job.title,
        "company_name": job.company_name,
        "location": job.location,
        "url": job.url,
        "description_chars": len(job.description),
        "salary_min": job.salary_min,
        "salary_max": job.salary_max,
        "posted_at": job.posted_at.isoformat() if job.posted_at else None,
    }


def _sync_task():
    from ..services.sync import sync_all

    db = SessionLocal()
    try:
        sync_all(db)
    finally:
        db.close()


@router.post("/sync", response_model=SyncResult)
def sync_now(background: BackgroundTasks, wait: bool = False, db: Session = Depends(get_db)):
    """Trigger a board sync. wait=true runs it inline and returns stats."""
    if wait:
        from ..services.sync import sync_all

        result = sync_all(db)
        return SyncResult(
            companies_synced=result["companies_synced"],
            jobs_fetched=result["jobs_fetched"],
            jobs_new=result["jobs_new"],
            errors=result["errors"],
        )
    background.add_task(_sync_task)
    now = datetime.utcnow().isoformat()
    return SyncResult(companies_synced=0, jobs_fetched=0, jobs_new=0,
                      errors=[f"Sync started in background at {now}"])
