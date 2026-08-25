"""Capture full-page screenshots of every feature into frontend/public/screenshots/."""
import sys
from pathlib import Path

from playwright.sync_api import sync_playwright

sys.stdout.reconfigure(encoding="utf-8", errors="replace")

OUT = Path(r"C:\Users\thann\OneDrive\Documents\Default Project\frontend\public\screenshots")
OUT.mkdir(parents=True, exist_ok=True)

BASE = "http://localhost:3000"
SHOTS = [
    # (path, filename, theme)
    ("/", "dashboard-light", "light"),
    ("/matches", "matches-light", "light"),
    ("/tailor/1710", "tailor-light", "light"),
    ("/applied", "applied-light", "light"),
    ("/tracker", "tracker-light", "light"),
    ("/profile", "profile-light", "light"),
    ("/docs", "docs-light", "light"),
    ("/matches", "matches-dark", "dark"),
    ("/dashboard-dark-placeholder", None, None),  # replaced below by explicit entry
]
# cleaner list without placeholder
SHOTS = [s for s in SHOTS if s[1]] + [
    ("/", "dashboard-dark", "dark"),
]


def main():
    failures = []
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        for path, name, theme in SHOTS:
            ctx = browser.new_context(viewport={"width": 1440, "height": 900})
            if theme == "dark":
                ctx.add_init_script("try{localStorage.setItem('theme','dark')}catch(e){}")
            page = ctx.new_page()
            try:
                page.goto(f"{BASE}{path}", wait_until="networkidle", timeout=45000)
                page.wait_for_timeout(1800)
                out = OUT / f"{name}.png"
                page.screenshot(path=str(out), full_page=True)
                print(f"OK   {name}.png  ({out.stat().st_size // 1024} KB)")
            except Exception as e:
                failures.append((name, str(e)[:120]))
                print(f"FAIL {name}: {e}")
            finally:
                ctx.close()
        browser.close()
    if failures:
        print("\nFAILURES:", failures)
        sys.exit(1)
    print("\nAll screenshots captured.")


if __name__ == "__main__":
    main()
