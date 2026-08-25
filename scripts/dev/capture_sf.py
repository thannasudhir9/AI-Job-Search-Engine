import json
import sys

from playwright.sync_api import sync_playwright

sys.stdout.reconfigure(encoding="utf-8", errors="replace")

captured = []


def on_response(resp):
    url = resp.url
    ct = (resp.headers.get("content-type") or "").lower()
    if "json" in ct and any(k in url.lower() for k in ("job", "search", "list", "vacanc")):
        try:
            body = resp.json()
            size = len(json.dumps(body))
            captured.append((url, size, body))
        except Exception:
            pass


with sync_playwright() as p:
    browser = p.chromium.launch(headless=True)
    page = browser.new_page()
    page.on("response", on_response)
    page.goto("https://careers.salesforce.com/en/jobs/?search=forward%20deployed&location=Germany", timeout=60000)
    page.wait_for_timeout(9000)
    browser.close()

print(f"captured {len(captured)} json responses\n")
for url, size, body in sorted(captured, key=lambda x: -x[1])[:5]:
    print("URL:", url[:160])
    print("SIZE:", size)
    if isinstance(body, dict):
        print("KEYS:", list(body.keys())[:12])
        found = False
        for k, v in body.items():
            if isinstance(v, list) and v and isinstance(v[0], dict):
                print(f"LIST '{k}' ({len(v)} items), first item keys:", list(v[0].keys())[:15])
                print(json.dumps(v[0], indent=1)[:900])
                found = True
                break
        if not found and isinstance(body.get("data"), dict):
            print("data keys:", list(body["data"].keys())[:12])
    print("=" * 70)
