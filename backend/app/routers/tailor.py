from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import FileResponse
from sqlalchemy.orm import Session

from ..db import get_db
from ..models import Job, Profile, Resume, ResumeVariant
from ..services.llm import tailor_fallback, tailor_with_llm
from ..services.pdfgen import pdf_path_for_job, text_to_pdf

router = APIRouter()


def _get_context(db: Session, job_id: int) -> tuple[Job, Resume, Profile]:
    job = db.get(Job, job_id)
    if not job:
        raise HTTPException(404, "Job not found.")
    master = db.query(Resume).filter(Resume.is_master.is_(True)).first()
    if not master:
        raise HTTPException(428, "Upload a master resume first (Profile page).")
    profile = db.get(Profile, 1)
    if profile is None:
        raise HTTPException(428, "Complete your profile first.")
    return job, master, profile


@router.get("/tailor/list", response_model=list[dict])
def list_variants(db: Session = Depends(get_db)):
    """All tailored resumes (newest first) - powers the resume library in the UI."""
    from ..models import ResumeVariant as RV  # noqa: F401  (already imported above)

    rows = (
        db.query(ResumeVariant, Job)
        .join(Job, Job.id == ResumeVariant.job_id)
        .order_by(ResumeVariant.created_at.desc())
        .limit(300)
        .all()
    )
    return [
        {
            "job_id": v.job_id,
            "title": j.title,
            "company_name": j.company_name,
            "location": j.location,
            "model": v.model,
            "pdf_url": f"/api/tailor/{v.job_id}/pdf",
            "created_at": v.created_at.isoformat(),
        }
        for v, j in rows
    ]


@router.post("/tailor/{job_id}", response_model=dict)
def tailor(job_id: int, force: bool = False, db: Session = Depends(get_db)):
    job, master, profile = _get_context(db, job_id)

    existing = db.query(ResumeVariant).filter(ResumeVariant.job_id == job_id).first()
    if existing and not force:
        return _payload(existing, job_id)

    content = tailor_with_llm(master.text, job.title, job.company_name, job.description)
    model_name = "ollama"
    if not content:
        content = tailor_fallback(
            master.text, job.title, job.company_name, job.description, profile.skills or []
        )
        model_name = "keyword-fallback"

    pdf_path = pdf_path_for_job(job_id)
    text_to_pdf(content, pdf_path)

    if existing is None:
        existing = ResumeVariant(job_id=job_id)
        db.add(existing)
    existing.content = content
    existing.pdf_path = pdf_path
    existing.model = model_name
    db.commit()
    return _payload(existing, job_id)


@router.get("/tailor/{job_id}", response_model=dict)
def get_variant(job_id: int, db: Session = Depends(get_db)):
    existing = db.query(ResumeVariant).filter(ResumeVariant.job_id == job_id).first()
    if not existing:
        raise HTTPException(404, "No tailored resume for this job yet. Generate one.")
    return _payload(existing, job_id)


@router.get("/tailor/{job_id}/pdf")
def download_pdf(job_id: int, db: Session = Depends(get_db)):
    existing = db.query(ResumeVariant).filter(ResumeVariant.job_id == job_id).first()
    if not existing or not existing.pdf_path:
        raise HTTPException(404, "Generate the resume first.")
    return FileResponse(existing.pdf_path, media_type="application/pdf",
                        filename=f"resume_job_{job_id}.pdf")


def _payload(v: ResumeVariant, job_id: int) -> dict:
    return {"job_id": job_id, "content": v.content, "model": v.model,
            "pdf_url": f"/api/tailor/{job_id}/pdf"}
