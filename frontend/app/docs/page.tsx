"use client";

import { useCallback, useEffect, useState } from "react";

const API = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";
const LAST_UPDATED = "2026-08-25 22:53 CEST";

/* ------------------------------------------------------------------ */
/* Documentation content                                               */
/* ------------------------------------------------------------------ */

const OVERVIEW = `# Local Job Agent — AI Job Search Engine

An AI job-hunt agent that runs entirely on your machine:

1. FIND     Syncs real jobs every 4h from 25 sources:
            Greenhouse / Lever / Ashby boards (OpenAI, Anthropic, Databricks,
            Snowflake, DeepL, Careem, Adyen...), the Salesforce Careers CDN
            feed (high priority) and LinkedIn public job search.
2. MATCH    Scores every job 0-100 against your profile - keyword scoring,
            upgraded to semantic embeddings if Ollama is running.
3. TAILOR   Generates a job-specific ATS-friendly resume (AI rewriting via
            Ollama, deterministic fallback otherwise) and renders it as PDF.
4. TRACK    Kanban tracker + Applied view listing every application together
            with the exact tailored resume that was sent.

Built for FDE / Technical Architect / PM roles across DE / NL / CH / UAE.

QUICK START
    powershell -ExecutionPolicy Bypass -File .\\start.ps1
    open http://localhost:3000          (API docs at :8000/docs)

FULL AI MODE (optional)
    ollama pull llama3.1 && ollama pull nomic-embed-text && ollama serve

Privacy: CV, profile and database stay local; only public job APIs are called.`;

const STRUCTURE = `Default Project/
├── PLAN.md                    original build plan
├── README.md                  readme w/ screenshots + changelog
├── COMMANDS.md                chronological log of commands used
├── start.ps1                  launches backend + frontend windows
│
├── scripts/
│   ├── import_saved_jobs.py   LinkedIn saved jobs via your Chrome session
│   ├── import_saved_jobs.bat  one-click wrapper for the above
│   └── dev/                   every dev/probe/test script used to build this
│       ├── extract_cv.py      resume text extraction
│       ├── setup_profile.py   profile + first boards bootstrap
│       ├── probe_boards.py    ATS API discovery probes
│       ├── capture_sf*.py     Salesforce careers reverse-engineering
│       ├── add_roles_sf.py    PM/FDE/TA titles + Salesforce priority feed
│       ├── add_linkedin.py    LinkedIn sources + currency backfill
│       ├── fde_matches.py     match reporting
│       ├── tailor_top.py      batch tailored-resume generation
│       ├── screenshot.py      full-app screenshot capture (Playwright)
│       └── e2e_test.py        end-to-end browser test suite (10 checks)
│
├── backend/                   FastAPI app (Python)
│   ├── requirements.txt
│   ├── server.log / server_err.log        live-tailed in Docs ▸ Logs
│   ├── data/                  SQLite DB, uploads, generated PDFs (gitignored)
│   └── app/
│       ├── main.py config.py db.py models.py schemas.py utils.py
│       ├── routers/           system profile resumes jobs matches tailor applications
│       └── services/          boards sync matching llm pdfgen scheduler
│
└── frontend/                  Next.js 16 App Router + Tailwind v4
    ├── lib/api.ts             typed API client
    ├── public/screenshots/    app gallery (referenced by README + Docs tab)
    └── app/
        ├── layout.tsx globals.css components/ThemeToggle.tsx
        ├── page.tsx           Dashboard
        ├── matches/page.tsx   score/country/role/salary/company filters
        ├── tailor/[jobId]/    tailored resume preview + PDF
        ├── applied/page.tsx   applied jobs with resume used
        ├── tracker/page.tsx   kanban board
        ├── profile/page.tsx   profile, master resume viewer, library
        └── docs/page.tsx      this documentation tab`;

const PROMPTS = `# Prompts used by the tailoring service (backend/app/services/llm.py)

SYSTEM PROMPT
────────────────────────────────────────────────────────────────────
You are an expert resume writer. You rewrite resumes so they are
tailored to a specific job posting while staying 100% truthful to the
source resume: never invent employers, dates, titles, schools, or
skills the candidate does not have. Output plain text only (no
markdown symbols like ** or #), ATS-friendly single column, with
UPPERCASE section headers such as SUMMARY, SKILLS, EXPERIENCE,
EDUCATION, PROJECTS. Keep it within two pages.
────────────────────────────────────────────────────────────────────

USER TEMPLATE (filled per job)
────────────────────────────────────────────────────────────────────
Tailor this resume for the role below.

JOB TITLE: {job_title}
COMPANY:   {company}

JOB DESCRIPTION (first 6000 chars):
{job_description}

MASTER RESUME:
{master_resume_text}

Rules:
- Emphasize the experience and skills most relevant to this job;
  reorder bullets if helpful.
- Mirror important keywords from the posting where they truthfully apply.
- Do not add new facts. Keep contact info exactly as in the master resume.
- Return ONLY the final resume plain text.
────────────────────────────────────────────────────────────────────

Model: OLLAMA_CHAT_MODEL (default llama3.1), temperature 0.4.
Output is post-processed (** and # stripped) and rendered to PDF by
services/pdfgen.py. Without Ollama, a keyword fallback keeps your
master resume truthful and adds a RELEVANT SKILLS block computed from
token overlap between your profile and the posting.`;

