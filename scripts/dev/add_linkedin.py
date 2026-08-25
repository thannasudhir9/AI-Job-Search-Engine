import sys

import httpx

sys.stdout.reconfigure(encoding="utf-8", errors="replace")
BASE = "http://localhost:8000/api"

LINKEDIN_SEARCHES = [
    ("LinkedIn · FDE Germany", "forward deployed engineer|Germany"),
    ("LinkedIn · FDE UAE", "forward deployed engineer|United Arab Emirates"),
    ("LinkedIn · Technical Architect NL", "technical architect|Netherlands"),
    ("LinkedIn · Product PM Switzerland", "product project manager|Switzerland"),
]

with httpx.Client(timeout=700) as c:
    # 1) currency backfill for existing jobs (re-extract with currency capture)
    sys.path.insert(0, ".")
    from app.db import SessionLocal
    from app.models import Job
    from app.utils import extract_salary

    db = SessionLocal()
    n = 0
    for job in db.query(Job).filter(Job.salary_min.isnot(None), Job.salary_currency.is_(None)).all():
        _, _, cur = extract_salary(f"{job.title}\n{job.description[:4000]}")
        job.salary_currency = cur or ("CHF" if "zurich" in (job.location or "").lower() else "EUR")
        n += 1
    db.commit()
    db.close()
    print(f"currency backfilled on {n} jobs")

    # 2) register LinkedIn search sources (priority: none)
    for name, slug in LINKEDIN_SEARCHES:
        r = c.post(f"{BASE}/companies", json={"name": name, "source": "linkedin", "slug": slug})
        print("linkedin row:", r.status_code, name)

    # 3) full sync (fetches everything incl. LinkedIn guest API)
    print("SYNCING...", flush=True)
    r = c.post(f"{BASE}/sync?wait=true", timeout=900)
    data = r.json()
    print(f"SYNC OK: {data['companies_synced']} boards ok | fetched={data['jobs_fetched']} new={data['jobs_new']}")
    for e in data["errors"]:
        print("  ERR:", e[:160])

    st = c.get(f"{BASE}/status", timeout=60).json()
    print("TOTAL JOBS:", st["jobs"])

    # 4) sample multi-currency salaries
    sample = httpx.get(f"{BASE}/matches?limit=500", timeout=120).json()
    with_sal = [m for m in sample if m["salary_min"] or m["salary_max"]]
    seen_cur = {}
    for m in with_sal:
        seen_cur.setdefault(m["salary_currency"] or "?", []).append(m)
    print("\nsalary coverage in top 500:", {k: len(v) for k, v in seen_cur.items()})
    for cur, items in seen_cur.items():
        ex = items[0]
        print(f"  {cur}: {ex['title']} @ {ex['company_name']} — {ex['salary_min']}-{ex['salary_max']}")
