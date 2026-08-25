import json
import re
import sys

import httpx

sys.stdout.reconfigure(encoding="utf-8", errors="replace")
h = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 Chrome/126 Safari/537.36",
}

with httpx.Client(timeout=25, follow_redirects=True, headers=h) as c:
    r = c.get("https://careers.salesforce.com/en/jobs/?search=fde&country=Germany")
    print("status", r.status_code, "len", len(r.text))

    # 1) JSON-LD JobPosting?
    ld = re.findall(r'<script type="application/ld\+json">(.*?)</script>', r.text, re.S)
    print("json-ld blocks:", len(ld))
    for block in ld[:2]:
        try:
            data = json.loads(block)
            t = data.get("@type") if isinstance(data, dict) else "?"
            print("  @type:", t)
        except Exception as e:
            print("  parse err", e)

    # 2) job detail links?
    links = set(re.findall(r'href="(/en/jobs/[^"]+|https://careers\.salesforce\.com/en/jobs/[^"]+)"', r.text))
    print("detail links:", len(links))
    for x in sorted(links)[:8]:
        print(" ", x)

    # 3) any embedded state json?
    m = re.search(r'window\.__INITIAL_STATE__\s*=\s*(\{.*?\});?\s*</script>', r.text, re.S)
    print("initial state:", bool(m))
    hits = set(re.findall(r'"(jobs?[^"]{0,40})"\s*:', r.text.lower()))
    print("job-ish keys:", list(hits)[:12])