const FUTURE = `# Future scope / roadmap

1. Real auto-apply (Playwright, Phase 6 of PLAN.md)
   - Headed browser session opens the job URL, detects common ATS fields
     (Workday/Greenhouse/Lever), fills them and attaches the tailored PDF.
   - Human-in-the-loop: you review and click Submit yourself.
2. More board sources
   - Workday tenants (Palantir etc.) via their XML feeds where exposed.
   - Salesforce Careers deep-diff alerts (feed already integrated).
   - StepStone / LinkedIn saved-jobs importer hardening.
3. Matching quality
   - Persistent vector store (sqlite-vec) instead of re-embedding.
   - Salary normalization across currencies (CHF/EUR/AED FX table).
   - Learn from outcomes: boost sources/titles where you get interviews.
4. Application automation
   - Auto-detect confirmation e-mails (IMAP) -> auto-move tracker state.
   - Interview tracking with calendar integration.
   - Cover-letter generation per job (same prompt pipeline).
5. Product hardening
   - Multi-user support with authentication.
   - Docker compose packaging for NAS/home-server deployment.
   - Daily e-mail digest of new high-scoring matches.
   - Browser extension "apply to this job" button.
6. Data safety
   - Encrypted storage for any credentials you choose to save.
   - One-click export (JSON) and wipe of all personal data.`;

type LogFile = { file: string; exists: boolean; lines: string[]; total_lines?: number };

const SCREENSHOTS: { src: string; caption: string }[] = [
  { src: "/screenshots/dashboard-light.png", caption: "Dashboard — live stats, board sync, watchlist" },
  { src: "/screenshots/matches-light.png", caption: "Matches — scored /100, country · role · salary · company filters" },
  { src: "/screenshots/tailor-light.png", caption: "Tailored resume preview with PDF download" },
  { src: "/screenshots/applied-light.png", caption: "Applied jobs with the exact resume used" },
  { src: "/screenshots/tracker-light.png", caption: "Application tracker kanban" },
  { src: "/screenshots/profile-light.png", caption: "Profile — master resume viewer + tailored library" },
  { src: "/screenshots/docs-light.png", caption: "Documentation tab" },
  { src: "/screenshots/dashboard-dark.png", caption: "Dashboard — dark theme" },
  { src: "/screenshots/matches-dark.png", caption: "Matches — dark theme" },
];

const SECTIONS = [
  { id: "overview", label: "Overview", body: OVERVIEW },
  { id: "structure", label: "Project structure", body: STRUCTURE },
  { id: "prompts", label: "Prompts", body: PROMPTS },
  { id: "future", label: "Future scope", body: FUTURE },
];

