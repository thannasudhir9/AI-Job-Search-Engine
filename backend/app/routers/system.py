from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from ..config import BASE_DIR, SYNC_INTERVAL_HOURS
from ..db import get_db
from ..models import Application, Company, Job, Match, Resume
from ..schemas import StatusOut
from ..services.llm import ollama_chat_available

router = APIRouter()


@router.get("/status", response_model=StatusOut)
def status(db: Session = Depends(get_db)):
    ok, models_list = ollama_chat_available()
    return StatusOut(
        jobs=db.query(Job).count(),
        matches=db.query(Match).filter(Match.dismissed.is_(False)).count(),
        applications=db.query(Application).count(),
        resumes=db.query(Resume).count(),
        ollama_available=ok,
        ollama_models=models_list[:10],
        sync_interval_hours=SYNC_INTERVAL_HOURS,
    )


@router.get("/companies", response_model=list[dict])
def list_companies(db: Session = Depends(get_db)):
    return [
        {
            "id": c.id,
            "name": c.name,
            "source": c.source,
            "slug": c.slug,
            "enabled": c.enabled,
            "last_synced_at": c.last_synced_at.isoformat() if c.last_synced_at else None,
            "job_count": db.query(Job).filter(Job.company_id == c.id).count(),
        }
        for c in db.query(Company).order_by(Company.name).all()
    ]


@router.get("/logs")
def logs(lines: int = 120):
    """Tail of the server logs so the Docs tab can show them live."""
    result = []
    for name in ("server.log", "server_err.log"):
        path = BASE_DIR / name
        entry = {"file": name, "exists": path.exists(), "lines": []}
        if path.exists():
            try:
                all_lines = path.read_text(encoding="utf-8", errors="replace").splitlines()
                entry["lines"] = all_lines[-lines:]
                entry["total_lines"] = len(all_lines)
            except Exception as e:
                entry["lines"] = [f"<unreadable: {e}>"]
        result.append(entry)
    return result
