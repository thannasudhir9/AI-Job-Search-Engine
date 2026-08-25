# career-ops Feature Inventory & Integration Plan

> Source repo: <https://github.com/santifer/career-ops> (MIT) · Analyzed: **2026-08-26**
> Purpose: complete inventory of career-ops features, mapped against our **AI Job Search Engine**,
> with an implementation plan and phased roadmap.

Legend: ✅ we already have it · 🟡 partial · ❌ missing
Priority: P1 = next · P2 = soon · P3 = later

---

## 1 · Job discovery & scanning

| # | career-ops feature | What it does | Ours | Implementation plan in our stack |
|---|---|---|---|---|
| 1.1 | **89 ATS/board providers** (`providers/*.mjs`) | Uniform scanners for Greenhouse, Lever, Ashby, **Workday, SuccessFactors, Phenom, SmartRecruiters, Personio, Eightfold, Radancy, Workable, Teamtailor, Recruitee, BambooHR, iCIMS, Oracle/Taleo**, plus boards (HN, RemoteOK, Remotive, WeWorkRemotely, Himalayas, The Muse, Wellfound, arbeitnow…) | 🟡 5 source types (greenhouse/lever/ashby/salesforce/linkedin) | Port their `_http`/`_html-to-text` parsing patterns; implement **Workday + SuccessFactors + Phenom** first (unlocks Emirates, Palantir, SAP-shop FDE roles). Provider registry = dict of fetchers we already have. P1/P2 |
| 1.2 | **`scan-hn.mjs`** — Hacker News “Who’s hiring” scraper | Monthly thread parse, keyword filter | ❌ | Fetch Algolia HN API `query=Ask%20HN:%20Who%20is%20hiring`, regex-parse comment threads, store as source. P2 |
| 1.3 | **`jd-capture.mjs` / `find.mjs`** — add any job by URL | Paste a posting URL anywhere → extracted JD becomes a tracked candidate | ❌ | `POST /api/jobs/from-url`: httpx fetch + tag-stripping extractor (reuse greenhouse `_clean_html`), create Job(source="manual"). UI: “＋ Paste job URL” box on home. **P1** |
| 1.4 | **`detect-reposts.mjs`** | Flags reposted roles (signals urgency / prior ghost) | ❌ | Same-title+company seen >30d apart → `reposted` reason chip. Easy SQL window. P2 |
| 1.5 | **Liveness check** (`liveness-core`) | Re-validates posting is still live before you invest time | ❌ | On “Tailor” click, HEAD-request the URL; warn if non-200. P2 |
| 1.6 | **Funded-company discovery** (`company-funded.mjs`) | Surfaces recently funded startups to watch | ❌ | Parse TechCrunch/funding RSS → suggest new watchlist rows. P3 |

## 2 · Evaluation engine

| # | career-ops feature | What it does | Ours | Implementation plan |
|---|---|---|---|---|
| 2.1 | **A–G structured evaluation** | One report per job: A role summary · B CV match (gaps + mitigation) · C level strategy · D comp research · E personalization plan · F interview prep (STAR) · G legitimacy | 🟡 G-heuristics + 0–100 score | `POST /api/evaluate/{job_id}` → LLM returns strict JSON `{a..g, score_1_5, dimensions}` (Ollama), heuristic fallback; render as an **Evaluation tab** on the tailor page. P1 (after Ollama install) |
| 2.2 | **6 role archetypes classification** | Classifies posting type to tune evaluation prompts | ❌ | First block of the same LLM call. P1 (bundled) |
| 2.3 | **`jd-similarity.mjs`** | Embedding similarity between CV and JD | 🟡 wired, inactive until Ollama | Already designed (hybrid scoring). Install Ollama → active. P1 config task |
| 2.4 | **`jd-skill-gap.mjs`** | Lists skills the JD wants that your CV lacks | ❌ | Token-overlap version now (JD tokens − profile tokens → top-N missing skills chip); LLM-refined later. **P1** |
| 2.5 | **Ghost-job fingerprinting** (`fingerprint-core`) | Statistical signals for fake/stale postings | 🟡 scam-pattern flags | Add: desc length outlier, no company site link, repost count. P3 |
| 2.6 | **Work-auth blocker signal** | Flags explicit no-sponsorship JDs as hard blockers | 🟡 amber flag exists | Upgrade to hard-filter toggle in UI (“hide no-sponsorship”). P2 |
| 2.7 | **Score calibration** (`calibrate.mjs`, `eval-golden`) | Recalibrates scores against real outcomes; golden-set tests for LLM quality | ❌ | Track interviews/offers per application → regression weight per source/role; golden prompt tests in pytest. P3 |

