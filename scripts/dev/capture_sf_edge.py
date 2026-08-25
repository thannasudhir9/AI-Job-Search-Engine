import sys

from playwright.sync_api import sync_playwright

sys.stdout.reconfigure(encoding="utf-8", errors="replace")

UA = ("Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) "
      "Chrome/126.0.0.0 Safari/537.36 Edg/126.0.0.0")

reqs = []
body_text = ""

with sync_playwright() as p:
    try:
        browser = p.chromium.launch(
            channel="msedge",
            headless=True,
            args=["--disable-blink-features=AutomationControlled"],
        )
    except Exception as e:
        print("edge launch failed:", str(e)[:150])
        raise SystemExit(1)
    ctx = browser.new_context(user_agent=UA, locale="en-US")
    ctx.add_init_script("Object.defineProperty(navigator,'webdriver',{get:()=>undefined});")
    page = ctx.new_page()
    page.on("request", lambda r: reqs.append(r.url))
    page.goto("https://careers.salesforce.com/en/jobs/", timeout=60000)
    page.wait_for_timeout(9000)
    try:
        body_text = page.inner_text("body")
    except Exception:
        body_text = "(no body)"
    html_len = len(page.content())
    browser.close()

print(f"requests: {len(reqs)}, html len: {html_len}")
interesting = [u for u in reqs if any(k in u.lower() for k in ("api", "search", "job", "graphql", "query", "talent"))]
print("-- interesting requests --")
for u in sorted(set(interesting))[:30]:
    print(" ", u[:160])
print("\n-- body sample --")
print(body_text[:800])
