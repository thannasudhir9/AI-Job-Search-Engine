import sys

import httpx

sys.stdout.reconfigure(encoding="utf-8", errors="replace")
BASE = "http://localhost:8000/api"

FDE_WORDS = [
    "forward deployed", "deployment strategist", "solutions engineer",
    "solution engineer", "solutions architect", "solution architect",
    "customer engineer", "customer success architect", "implementation",
    "technical consultant", "field engineer", "professional services",
    "solution consultant", "technical architect", "fde",
]
REGIONS = [
    "germany", "berlin", "munich", "frankfurt", "hesse",
    "netherlands", "amsterdam", "the hague",
    "switzerland", "zurich", "geneva", "baar",
    "dubai", "abu dhabi", "united arab emirates", "uae",
    "emea", "europe",
]

matches = httpx.get(f"{BASE}/matches?limit=10000", timeout=120).json()
print(f"total scored jobs in DB: {len(matches)}")

region_hits = []
for m in matches:
    loc = m["location"].lower()
    if any(r in loc for r in REGIONS):
        region_hits.append(m)
print(f"in DE/NL/CH/UAE regions: {len(region_hits)}")

fde = []
for m in region_hits:
    title = m["title"].lower()
    if any(w in title for w in FDE_WORDS):
        fde.append(m)
fde.sort(key=lambda x: x["score"] or 0, reverse=True)

print(f"FDE-relevant titles in target regions: {len(fde)}\n")
for i, m in enumerate(fde[:25], 1):
    print(f"{i:2}. [{m['score']:5.1f}] {m['title']}")
    print(f"      {m['company_name']} - {m['location']}")