## 3 · Resume / CV generation

| # | career-ops feature | What it does | Ours | Implementation plan |
|---|---|---|---|---|
| 3.1 | **ATS PDF generation** (HTML→Playwright, LaTeX option) | Keyword-injected CVs, multiple templates (modern/executive/jake…), Space Grotesk design | 🟡 fpdf2 plain text | Keep fpdf2 default; optionally render HTML template → PDF via Playwright for premium look. P2 |
| 3.2 | **LLM tailoring** (`openai-tailor`, `batch-tailor`) | Per-JD rewrite | ✅ (Ollama path built) | Install Ollama. P1 task |
| 3.3 | **`verify-cv-facts.mjs`** | Anti-hallucination check of tailored output vs master CV | ❌ | Post-generation guard: assert contact lines identical, all employers/dates from master appear; else mark ⚠ unverified. **P1** |
| 3.4 | **CV sync / PDF-ready flags** | Tracks which variants are current vs stale | 🟡 variants stored w/ timestamps | Stale badge if job description changed after variant was made. P3 |

## 4 · Cover letters · emails · application answers

| # | career-ops feature | What it does | Ours | Implementation plan |
|---|---|---|---|---|
| 4.1 | **Cover letter generator** (+ templates, approval gate) | Research-backed letter → PDF | ✅ basic (single template) | Add 3 tone presets + editable-before-download. P2 |
| 4.2 | **Application email drafts** | Recruiter/referral/cold emails | ✅ basic | Add referral vs cold variants. P3 |
| 4.3 | **`application-answers.mjs` — answer bank** | Generates & reuses answers to common form questions (work auth, salary expectation, why-us) | ❌ | `answers` table (question_key → answer); used by future autofill + shown on tailor page. **P1** |
| 4.4 | **`prepare-application.mjs`** | Bundles CV + letter + answers into one package | ❌ | “Download application pack” ZIP on tailor page. P2 |

## 5 · Interview · negotiation · offers

| # | career-ops feature | What it does | Ours | Implementation plan |
|---|---|---|---|---|
| 5.1 | **Interview prep (STAR+R)** per evaluation | Likely questions + suggested stories | ❌ | `POST /api/interview/{job_id}` → questions from JD + profile; simple `/interview/[jobId]` page. P2 |
| 5.2 | **Story Bank** (`match-star.mjs`) | 5–10 master stories reused across answers | ❌ | `stories` table (situation/action/result); linked into 5.1 prompts. P2 |
| 5.3 | **Offer prep + negotiation scripts** (`offer-prep`, `negotiation-roi`, `salary-gap`) | Scripts, geographic-discount pushback, ROI math | ❌ | Offer stage in tracker unlocks an offer-prep panel; salary-gap = posted vs levels.fyi-style baseline (manual input first). P3 |
| 5.4 | **Interview red-flag mode** | Detect bad-employer signals during interviews | ❌ | Checklist UI added to interview stage. P3 |
| 5.5 | **`upskill.mjs`** | Turns recurring skill gaps into a learning plan | ❌ | Aggregate 2.4 gaps across dismissed/low-score matches → learning plan card on Sources page. P3 |

## 6 · Pipeline tracking & analytics

