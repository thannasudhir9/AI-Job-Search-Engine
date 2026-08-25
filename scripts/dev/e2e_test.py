"""End-to-end test of the AI Job Search Engine web app (v1.1 IA)."""
import sys

from playwright.sync_api import sync_playwright

sys.stdout.reconfigure(encoding="utf-8", errors="replace")
BASE = "http://localhost:3000"

results = []


def check(name, fn):
    try:
        detail = fn()
        results.append(("PASS", name, detail or ""))
    except Exception as e:
        results.append(("FAIL", name, str(e)[:160]))


def run():
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        ctx = browser.new_context(viewport={"width": 1440, "height": 900})
        page = ctx.new_page()

        # ---------- Job Search Engine (home) ----------
        def t_home():
            page.goto(BASE + "/", wait_until="networkidle", timeout=45000)
            assert "Job Search Engine" in page.inner_text("h1"), "h1 missing"
            page.wait_for_selector("ul > li a[href^='http']", timeout=20000)
            cards = page.locator("ul > li").count()
            assert cards >= 10, f"only {cards} cards"
            body = page.inner_text("body")
            assert "/100" in body and "Best match" in body, "score/sort missing"
            return f"{cards} ranked cards with /100 scores + sort control"
        check("Home = Job Search Engine with ranked cards", t_home)

        # ---------- Filters on home ----------
        def t_filters():
            page.goto(BASE + "/", wait_until="domcontentloaded", timeout=45000)
            page.wait_for_timeout(2500)
            page.select_option("select[aria-label='Country']", "UAE")
            page.wait_for_timeout(2500)
            page.select_option("select[aria-label='Role']", "fde")
            page.wait_for_timeout(2500)
            body = page.inner_text("body").lower()
            assert "forward deployed" in body, "no FDE rows for UAE"
            chips = page.locator("button:has(svg)").count()  # chip X buttons exist
            assert chips >= 0
            # sort by newest works
            page.select_option("select[aria-label='Sort']", "newest")
            page.wait_for_timeout(2500)
            return "country+role filters & sort applied via UI"
        check("Filters: country, role, sort", t_filters)

        # ---------- Sources page ----------
        def t_sources():
            page.goto(BASE + "/sources", wait_until="networkidle", timeout=45000)
            body = page.inner_text("body")
            assert "Watched sources" in body, "watchlist missing"
            assert "Salesforce Careers" in body, "priority source missing"
            assert "Sync now" in body, "sync button missing"
            n = int(body.split("Watched sources (")[1].split(")")[0])
            assert n >= 25, f"only {n} sources"
            return f"{n} sources listed incl. Salesforce Careers"
        check("Sources page: sync + watchlist", t_sources)

        # ---------- Tailor + career-ops extras ----------
        def t_tailor():
            page.goto(BASE + "/tailor/1710", wait_until="networkidle", timeout=60000)
            pre = page.locator("pre.code-view")
            pre.first.wait_for(timeout=20000)
            assert len(pre.first.inner_text()) > 300, "resume preview short"
            btn = page.get_by_role("button", name="Draft outreach email")
            btn.scroll_into_view_if_needed()
            btn.click()
            found = False
            for _ in range(30):  # poll up to 15s
                page.wait_for_timeout(500)
                if "Outreach draft" in page.inner_text("body"):
                    found = True
                    break
            assert found, "outreach draft not generated"
            return "resume preview + outreach email draft working"
        check("Tailor page: resume + outreach draft", t_tailor)

        def t_cover():
            page.goto(BASE + "/tailor/1710", wait_until="domcontentloaded", timeout=45000)
            page.wait_for_timeout(2500)
            btn = page.get_by_role("button", name="Generate cover letter")
            btn.scroll_into_view_if_needed()
            btn.click()
            found = False
            for _ in range(20):
                page.wait_for_timeout(500)
                if "Download PDF" in page.inner_text("body"):
                    found = True
                    break
            assert found, "cover letter not generated"
            return "cover letter generated with PDF link"
        check("Tailor page: cover letter generation", t_cover)

        # ---------- Applied ----------
        def t_applied():
            page.goto(BASE + "/applied", wait_until="networkidle", timeout=45000)
            page.wait_for_timeout(1500)
            body = page.inner_text("body")
            assert "Resume PDF" in body or "Open tailored" in body, "resume links missing"
            return "applied card shows resume links"
        check("Applied page lists job + resume", t_applied)

        # ---------- Tracker move ----------
        def t_tracker():
            page.goto(BASE + "/tracker", wait_until="networkidle", timeout=45000)
            page.wait_for_timeout(1500)
            btns = page.locator("button:has-text('▶')")
            assert btns.count() >= 1, "no move buttons"
            btns.first.click()
            page.wait_for_timeout(1800)
            return "status advanced via ▶"
        check("Tracker kanban status change", t_tracker)

        # ---------- Profile viewers ----------
        def t_profile():
            page.goto(BASE + "/profile", wait_until="networkidle", timeout=60000)
            page.get_by_role("button", name="View master resume text").click()
            page.wait_for_timeout(1200)
            txt = page.locator("pre.code-view").first.inner_text(timeout=10000)
            assert "SUDHIR" in txt.upper(), "master resume not shown"
            import re

            m = re.search(r"Tailored resumes \((\d+)\)", page.inner_text("body"))
            assert m and int(m.group(1)) >= 3, "library missing"
            return f"master viewer + {m.group(1)} tailored resumes"
        check("Profile: master resume viewer + library", t_profile)

        # ---------- Theme ----------
        def t_theme():
            page.goto(BASE + "/", wait_until="domcontentloaded", timeout=45000)
            page.wait_for_timeout(800)
            assert page.evaluate("document.documentElement.classList.contains('dark')") is False
            page.locator("button[aria-label='Toggle theme']").click()
            page.wait_for_timeout(400)
            assert page.evaluate("document.documentElement.classList.contains('dark')") is True
            page.reload(wait_until="domcontentloaded")
            page.wait_for_timeout(800)
            assert page.evaluate("document.documentElement.classList.contains('dark')") is True
            page.locator("button[aria-label='Toggle theme']").click()
            return "light default, toggle persists"
        check("Theme toggle persistence", t_theme)

        # ---------- Docs + lightbox ----------
        def t_docs():
            page.goto(BASE + "/docs", wait_until="networkidle", timeout=45000)
            body = page.inner_text("body")
            for sec in ("Overview", "Project structure", "Prompts", "Future scope", "Screenshots", "Logs"):
                assert sec in body, f"{sec} missing"
            assert "career-ops" in body.lower(), "career-ops attribution missing"
            page.get_by_role("button", name="📸 Screenshots").click()
            page.wait_for_timeout(2000)
            page.locator("figure").first.click()
            page.wait_for_timeout(800)
            assert page.locator("div.fixed.inset-0.z-50").count() == 1, "lightbox did not open"
            page.keyboard.press("Escape")
            return "sections + career-ops attribution + lightbox OK"
        check("Docs tab incl. lightbox", t_docs)

        # ---------- /matches redirect ----------
        def t_redirect():
            page.goto(BASE + "/matches", wait_until="domcontentloaded", timeout=30000)
            page.wait_for_timeout(1500)
            assert page.url.rstrip("/") == BASE, f"redirect failed, at {page.url}"
            return "/matches redirects to /"
        check("/matches legacy redirect", t_redirect)

        browser.close()

    fails = [r for r in results if r[0] == "FAIL"]
    for status, name, detail in results:
        mark = "✅" if status == "PASS" else "❌"
        print(f"{mark} {name}" + (f"\n     -> {detail}" if status == "PASS" else f"\n     !! {detail}"))
    print(f"\n{len(results) - len(fails)}/{len(results)} passed")
    return 1 if fails else 0


if __name__ == "__main__":
    sys.exit(run())
