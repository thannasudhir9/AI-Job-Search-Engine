import re
import sys

import httpx

sys.stdout.reconfigure(encoding="utf-8", errors="replace")
h = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 Chrome/126 Safari/537.36",
    "Accept": "text/html,application/json",
}

with httpx.Client(timeout=25, follow_redirects=True, headers=h) as c:
    r = c.get("https://careers.salesforce.com/en/jobs/")
    print("status", r.status_code, "len", len(r.text))
    pats = [
        r'"(/[^"]*(?:api|jobs|search|services)[^"]*)"',
        r"(https?://[^\"'\s<>]+(?:api|search)[^\"'\s<>]*)",
        r'fetch\(["\']([^"\']+)',
    ]
    hits = set()
    for p in pats:
        hits.update(m[:160] for m in re.findall(p, r.text))
    print("--- candidate endpoints ---")
    for x in sorted(hits)[:40]:
        print(x)
