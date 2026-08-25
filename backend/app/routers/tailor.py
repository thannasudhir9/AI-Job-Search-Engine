from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import FileResponse
from sqlalchemy.orm import Session

from ..config import GENERATED_DIR
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


@router.post("/cover/{job_id}", response_model=dict)
def cover_letter(job_id: int, db: Session = Depends(get_db)):
    """career-ops style cover letter - LLM written when available, template fallback."""
    job, master, profile = _get_context(db, job_id)

    from ..services.llm import chat

    prompt_user = f"""Write a concise (max 250 words) cover letter for the role below.

JOB TITLE: {job.title}
COMPANY: {job.company_name}
JOB DESCRIPTION (first 3000 chars):
{job.description[:3000]}

CANDIDATE MASTER RESUME:
{master.text[:5000]}

Rules: professional, specific to this posting, mirror key requirements truthfully
using only facts from the resume. Plain text. Include a placeholder-free greeting
"Dear Hiring Team," and sign off with the candidate's name."""
    content = chat(
        "You are an expert cover letter writer. Be truthful to the source resume; never invent facts.",
        prompt_user,
        temperature=0.5,
    )
    model_name = "ollama"
    if not content:
        skills = ", ".join((profile.skills or [])[:8])
        content = (
            f"Dear Hiring Team,\n\nI am applying for the {job.title} role at {job.company_name}. "
            f"With over 10 years of enterprise delivery experience across Europe, my background "
            f"maps closely to your requirements.\n\nRelevant strengths: {skills}.\n\n"
            f"{(profile.summary or '').strip()}\n\n"
            f"I would welcome the chance to discuss how I can contribute to your team.\n\n"
            f"Best regards,\n{profile.full_name or 'Candidate'}"
        )
        model_name = "fallback"

    pdf_path = str(GENERATED_DIR / f"cover_job_{job_id}.pdf")
    text_to_pdf(content, pdf_path)
    return {"job_id": job_id, "content": content, "model": model_name,
            "pdf_url": f"/api/cover/{job_id}/pdf"}


@router.get("/cover/{job_id}/pdf")
def cover_pdf(job_id: int):
    path = GENERATED_DIR / f"cover_job_{job_id}.pdf"
    if not path.exists():
        raise HTTPException(404, "Generate the cover letter first.")
    return FileResponse(str(path), media_type="application/pdf",
                        filename=f"cover_letter_job_{job_id}.pdf")


@router.post("/outreach/{job_id}", response_model=dict)
def outreach_email(job_id: int, db: Session = Depends(get_db)):
    """Draft a recruiter-outreach application email (draft-only; nothing is sent)."""
    job, master, profile = _get_context(db, job_id)

    from ..services.llm import chat

    prompt_user = f"""Draft a short recruiter-outreach email (<160 words) applying for:

JOB TITLE: {job.title}
COMPANY: {job.company_name}

KEY REQUIREMENTS (from posting): {job.description[:1200]}

CANDIDATE: {profile.full_name}, based in {profile.location}.
HIGHLIGHTS: {(profile.summary or '')[:600]} Top skills: {', '.join((profile.skills or [])[:10])}.

Return format:
SUBJECT: <one line>
BODY:
<email body>"""
    out = chat(
        "You write crisp, respectful job-application emails grounded in the candidate's real experience.",
        prompt_user, temperature=0.5,
    )
    if out and "SUBJECT:" in out:
        subject = out.split("SUBJECT:", 1)[1].split("BODY:", 1)[0].strip()
        body = out.split("BODY:", 1)[1].strip() if "BODY:" in out else ""
        return {"job_id": job_id, "subject": subject, "body": body, "model": "ollama"}

    subject = f"Application: {job.title} — {profile.full_name}"
    body = (
        f"Dear Hiring Team,\n\nI'd like to apply for the {job.title} position at "
        f"{job.company_name}. I bring 10+ years of enterprise platform delivery across "
        f"Europe - currently Senior Technical Consultant work centred on Revenue Cloud, "
        f"Agentforce and complex integrations - and I believe this maps directly to your "
        f"requirements.\n\nHighlights: {', '.join((profile.skills or [])[:8])}.\n\n"
        f"My tailored CV is attached. I am available for a conversation at your convenience "
        f"and can be reached at {profile.email}.\n\nBest regards,\n{profile.full_name}\n"
        f"{profile.phone}"
    )
    return {"job_id": job_id, "subject": subject, "body": body, "model": "fallback"}


def _payload(v: ResumeVariant, job_id: int) -> dict:
    return {"job_id": job_id, "content": v.content, "model": v.model,
            "pdf_url": f"/api/tailor/{job_id}/pdf"}
