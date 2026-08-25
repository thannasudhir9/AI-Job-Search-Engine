import sys

from playwright.sync_api import sync_playwright

sys.stdout.reconfigure(encoding="utf-8", errors="replace")

seen = []


def on_response(resp):
    ct = (resp.headers.get("content-type") or "").lower()
    if "html" in ct:
        return
    seen.append((resp.status, resp.request.method, resp.url[:150], ct[:40], len(resp.body()) if resp.status == 200 else 0))


with sync_playwright() as p:
    browser = p.chromium.launch(headless=True)
    page = browser.new_page()
    page.on("response", on_response)
    page.goto("https://careers.salesforce.com/en/jobs/", timeout=60000)
    page.wait_for_timeout(5000)
    # scroll to trigger lazy loads
    page.mouse.wheel(0, 3000)
    page.wait_for_timeout(4000)
    browser.close()

print(f"non-html responses: {len(seen)}\n")
for s in sorted(seen, key=lambda x: -x[4]):
    print(s[0], s[1], f"[{s[4]:>7}b]", s[3], "|", s[2])
