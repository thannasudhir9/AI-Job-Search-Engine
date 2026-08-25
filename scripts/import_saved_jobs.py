"""Import your saved jobs from LinkedIn using your real Chrome login.

Usage: close Google Chrome, then run:
    backend\\.venv\\Scripts\\python.exe scripts\\import_saved_jobs.py

A visible Chrome window opens on your profile. If LinkedIn asks you to log
in / approve, do it in that window - the script waits up to 3 minutes.
Saved jobs are imported as Draft applications in the tracker.
"""
import re
import sys
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8", errors="replace")

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "backend"))

from app.db import SessionLocal  # noqa: E402
from app.models import Application, Company, Job, Match  # noqa: E402

SAVED_URL = "https://www.linkedin.com/my-items/saved-jobs/"
CHROME_PROFILE = Path.home() / "AppData" / "Local" / "Google" / "Chrome" / "User Data"
SCRATCH_PROFILE = Path(__file__).resolve().parent / ".linkedin-profile"
STATE_FILE = Path(__file__).resolve().parent / ".linkedin-state.json"


def _make_scratch_profile() -> None:
    """Chrome >=136 refuses CDP on the DEFAULT profile dir, so clone the
    session-critical files into a scratch profile (same Windows user => DPAPI ok)."""
    import shutil

    if SCRATCH_PROFILE.exists():
        shutil.rmtree(SCRATCH_PROFILE, ignore_errors=True)
    (SCRATCH_PROFILE / "Default" / "Network").mkdir(parents=True, exist_ok=True)
    src_default = CHROME_PROFILE / "Default"
    pairs = [
        (src_default / "Network" / "Cookies", SCRATCH_PROFILE / "Default" / "Network" / "Cookies"),
        (CHROME_PROFILE / "Local State", SCRATCH_PROFILE / "Local State"),
        (src_default / "Preferences", SCRATCH_PROFILE / "Default" / "Preferences"),
    ]
    for src, dst in pairs:
        try:
            if src.exists():
                shutil.copy2(src, dst)
        except Exception as e:
            print(f"  (skip {src.name}: {e})")


def main() -> int:
    from playwright.sync_api import sync_playwright

    print("Preparing a scratch Chrome profile cloned from YOUR Chrome session...")
    _make_scratch_profile()

    with sync_playwright() as p:
        ctx = p.chromium.launch_persistent_context(
            user_data_dir=str(SCRATCH_PROFILE),
            channel="chrome",
            headless=False,
            args=["--disable-blink-features=AutomationControlled"],
            viewport={"width": 1400, "height": 900},
        )
        page = ctx.pages[0] if ctx.pages else ctx.new_page()
        page.goto(SAVED_URL, timeout=60000)

        # wait for either the saved list or a login wall to clear
        print("Waiting up to 5 MINUTES - please log in to LinkedIn inside the opened window.")
        deadline = 300
        found = False
        try:
            for _ in range(deadline // 5):
                page.wait_for_timeout(5000)
                html = page.content()
                if "/jobs/view/" in html and "my-items" in page.url:
                    found = True
                    break
                if "/login" in page.url or "checkpoint" in page.url:
                    continue
        except Exception as e:
            print(f"Browser window was closed before finishing ({type(e).__name__}).")
            return 1
        if not found:
            print("Could not reach the saved-jobs list in time.")
            ctx.close()
            return 1

        try:
            ctx.storage_state(path=str(STATE_FILE))
        except Exception:
            pass

        # scroll to load all rows
        for _ in range(10):
            page.mouse.wheel(0, 2500)
            page.wait_for_timeout(600)

        html = page.content()
        cards = re.findall(
            r'href="[^"]*/jobs/view/([^/?"]+)[^"]*"[^>]*>.*?aria-label="([^"]+)"',
            html,
            re.S,
        )
        if not cards:
            # fallback: ids only, titles from card text
            ids = re.findall(r"/jobs/view/([^/?\"&#]+)", html)
            cards = [(i, "") for i in dict.fromkeys(ids)]

        seen = {}
        for jid, title in cards:
            jid = jid.strip()
            title = re.sub(r"\s+", " ", title).strip()
            if jid and jid not in seen:
                seen[jid] = title
        print(f"Found {len(seen)} saved jobs on LinkedIn.")

        db = SessionLocal()
        company_row = (
            db.query(Company).filter(Company.source == "linkedin").first()
        )
        if company_row is None:
            company_row = Company(name="LinkedIn Saved", source="linkedin", slug="saved")
            db.add(company_row)
            db.commit()

        imported = skipped = 0
        for jid, title in seen.items():
            ext_id = f"li-saved-{jid}"
            if db.query(Job).filter(Job.source == "linkedin", Job.ext_id == ext_id).first():
                skipped += 1
                continue
            job = Job(
                company_id=company_row.id,
                company_name="LinkedIn saved job",
                source="linkedin",
                ext_id=ext_id,
                title=(title or f"Saved job {jid}")[:300],
                location="",
                url=f"https://www.linkedin.com/jobs/view/{jid}/",
                description="Imported from your LinkedIn saved jobs.",
            )
            db.add(job)
            db.flush()
            now_iso = __import__("datetime").datetime.utcnow().isoformat()
            db.add(
                Application(
                    job_id=job.id,
                    status="draft",
                    notes="Saved on LinkedIn - imported by Local Job Agent.",
                    events=[{"at": now_iso, "status": "draft", "note": "Imported from LinkedIn saved"}],
                )
            )
            db.add(Match(job_id=job.id, score=0.0, reasons=["From LinkedIn saved"], dismissed=True))
            imported += 1
        db.commit()
        db.close()
        print(f"Imported {imported} new saved jobs as drafts ({skipped} already known).")
        print("You can close the Chrome window now.")
        ctx.close()
        return 0


if __name__ == "__main__":
    sys.exit(main())