export default function DocsPage() {
  const [active, setActive] = useState("overview");
  const [logs, setLogs] = useState<LogFile[] | null>(null);
  const [loadingLogs, setLoadingLogs] = useState(false);
  const [viewer, setViewer] = useState<number | null>(null);
  const [zoom, setZoom] = useState(1);

  const loadLogs = useCallback(async () => {
    setLoadingLogs(true);
    try {
      const res = await fetch(`${API}/api/logs?lines=80`);
      setLogs(await res.json());
    } catch {
      setLogs([{ file: "(backend unreachable)", exists: false, lines: [] }]);
    } finally {
      setLoadingLogs(false);
    }
  }, []);

  // lightbox keyboard controls
  useEffect(() => {
    if (viewer === null) return;
    const onKey = (e: KeyboardEvent) => {
      if (e.key === "Escape") setViewer(null);
      if (e.key === "ArrowRight") setViewer((v) => ((v ?? 0) + 1) % SCREENSHOTS.length);
      if (e.key === "ArrowLeft") setViewer((v) => ((v ?? 0) - 1 + SCREENSHOTS.length) % SCREENSHOTS.length);
      if (e.key === "+" || e.key === "=") setZoom((z) => Math.min(4, z + 0.25));
      if (e.key === "-") setZoom((z) => Math.max(0.5, z - 0.25));
    };
    window.addEventListener("keydown", onKey);
    return () => window.removeEventListener("keydown", onKey);
  }, [viewer]);

  const openShot = (i: number) => {
    setZoom(1);
    setViewer(i);
  };

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-2xl font-semibold">Documentation</h1>
        <p className="muted text-sm mt-1">
          Architecture, prompts, live logs, roadmap & screenshots · Last updated{" "}
          <strong>{LAST_UPDATED}</strong>
        </p>
      </div>

      <div className="flex flex-wrap gap-2">
        {SECTIONS.map((s) => (
          <button
            key={s.id}
            onClick={() => setActive(s.id)}
            className={active === s.id ? "btn-primary !py-1.5" : "btn-ghost !py-1.5"}
          >
            {s.label}
          </button>
        ))}
        <button
          onClick={() => setActive("screenshots")}
          className={active === "screenshots" ? "btn-primary !py-1.5" : "btn-ghost !py-1.5"}
        >
          📸 Screenshots
        </button>
        <button
          onClick={() => setActive("logs")}
          className={active === "logs" ? "btn-primary !py-1.5" : "btn-ghost !py-1.5"}
        >
          📜 Logs
        </button>
      </div>

      {SECTIONS.filter((s) => s.id === active).map((s) => (
        <section key={s.id} className="card p-6">
          <pre className="whitespace-pre-wrap font-mono text-[13px] leading-relaxed">
{s.body}
          </pre>
        </section>
      ))}

      {active === "logs" && (
        <section className="card p-6 space-y-4">
          <div className="flex items-center justify-between flex-wrap gap-2">
            <p className="muted text-sm">
              Live tail of <code className="font-mono">backend/server.log</code> and{" "}
              <code className="font-mono">server_err.log</code>.
            </p>
            <button onClick={loadLogs} className="btn-ghost !py-1.5 !text-xs">
              {loadingLogs ? "Loading…" : "Refresh logs"}
            </button>
          </div>
          {logs === null && <p className="muted text-sm">Click “Refresh logs” to load.</p>}
          {logs?.map((f) => (
            <div key={f.file}>
              <h3 className="font-mono text-xs muted mb-1">
                {f.file}
                {typeof f.total_lines === "number" && ` (${f.total_lines} lines)`}
              </h3>
              <pre className="code-view rounded-lg p-3 text-[11px] leading-snug max-h-72 overflow-auto font-mono">
{f.exists ? f.lines.join("\n") || "(empty)" : "(file not found)"}
              </pre>
            </div>
          ))}
        </section>
      )}

      {active === "screenshots" && (
        <section className="space-y-4">
          <p className="muted text-sm">
            Captured {LAST_UPDATED.split(" ")[0]} with Playwright. Click any image to magnify —
            then scroll, zoom with +/− or mouse-wheel buttons, and use ← → keys to flip through.
          </p>
          <div className="grid md:grid-cols-2 gap-4">
            {SCREENSHOTS.map((shot, i) => (
              <figure key={shot.src} className="card p-3 space-y-2 cursor-zoom-in" onClick={() => openShot(i)}>
                {/* eslint-disable-next-line @next/next/no-img-element */}
                <img
                  src={shot.src}
                  alt={shot.caption}
                  className="rounded-lg border w-full hover:opacity-90 transition-opacity"
                  style={{ borderColor: "var(--brd)" }}
                />
                <figcaption className="muted text-xs">{shot.caption}</figcaption>
              </figure>
            ))}
          </div>
        </section>
      )}

      {/* ---------- full-screen viewer ---------- */}
      {viewer !== null && (
        <div
          className="fixed inset-0 z-50 bg-black/85 flex flex-col"
          onClick={(e) => e.target === e.currentTarget && setViewer(null)}
        >
          <div className="flex items-center justify-between px-4 py-2 text-white text-sm">
            <span>
              {viewer + 1}/{SCREENSHOTS.length} · {SCREENSHOTS[viewer].caption} · zoom{" "}
              {Math.round(zoom * 100)}%
            </span>
            <span className="flex items-center gap-2">
              <button onClick={() => setViewer((v) => ((v ?? 0) - 1 + SCREENSHOTS.length) % SCREENSHOTS.length)} className="btn-ghost !py-1">
                ←
              </button>
              <button onClick={() => setZoom((z) => Math.max(0.5, z - 0.25))} className="btn-ghost !py-1">
                −
              </button>
              <button onClick={() => setZoom(1)} className="btn-ghost !py-1">
                reset
              </button>
              <button onClick={() => setZoom((z) => Math.min(4, z + 0.25))} className="btn-ghost !py-1">
                +
              </button>
              <button onClick={() => setViewer((v) => ((v ?? 0) + 1) % SCREENSHOTS.length)} className="btn-ghost !py-1">
                →
              </button>
              <button onClick={() => setViewer(null)} className="btn-primary !py-1">
                ✕ close
              </button>
            </span>
          </div>
          <div className="flex-1 overflow-auto p-4">
            {/* eslint-disable-next-line @next/next/no-img-element */}
            <img
              src={SCREENSHOTS[viewer].src}
              alt={SCREENSHOTS[viewer].caption}
              style={{ width: `${zoom * 100}%`, maxWidth: "none" }}
              className="mx-auto rounded-lg shadow-2xl block"
            />
          </div>
        </div>
      )}
    </div>
  );
}
