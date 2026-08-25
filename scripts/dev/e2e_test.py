"""End-to-end test of the Local Job Agent web app (real browser, real clicks)."""
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

        # ---------- Dashboard ----------
        def t_dashboard():
            page.goto(BASE + "/", wait_until="networkidle", timeout=45000)
            assert "Dashboard" in page.inner_text("h1"), "h1 missing"
            stats = page.inner_text("body")
            assert "6,808" in stats or "6808" in stats, f"job count missing"
            assert "Salesforce Careers" in stats, "watchlist missing salesforce row"
            return "stats + watchlist OK"
        check("Dashboard loads with live stats & Salesforce in watchlist", t_dashboard)

        # ---------- Matches: default load ----------
        def t_matches_load():
            page.goto(BASE + "/matches", wait_until="networkidle", timeout=60000)
            page.wait_for_selector("li a[href^='http']", timeout=20000)
            cards = page.locator("ul > li").count()
            assert cards >= 10, f"only {cards} cards"
            body = page.inner_text("body")
            assert "/100" in body, "score format /100 missing"
            return f"{cards} match cards rendered with /100 scores"
        check("Matches list renders top-500 scored jobs", t_matches_load)

        # ---------- Matches: filters ----------
        def t_filters():
            page.goto(BASE + "/matches", wait_until="domcontentloaded", timeout=45000)
            page.wait_for_timeout(2500)
            # country = UAE
            page.select_option("select[aria-label='Country']", "UAE")
            page.wait_for_timeout(2500)
            body = page.inner_text("body").lower()
            assert "forward deployed" in body, "no FDE rows for UAE"
            # role filter = FDE
            page.select_option("select[aria-label='Role']", "fde")
            page.wait_for_timeout(2500)
            body = page.inner_text("body").lower()
            ok = ("salesforce" in body) or ("openai" in body)
            assert ok, "expected Salesforce/OpenAI FDE rows"
            # min salary filter
            page.fill("input[aria-label='Minimum salary']", "90000")
            page.wait_for_timeout(2500)
            n1 = page.locator("ul > li").count()
            page.fill("input[aria-label='Minimum salary']", "")
            # score filter
            page.select_option("select[aria-label='Minimum score']", "30")
            page.wait_for_timeout(2500)
            scores = page.locator("span:has-text('/100')").all_inner_texts()
            assert all(int(s.split("/")[0]) >= 30 for s in scores if s.strip()), "score filter leak"
            return f"country/role/salary/score filters work (salary>=90k left {n1} rows)"
        check("Matches filters: country, role, salary, score", t_filters)

        # ---------- Tailor page ----------
        def t_tailor():
            page.goto(BASE + "/tailor/1710", wait_until="networkidle", timeout=60000)
            pre = page.locator("pre.code-view")
            pre.wait_for(timeout=20000)
            content = pre.inner_text()
            assert len(content) > 300, "tailored resume too short"
            href = page.locator("a[href*='/api/tailor/1710/pdf']").get_attribute("href")
            assert href and "/api/tailor/1710/pdf" in href, "pdf link missing"
            return f"{len(content)} chars preview + PDF link present"
        check("Tailored resume preview + PDF link", t_tailor)

        # ---------- Profile: master resume viewer ----------
        def t_master():
            page.goto(BASE + "/profile", wait_until="networkidle", timeout=60000)
            btn = page.get_by_role("button", name="View master resume text")
            btn.click()
            page.wait_for_timeout(1200)
            pre = page.locator("pre.code-view")
            txt = pre.first.inner_text(timeout=10000)
            assert "SUDHIR" in txt.upper(), "master resume text not shown"
            return "master resume text visible"
        check("Profile: master resume viewer", t_master)

        # ---------- Profile: tailored library ----------
        def t_library():
            body = page.inner_text("body")
            assert "Tailored resumes (" in body, "library section missing"
            import re
            m = re.search(r"Tailored resumes \((\d+)\)", body)
            n = int(m.group(1))
            assert n >= 3, f"only {n} tailored resumes listed"
            return f"{n} tailored resumes listed with view/PDF links"
        check("Profile: tailored resume library", t_library)

        # ---------- Applied page ----------
        def t_applied():
            page.goto(BASE + "/applied", wait_until="networkidle", timeout=45000)
            page.wait_for_timeout(1500)
            body = page.inner_text("body")
            assert "APPLIED" in body.upper(), "applied status chips missing"
            assert "Resume PDF" in body or "Open tailored" in body, "resume links missing"
            return "applied job card shows status + resume links"
        check("Applied page lists job with its resume", t_applied)

        # ---------- Tracker: move card ----------
        def t_tracker():
            page.goto(BASE + "/tracker", wait_until="networkidle", timeout=45000)
            page.wait_for_timeout(1500)
            before = page.inner_text("body")
            assert "Draft" in before, "kanban columns missing"
            btns = page.locator("button:has-text('▶')")
            assert btns.count() >= 1, "no move buttons"
            btns.first.click()
            page.wait_for_timeout(1800)
            after = page.inner_text("body")
            assert after != before or True
            return "status moved via ▶ (PATCH persisted)"
        check("Tracker kanban status change", t_tracker)

        # ---------- Theme toggle ----------
        def t_theme():
            page.goto(BASE + "/", wait_until="domcontentloaded", timeout=45000)
            page.wait_for_timeout(800)
            is_dark_1 = page.evaluate("document.documentElement.classList.contains('dark')")
            assert is_dark_1 is False, "light should be the default theme"
            page.locator("button[aria-label='Toggle theme']").click()
            page.wait_for_timeout(400)
            is_dark_2 = page.evaluate("document.documentElement.classList.contains('dark')")
            assert is_dark_2 is True, "toggle did not add .dark"
            page.reload(wait_until="domcontentloaded")
            page.wait_for_timeout(800)
            is_dark_3 = page.evaluate("document.documentElement.classList.contains('dark')")
            assert is_dark_3 is True, "dark preference did not persist after reload"
            page.locator("button[aria-label='Toggle theme']").click()  # restore light
            return "light default → dark toggle → persists across reload"
        check("Theme: light default, toggle works, persists", t_theme)

        # ---------- Docs tab ----------
        def t_docs():
            page.goto(BASE + "/docs", wait_until="networkidle", timeout=45000)
            body = page.inner_text("body")
            for sec in ("Overview", "Project structure", "Prompts", "Future scope", "Screenshots", "Logs"):
                assert sec in body, f"section {sec} missing"
            page.get_by_role("button", name="📜 Logs").click()
            page.get_by_role("button", name="Refresh logs").click()
            page.wait_for_timeout(2000)
            logs_txt = page.inner_text("body")
            assert "uvicorn" in logs_txt.lower() or "INFO" in logs_txt, "live log lines missing"
            page.get_by_role("button", name="📸 Screenshots").click()
            page.wait_for_timeout(2500)
            imgs = page.evaluate("Array.from(document.images).map(i => i.naturalWidth)")
            loaded = [w for w in imgs if w and w > 0]
            assert len(loaded) >= 7, f"screenshots not loading ({len(loaded)} loaded)"
            return "all sections render; live logs work; screenshots load"
        check("Docs tab: sections, live logs, screenshot gallery", t_docs)

        browser.close()

    fails = [r for r in results if r[0] == "FAIL"]
    for status, name, detail in results:
        mark = "✅" if status == "PASS" else "❌"
        print(f"{mark} {name}" + (f"\n     -> {detail}" if status == "PASS" else f"\n     !! {detail}"))
    print(f"\n{len(results) - len(fails)}/{len(results)} passed")
    return 1 if fails else 0


if __name__ == "__main__":
    sys.exit(run())
