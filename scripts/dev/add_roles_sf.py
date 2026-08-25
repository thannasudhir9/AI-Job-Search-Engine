import sys

import httpx

sys.stdout.reconfigure(encoding="utf-8", errors="replace")
BASE = "http://localhost:8000/api"

DESIRED = [
    "Forward Deployed Engineer",
    "Senior Forward Deployed Engineer",
    "Technical Architect",
    "Senior Technical Architect",
    "Project Manager",
    "Senior Project Manager",
    "Solutions Engineer",
    "Solutions Architect",
    "Customer Engineer",
    "Implementation Consultant",
    "Technical Consultant",
    "Solution Consultant",
]

with httpx.Client(timeout=700) as c:
    # 1) add Salesforce Careers as high-priority source
    r = c.post(f"{BASE}/companies", json={"name": "Salesforce Careers", "source": "salesforce", "slug": "prod"})
    print("company salesforce:", r.status_code, "" if r.status_code == 200 else r.text[:100])

    # 2) update desired titles (PUT triggers a full re-score)
    prof = c.get(f"{BASE}/profile").json()
    prof["desired_titles"] = DESIRED
    r = c.put(f"{BASE}/profile", json=prof)
    print("profile titles updated:", r.status_code)

    # 3) full sync incl. Salesforce board (re-scores at the end too)
    print("SYNCING...", flush=True)
    r = c.post(f"{BASE}/sync?wait=true", timeout=900)
    data = r.json()
    print(f"SYNC OK: {data['companies_synced']} boards | fetched={data['jobs_fetched']} new={data['jobs_new']}")
    for e in data["errors"]:
        print("  ERR:", e[:150])

    st = c.get(f"{BASE}/status", timeout=60).json()
    print("TOTAL JOBS NOW:", st["jobs"], "| matches:", st["matches"])
