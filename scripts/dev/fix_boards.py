import sys

import httpx

sys.stdout.reconfigure(encoding="utf-8", errors="replace")
BASE = "http://localhost:8000/api"

# dead slugs -> remove; moved companies -> re-add on correct source
REMOVE = ["Palantir Technologies", "Personio"]
FIX = {
    "OpenAI": ("ashby", "openai"),
    "Snowflake": ("ashby", "snowflake"),
    "DeepL": ("ashby", "deepl"),
}
ADD = [
    ("Adyen", "greenhouse", "adyen"),              # Amsterdam
    ("Scandit", "greenhouse", "scandit"),          # Zurich
    ("GetYourGuide", "greenhouse", "getyourguide"),  # Zurich/Berlin
    ("Careem", "greenhouse", "careem"),            # Dubai
    ("SumUp", "greenhouse", "sumup"),              # Berlin/London
    ("Linear", "ashby", "linear"),
    ("Cognition AI", "ashby", "cognition"),        # Devin makers, FDE roles
]

with httpx.Client(timeout=30) as c:
    for comp in c.get(f"{BASE}/companies").json():
        if comp["name"] in REMOVE:
            c.delete(f"{BASE}/companies/{comp['id']}")
            print("removed:", comp["name"])
        elif comp["name"] in FIX:
            src, slug = FIX[comp["name"]]
            c.delete(f"{BASE}/companies/{comp['id']}")
            r = c.post(f"{BASE}/companies", json={"name": comp["name"], "source": src, "slug": slug})
            print("moved:", comp["name"], "->", f"{src}/{slug}", r.status_code)

    for name, source, slug in ADD:
        r = c.post(f"{BASE}/companies", json={"name": name, "source": source, "slug": slug})
        print("added:" if r.status_code == 200 else "skip:", name, r.status_code)

    boards = {b["source"]: 0 for b in []}
    comps = c.get(f"{BASE}/companies").json()
    print("\nWATCHLIST:")
    for comp in comps:
        print(f"  {comp['source']:10} {comp['slug']:16} {comp['name']}")

    print("\nSYNCING...", flush=True)
    r = c.post(f"{BASE}/sync?wait=true", timeout=900)
    data = r.json()
    print(f"SYNC OK: {data['companies_synced']} boards | fetched={data['jobs_fetched']} new={data['jobs_new']}")
    for e in data["errors"]:
        print("  ERR:", e[:150])
