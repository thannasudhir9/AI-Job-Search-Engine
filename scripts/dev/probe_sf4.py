import sys

import httpx

sys.stdout.reconfigure(encoding="utf-8", errors="replace")
h = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 Chrome/126 Safari/537.36",
}

CANDIDATES = [
    # company-target guesses
    "https://api.company-target.com/api/v2/search/jobs?company_id=salesforce&page=1&per_page=5",
    "https://api.company-target.com/api/v2/search/jobs?q=engineer&page=1",
    "https://api.company-target.com/api/v1/search/jobs?page=1",
    # salesforce site guesses
    "https://careers.salesforce.com/api/jobs?start=0&num=5",
    "https://careers.salesforce.com/en/jobs/api?search=",
]

with httpx.Client(timeout=20, follow_redirects=True, headers=h) as c:
    print("== candidate APIs ==")
    for u in CANDIDATES:
        try:
            r = c.get(u)
            body = r.text[:120].replace("\n", " ")
            print(r.status_code, u[:75], "|", body)
        except Exception as e:
            print("ERR", type(e).__name__, u[:60])

    print("\n== robots ==")
    for host in ("https://careers.salesforce.com", "https://api.company-target.com"):
        try:
            r = c.get(f"{host}/robots.txt")
            print(host, r.status_code)
            if r.status_code == 200:
                print(r.text[:600])
        except Exception as e:
            print("ERR", host, type(e).__name__)

    print("\n== sitemap ==")
    try:
        r = c.get("https://careers.salesforce.com/sitemap.xml")
        print(r.status_code, r.text[:400])
    except Exception as e:
        print("ERR", type(e).__name__)
