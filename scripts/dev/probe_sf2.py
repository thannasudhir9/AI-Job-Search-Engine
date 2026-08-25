import re
import sys

import httpx

sys.stdout.reconfigure(encoding="utf-8", errors="replace")
h = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 Chrome/126 Safari/537.36",
}

with httpx.Client(timeout=25, follow_redirects=True, headers=h) as c:
    r = c.get("https://careers.salesforce.com/en/jobs/")
    text = r.text
    idxs = [m.start() for m in re.finditer(r"company-target", text)]
    print("mentions:", len(idxs))
    for i in idxs[:5]:
        print("...", text[max(0, i - 260) : i + 320].replace("\n", " "), "\n---")
