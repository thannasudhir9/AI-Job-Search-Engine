import sys

import httpx

sys.stdout.reconfigure(encoding="utf-8", errors="replace")
BASE = "http://localhost:8000/api"

matches = httpx.get(f"{BASE}/matches?limit=10000", timeout=120).json()
FDE = ["forward deployed", "deployment strategist", "solutions engineer",
       "solution engineer", "solutions architect", "solution architect"]
REG = ["germany", "berlin", "munich", "frankfurt", "netherlands", "amsterdam",
       "switzerland", "zurich", "geneva", "dubai", "abu dhabi", "uae", "emea"]

fde = [m for m in matches
       if any(w in m["title"].lower() for w in FDE)
       and any(r in m["location"].lower() for r in REG)]
fde.sort(key=lambda x: x["score"] or 0, reverse=True)

for i, m in enumerate(fde[:3], 1):
    r = httpx.post(f"{BASE}/tailor/{m['id']}", timeout=300).json()
    pdf = httpx.get(f"{BASE}/api/tailor/{m['id']}/pdf" if False else f"{BASE}/tailor/{m['id']}/pdf",
                    timeout=60)
    print(f"{i}. [{m['score']:5.1f}] {m['title']} @ {m['company_name']} ({m['location']})")
    print(f"   job_id={m['id']}  model={r['model']}  pdf={pdf.status_code}")
