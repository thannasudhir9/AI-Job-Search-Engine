# 🧾 Build Log — Commands Used

Chronological record of the important commands run while building this project.
All development scripts referenced here live in [`scripts/dev/`](scripts/dev/).

> Session date: **2026-08-25** (times CEST)

## 1 · Environment & scaffold

```powershell
python --version            # 3.14.5   node --version   # v22.22.3
python -m venv backend\.venv
backend\.venv\Scripts\python.exe -m pip install -r backend\requirements.txt
npx create-next-app@latest frontend --ts --tailwind --eslint --app --no-src-dir --import-alias "@/*" --use-npm --yes
```

## 2 · Run servers (used throughout)

```powershell
# backend  → http://localhost:8000  (Swagger UI at /docs)
cd backend; .\.venv\Scripts\python.exe -m uvicorn app.main:app --port 8000
# frontend → http://localhost:3000
cd frontend; npm.cmd run dev          # production: npm.cmd run build; npm.cmd run start
```

## 3 · Data pipeline commands (via curl / httpx one-liners)

```powershell
# profile + matching
Invoke-RestMethod -Uri http://localhost:8000/api/profile -Method Put -ContentType "application/json" -Body '{...}'
curl.exe -s -X POST http://localhost:8000/api/resumes/upload -F "file=@Sudhir_CV.pdf"
# board sources
Invoke-RestMethod -Uri http://localhost:8000/api/companies -Method Post -Body '{"name":"OpenAI","source":"ashby","slug":"openai"}'
# sync everything (waits, prints stats)
Invoke-RestMethod -Uri "http://localhost:8000/api/sync?wait=true" -Method Post
# scored matches with filters
Invoke-RestMethod -Uri "http://localhost:8000/api/matches?country=UAE&role=fde&min_salary=80000&limit=500"
```

Helper scripts that wrap the above (see files for exact payloads):

| Script | Purpose |
|---|---|
| `dev/extract_cv.py` | pull resume text out of the PDF in Downloads |
| `dev/setup_profile.py` | seed FDE-focused profile, upload CV, add first boards |
| `dev/probe_boards.py` / `probe2.py` | discover which ATS APIs each company exposes |
| `dev/probe_sf*.py`, `capture_sf*.py` | reverse-engineer Salesforce Careers (found CDN JSON) |
| `dev/add_roles_sf.py` | PM/FDE/TA titles + Salesforce priority source + resync |
| `dev/add_linkedin.py` | LinkedIn guest-search sources + salary-currency backfill |
| `dev/fde_matches.py`, `dev/tailor_top.py` | report top matches, generate tailored resumes |

## 4 · Playwright (screenshots, E2E, Salesforce capture)

```powershell
backend\.venv\Scripts\python.exe -m pip install playwright
backend\.venv\Scripts\python.exe -m playwright install chromium     # 114 MB headless shell
backend\.venv\Scripts\python.exe scripts\dev\screenshot.py           # app gallery → frontend/public/screenshots
backend\.venv\Scripts\python.exe scripts\dev\e2e_test.py             # 10/10 feature checks
```

## 5 · Quality gates run after each change

```powershell
cd frontend; npm.cmd run build        # TypeScript + ESLint gate
# restart uvicorn to pick up backend changes; measure endpoint timings:
Measure-Command { Invoke-WebRequest http://localhost:8000/api/matches?limit=500 }
```

Notable fix during development: matches endpoint was doing one SQL query per job
(3,740 ms for 500 rows) — rewritten to filter+paginate in SQL (**~60 ms**).

## 6 · Git publish (2026-08-25)

```powershell
git init
git add .
git commit -m "v1.0: AI job search engine - find/match/tailor/track"
git branch -M main
git remote add origin https://github.com/thannasudhir9/AI-Job-Search-Engine.git
git push -u origin main
```