| # | career-ops feature | What it does | Ours | Implementation plan |
|---|---|---|---|---|
| 6.1 | **Canonical tracker** (TSV + integrity checks) | Single source of truth, dedupe, aliases | ✅ SQLite stricter | — |
| 6.2 | **Follow-up cadence** (`followup-cadence`) | Nudge schedule after applying | ❌ | `next_followup_at` on applications; “Due today” badge + sort. **P1** |
| 6.3 | **Funnel analytics** (`funnel-velocity`, `rejection-latency`, `stats`) | Stage counts, median time-in-stage, response rates | ❌ | Simple aggregates endpoint + bar chart on Tracker page. P2 |
| 6.4 | **Weekly digest** (`weekly-digest.mjs`) | Email summary of pipeline movement | ❌ | Local SMTP optional; start with in-app “This week” card. P3 |
| 6.5 | **Reply watching** (`reply-watch`, `reply-matcher`, IMAP) | Matches recruiter emails to applications, auto-status | ❌ | Needs credentials; Phase C. P3 |
| 6.6 | **Agent inbox** | Central inbox for agent-generated items | ❌ | Skip — our UI is the inbox. — |

## 7 · Company research & outreach

| # | career-ops feature | What it does | Ours | Implementation plan |
|---|---|---|---|---|
| 7.1 | **Company history/research** (`company-history`) | Background brief per company | ❌ | LLM + homepage/about scrape on tailor page (“About {company}” collapsible). P3 |
| 7.2 | **Contact finder** (`contacts`) | Finds the right person to message | ❌ | Out of scope locally (LinkedIn-dependent). P3/manual |
| 7.3 | **`invite-match`** | LinkedIn invite drafting matched to roles | ❌ | Manual for now. — |
| 7.4 | **`analyze-patterns`** | Which titles/sources convert to interviews | ❌ | SQL over events; small chart on Tracker. P3 |

## 8 · Platform / infra

| # | career-ops feature | What it does | Ours | Implementation plan |
|---|---|---|---|---|
| 8.1 | **Batch parallel evaluation** (headless workers, state TSV) | 10+ offers at once with retries/resume | ❌ | FastAPI BackgroundTasks queue + `applications.status=batch`; enough at our scale. P2 |
| 8.2 | **Doctor / self-test** (`doctor.mjs`, `validate-portals`) | Health checks for every integration | ❌ | `GET /api/system/selftest`: DB, each source reachability, Ollama, disk — surfaced on Sources page. **P1** |
| 8.3 | **Docker packaging** (`docker-compose.yml`) | One-command deploy | ❌ | Two-service composefile (api+web) + volumes. P2 |
| 8.4 | **Plugin registry** | Third-party extensions | ❌ | Skip — monorepo is fine. — |
| 8.5 | **Multi-language modes** (de/es/fr/hi/…) | Prompts/UI localized | ❌ | Add DE prompt variant for German-language postings. P3 |
| 8.6 | **Budget/free-tier guides** (`RUNNING_ON_A_BUDGET`, `FREE_TIER`) | Run without paid APIs | ✅ philosophy already local-first | — |

---

## Recommended roadmap for AI Job Search Engine

### Phase A — quick wins, no LLM needed (P1, ≈2–3 days)
1. **Paste-job-URL ingestion** (1.3) 2. **Skill-gap chips** (2.4) 3. **Answer bank** (4.3)
4. **Follow-up cadence** (6.2) 5. **Self-test endpoint** (8.2) 6. **Fact-check guard** (3.3)

### Phase B — unlock the LLM layer (install Ollama first) (P1–P2, ≈3–4 days)
7. **A–F structured evaluation report + 1–5 score** rendered per job (2.1/2.2)
8. Semantic matching activation (2.3 — config-only) 9. **Interview prep page** (5.1)
10. Batch evaluate top-20 matches overnight (8.1)

### Phase C — scale & polish (P2–P3)
11. Workday/SuccessFactors/Phenom providers (1.1 — unlocks Emirates-class employers)
12. Funnel analytics + weekly digest (6.3/6.4) 13. HTML CV templates (3.1)
14. Reply-watching via IMAP (6.5) 15. Docker compose (8.3)

> Attribution note: career-ops is MIT-licensed; ideas ported here should credit
> `santifer/career-ops` in code comments where logic is closely modeled.
