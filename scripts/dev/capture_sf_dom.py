import re
import sys

from playwright.sync_api import sync_playwright

sys.stdout.reconfigure(encoding="utf-8", errors="replace")

reqs = []

with sync_playwright() as p:
    browser = p.chromium.launch(headless=True)
    ctx = browser.new_context(viewport={"width": 1440, "height": 900})
    page = ctx.new_page()
    page.on("request", lambda r: reqs.append(r.url))
    page.goto("https://careers.salesforce.com/en/jobs/", timeout=60000)
    page.wait_for_timeout(8000)
    body_text = page.inner_text("body")
    browser.close()

print(f"total requests: {len(reqs)}")
interesting = [u for u in reqs if any(k in u.lower() for k in ("api", "search", "job", "graphql", "query"))]
print("-- interesting requests --")
for u in sorted(set(interesting))[:25]:
    print(" ", u[:150])

# any job-looking anchors in DOM?
html = page.content() if False else ""
print("\n-- body sample (first 1200 chars) --")
print(body_text[:1200])
