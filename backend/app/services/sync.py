"""Orchestrate a sync: fetch all enabled company boards, upsert jobs, rescore matches."""
import httpx
from sqlalchemy.orm import Session

from ..models import Company, Job
from ..utils import extract_salary
from .boards import FETCHERS
from .matching import recompute_matches


def _upsert_jobs(db: Session, company: Company, fetched: list[dict]) -> tuple[int, int]:
    new = 0
    for item in fetched:
        if not item.get("title") or not item.get("ext_id"):
            continue
        existing = (
            db.query(Job)
            .filter(Job.source == company.source, Job.ext_id == str(item["ext_id"]))
            .first()
        )
        if existing:
            continue
        description = item.get("description") or ""
        rx_min, rx_max, rx_cur = extract_salary(f"{item['title']}\n{description}")
        sal_min = item.get("salary_min") or rx_min
        sal_max = item.get("salary_max") or rx_max
        sal_cur = item.get("salary_currency") or (rx_cur if (sal_min or sal_max) else None)
        db.add(
            Job(
                company_id=company.id,
                company_name=(item.get("_company_override") or company.name)[:200],
                source=company.source,
                ext_id=str(item["ext_id"]),
                title=item["title"][:300],
                location=(item.get("location") or "")[:300],
                url=item.get("url") or "",
                description=description,
                salary_min=sal_min,
                salary_max=sal_max,
                salary_currency=sal_cur,
                posted_at=item.get("posted_at"),
            )
        )
        new += 1
    return len(fetched), new


def sync_all(db: Session) -> dict:
    companies = db.query(Company).filter(Company.enabled.is_(True)).all()
    errors: list[str] = []
    fetched_total = 0
    new_total = 0

    with httpx.Client(follow_redirects=True) as client:
        for company in companies:
            fetcher = FETCHERS.get(company.source)
            if fetcher is None:
                errors.append(f"{company.name}: unknown source '{company.source}'")
                continue
            try:
                jobs = fetcher(client, company.slug)
                fetched, new = _upsert_jobs(db, company, jobs)
                fetched_total += fetched
                new_total += new
                from datetime import datetime

                company.last_synced_at = datetime.utcnow()
                db.commit()
            except Exception as e:
                db.rollback()
                msg = f"{company.name} ({company.source}/{company.slug}): {type(e).__name__}: {e}"
                errors.append(msg)

    matches_updated = recompute_matches(db)
    return {
        "companies_synced": len(companies) - len(errors),
        "jobs_fetched": fetched_total,
        "jobs_new": new_total,
        "matches_scored": matches_updated,
        "errors": errors,
    }
