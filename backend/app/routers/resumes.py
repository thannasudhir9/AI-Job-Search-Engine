import shutil
from datetime import datetime
from pathlib import Path

from fastapi import APIRouter, Depends, HTTPException, UploadFile
from sqlalchemy.orm import Session

from ..config import UPLOAD_DIR
from ..db import get_db
from ..models import Resume

router = APIRouter()


def _parse_pdf(path: Path) -> str:
    from pypdf import PdfReader

    reader = PdfReader(str(path))
    return "\n".join((page.extract_text() or "") for page in reader.pages).strip()


@router.post("/resumes/upload", response_model=dict)
async def upload_resume(file: UploadFile, db: Session = Depends(get_db)):
    suffix = Path(file.filename or "resume").suffix.lower()
    if suffix not in (".pdf", ".txt", ".md"):
        raise HTTPException(400, "Only .pdf, .txt, .md files are supported.")

    stamp = datetime.utcnow().strftime("%Y%m%d%H%M%S")
    safe_name = f"{stamp}_{Path(file.filename).name}"
    dest = UPLOAD_DIR / safe_name
    with open(dest, "wb") as fh:
        shutil.copyfileobj(file.file, fh)

    if suffix == ".pdf":
        try:
            text = _parse_pdf(dest)
        except Exception as e:
            dest.unlink(missing_ok=True)
            raise HTTPException(400, f"Could not read PDF: {e}")
    else:
        text = dest.read_text(errors="replace")

    if len(text.strip()) < 50:
        dest.unlink(missing_ok=True)
        raise HTTPException(400, "Extracted text is too short - is this a valid resume file?")

    has_master = db.query(Resume).filter(Resume.is_master.is_(True)).first() is not None
    resume = Resume(name=file.filename or safe_name, path=str(dest), text=text,
                    is_master=not has_master)
    db.add(resume)
    db.commit()
    return {"id": resume.id, "name": resume.name, "is_master": resume.is_master,
            "text_chars": len(text)}


@router.get("/resumes", response_model=list[dict])
def list_resumes(db: Session = Depends(get_db)):
    rows = db.query(Resume).order_by(Resume.created_at.desc()).all()
    return [
        {"id": r.id, "name": r.name, "is_master": r.is_master,
         "text_chars": len(r.text), "created_at": r.created_at.isoformat()}
        for r in rows
    ]


@router.get("/resumes/master")
def get_master_text(db: Session = Depends(get_db)):
    r = db.query(Resume).filter(Resume.is_master.is_(True)).first()
    if not r:
        raise HTTPException(404, "No master resume uploaded yet.")
    return {"id": r.id, "name": r.name, "text": r.text}


@router.post("/resumes/{resume_id}/set-master")
def set_master(resume_id: int, db: Session = Depends(get_db)):
    target = db.get(Resume, resume_id)
    if not target:
        raise HTTPException(404, "Resume not found.")
    for r in db.query(Resume).all():
        r.is_master = r.id == resume_id
    db.commit()
    return {"ok": True}


@router.delete("/resumes/{resume_id}")
def delete_resume(resume_id: int, db: Session = Depends(get_db)):
    r = db.get(Resume, resume_id)
    if not r:
        raise HTTPException(404, "Resume not found.")
    if r.path and Path(r.path).exists():
        Path(r.path).unlink(missing_ok=True)
    db.delete(r)
    db.commit()
    return {"ok": True}
