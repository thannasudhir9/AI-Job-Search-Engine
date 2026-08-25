# Plan: Local AI Job-Application Agent (Tsenta-style)

A self-hosted web app that runs on `localhost` and does what tsenta.com does:
**find matching jobs → tailor resume → apply (with review) → track results.**

---

## 1. MVP Scope (core loop)

| Feature | Tsenta | Our local version |
|---|---|---|
| Job discovery | Watches 50k career pages | Poll public board APIs (Greenhouse, Lever, Ashby) every few hours |
| Matching | Contextual models | Keyword + embedding similarity scoring |
| Resume tailoring | ATS-friendly rewrite | LLM rewrites resume per job → PDF |
| Auto-apply | Submits on 30+ ATSs | Playwright fills forms, **you click submit** (review step) |
| Tracking | Dashboard + apps | Kanban tracker with status history |

Out of scope for v1: mobile apps, Chrome extension, iMessage/WhatsApp, account-creation & OTP handling on employer sites, multi-user/billing.

---

## 2. Recommended Stack

- **App:** Next.js 15 (App Router) + TypeScript + Tailwind + shadcn/ui
  *(Python alternative: FastAPI + Vite/React if you prefer)*
- **DB:** SQLite via Drizzle ORM — zero-config, perfect for local
- **LLM:** Ollama (`llama3.1`, `qwen2.5`) for 100% local; optional OpenAI/Anthropic API key as fallback for better tailoring
- **Embeddings:** `nomic-embed-text` via Ollama (or sqlite-vec / in-memory cosine)
- **Job sources (free, public JSON):**
  - Greenhouse: `https://boards-api.greenhouse.io/v1/boards/{company}/jobs`
  - Lever: `https://api.lever.co/v0/postings/{company}?mode=json`
  - Ashby: `https://api.ashbyhq.com/posting-api/job-board/{company}`
  - Optional: Remotive / RemoteOK public APIs for breadth
- **Resume output:** react-pdf or docx templating → ATS-friendly single-column PDF
- **Automation:** Playwright (headed mode so you can watch + solve CAPTCHAs/OTPs yourself)
- **Scheduler:** node-cron worker (or simple interval task) for job sync

---

## 3. Architecture

```
┌───────────────────────────── localhost:3000 ─────────────────────────────┐
│  Next.js UI                                                              │
│  ├─ Profile & resume upload        ├─ Job search / match list            │
│  ├─ Tailored resume preview/approve├─ Application tracker (kanban)       │
└──────────────┬───────────────────────────┬───────────────────────────────┘
               │                           │
      ┌────────▼────────┐         ┌────────▼─────────┐
      │  Sync worker    │         │  Apply runner    │
      │  (cron: fetch   │         │  (Playwright,    │
      │  boards, embed, │         │  headed, human   │
      │  score matches) │         │  clicks submit)  │
      └────────┬────────┘         └────────┬─────────┘
               └──────────► SQLite ◄───────┘
```

---

## 4. Data Model (Drizzle/SQLite)

- `profile` – name, contact, skills[], experience[], preferences (titles, locations, salary, remote)
- `resumes` – uploaded master resume (parsed text), generated variants
- `jobs` – source, company, title, location, url, description, posted_at, raw_json
- `matches` – job_id ↔ profile, match_score, reasons, dismissed
- `applications` – job_id, resume_variant_id, status (draft → ready → applied → interview → offer/rejected), timeline events
- `settings` – model choice, sync schedule, API keys

---

## 5. Build Phases

### Phase 0 – Scaffold (~half day)
- `create-next-app` + Drizzle + SQLite + shadcn/ui, run migrations, base layout/nav.

### Phase 1 – Profile & resume (~1 day)
- Upload PDF → parse text (`pdf-parse`).
- Profile form; preferences stored.

### Phase 2 – Job ingestion (~1–2 days)
- Company-list config (JSON) → fetch Greenhouse/Lever/Ashby boards.
- Dedupe by URL/id; normalize title/location/description.
- Cron sync + manual "Sync now" button.

### Phase 3 – Matching (~1–2 days)
- Embed descriptions once; embed profile/preferences.
- Score = weighted (embedding similarity + title keyword overlap + location/remote filter).
- Match list UI with score, reasons, dismiss/save.

### Phase 4 – Resume tailoring (~2 days)
- Prompt template: master resume + job description → tailored, ATS-safe resume (no tables/graphics).
- Diff view (what changed), approve/edit → generate PDF.
- Cover letter variant (optional toggle).

### Phase 5 – Application tracker (~1 day)
- Kanban board, status changes, notes, activity log per application.

### Phase 6 – Assisted auto-apply (~2–3 days, hardest)
- "Apply" button opens Playwright (headed) at the job URL.
- Detect common fields (name/email/phone/work-auth) + upload tailored resume PDF.
- Autofill everything, then **pause for human review** before submit.
- Record outcome + screenshot into the tracker.

### Phase 7 – Polish
- Daily digest email/notification, stats page, backup of SQLite file, packaging (`npm run dev` one-liner or Electron wrapper later).

---

## 6. Milestones

| Milestone | Deliverable |
|---|---|
| M1 (end of Phase 2) | Fresh jobs flowing into local DB daily |
| M2 (end of Phase 4) | One-click tailored resume for any matched job |
| M3 (end of Phase 5) | Full find → tailor → track loop usable |
| M4 (end of Phase 6) | One-click autofill + manual submit |

---

## 7. Practical & Legal Notes

- Board APIs above are public/read-only — respect them: cache responses, sync a few times/day, identify your client.
- Avoid mass auto-submission to employer sites; keep the human-in-the-loop submit (also avoids ToS/CAPTCHA problems).
- Never store employer-site passwords in plaintext; prefer you typing them in the visible Playwright session.
- Fully-local mode needs ~8 GB RAM machine for decent Ollama models; otherwise use an API key.

---

## 8. First Steps (when you say go)

1. Scaffold Phase 0 project in this folder.
2. Add 3–5 companies to the board config and prove ingestion works end-to-end.
3. Then iterate through Phases 1→6.
