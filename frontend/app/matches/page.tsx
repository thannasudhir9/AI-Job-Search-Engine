"use client";

import { useCallback, useEffect, useState } from "react";
import { api, JobMatch } from "@/lib/api";

const ROLE_OPTIONS = [
  { value: "", label: "All roles" },
  { value: "fde", label: "Forward Deployed Engineer" },
  { value: "pm", label: "Project / Program Manager" },
  { value: "solutions", label: "Solutions Engineer / Architect" },
  { value: "architecture", label: "Technical Architect" },
  { value: "implementation", label: "Implementation / Prof. Services" },
  { value: "field", label: "Field Engineering" },
];

const COUNTRY_OPTIONS = ["Germany", "Netherlands", "Switzerland", "UAE"];

const SCORE_OPTIONS = [
  { value: "", label: "Any score" },
  { value: "70", label: "70+ / 100  (strong)" },
  { value: "50", label: "50+ / 100  (good)" },
  { value: "30", label: "30+ / 100" },
  { value: "15", label: "15+ / 100" },
];

const CURRENCY_SYMBOLS: Record<string, string> = {
  EUR: "€",
  USD: "$",
  GBP: "£",
  CHF: "CHF ",
  AED: "AED ",
};

function fmtSalary(
  min: number | null,
  max: number | null,
  currency?: string | null,
) {
  if (!min && !max) return "";
  const sym = CURRENCY_SYMBOLS[currency || "EUR"] ?? `${currency} `;
  const fmt = (n: number) => (n >= 1000 ? `${Math.round(n / 1000)}k` : String(n));
  if (min && max && min !== max) return `${sym}${fmt(min)} – ${sym}${fmt(max)}`;
  return `${sym}${fmt((max ?? min) as number)}`;
}

function ScoreBadge({ score }: { score: number | null }) {
  if (score === null) return null;
  const cls =
    score >= 70 ? "score-hi" :
    score >= 50 ? "score-mid" :
                  "score-lo";
  return (
    <span className={`inline-block rounded-lg px-2.5 py-1 text-sm font-semibold ${cls}`}>
      {Math.round(score)}/100
    </span>
  );
}

export default function MatchesPage() {
  const [jobs, setJobs] = useState<JobMatch[]>([]);
  const [countries, setCountries] = useState<string[]>(COUNTRY_OPTIONS);
  const [companies, setCompanies] = useState<string[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");
  const [busyId, setBusyId] = useState<number | null>(null);

  // filters
  const [q, setQ] = useState("");
  const [country, setCountry] = useState("");
  const [role, setRole] = useState("");
  const [company, setCompany] = useState("");
  const [minSalary, setMinSalary] = useState("");
  const [minScore, setMinScore] = useState("");

  const load = useCallback(async () => {
    setLoading(true);
    try {
      setJobs(
        await api.matches({
          limit: 500,
          country,
          role,
          company,
          min_salary: Number(minSalary) || 0,
          min_score: Number(minScore) || 0,
        }),
      );
      setError("");
    } catch (e) {
      setError((e as Error).message);
    } finally {
      setLoading(false);
    }
  }, [country, role, company, minSalary, minScore]);

  useEffect(() => {
    load();
  }, [load]);

  useEffect(() => {
    api
      .facets()
      .then((f) => {
        if (f.countries.length) setCountries(f.countries);
        setCompanies(f.companies);
      })
      .catch(() => {});
  }, []);

  const dismiss = async (id: number) => {
    setBusyId(id);
    await api.dismissMatch(id).catch(() => {});
    await load();
    setBusyId(null);
  };

  const track = async (id: number) => {
    setBusyId(id);
    await api.trackJob(id, "draft").catch((e) => setError(e.message));
    await load();
    setBusyId(null);
  };

  const filtered = jobs.filter(
    (j) =>
      !q ||
      `${j.title} ${j.company_name} ${j.location}`.toLowerCase().includes(q.toLowerCase()),
  );

  const activeFilters = country || role || company || minSalary || minScore;

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-2xl font-semibold">Matches</h1>
        <p className="muted text-sm mt-1">
          Scored 0–100 against your profile. Filter by score, country, role, salary or company.
        </p>
      </div>

      <div className="card p-4">
        <div className="grid grid-cols-2 md:grid-cols-6 gap-2.5">
          <select
            className="input"
            value={minScore}
            onChange={(e) => setMinScore(e.target.value)}
            aria-label="Minimum score"
          >
            {SCORE_OPTIONS.map((s) => (
              <option key={s.value} value={s.value}>
                ⭐ {s.label}
              </option>
            ))}
          </select>

          <select
            className="input"
            value={country}
            onChange={(e) => setCountry(e.target.value)}
            aria-label="Country"
          >
            <option value="">🌍 All countries</option>
            {countries.map((c) => (
              <option key={c} value={c}>
                {c}
              </option>
            ))}
          </select>

          <select
            className="input"
            value={role}
            onChange={(e) => setRole(e.target.value)}
            aria-label="Role"
          >
            {ROLE_OPTIONS.map((r) => (
              <option key={r.value} value={r.value}>
                {r.label}
              </option>
            ))}
          </select>

          <select
            className="input"
            value={company}
            onChange={(e) => setCompany(e.target.value)}
            aria-label="Company"
          >
            <option value="">🏢 All companies</option>
            {companies.map((c) => (
              <option key={c} value={c}>
                {c}
              </option>
            ))}
          </select>

          <input
            type="number"
            inputMode="numeric"
            className="input"
            placeholder="Min salary (as posted)"
            value={minSalary}
            onChange={(e) => setMinSalary(e.target.value.replace(/\D/g, ""))}
            aria-label="Minimum salary"
          />

          <input
            className="input"
            placeholder="Search title / company…"
            value={q}
            onChange={(e) => setQ(e.target.value)}
            aria-label="Search"
          />
        </div>
        <div className="flex items-center justify-between mt-3 text-xs muted">
          <span>
            {loading ? "Loading…" : `${filtered.length} job${filtered.length === 1 ? "" : "s"}`}
          </span>
          {activeFilters && (
            <button
              onClick={() => {
                setCountry("");
                setRole("");
                setCompany("");
                setMinSalary("");
                setMinScore("");
              }}
              className="hover:text-indigo-500 underline"
            >
              clear filters
            </button>
          )}
        </div>
      </div>

      {error && (
        <p className="rounded-lg bg-red-500/10 border border-red-500/30 px-4 py-2 text-sm text-red-500 dark:text-red-300">
          {error}
        </p>
      )}
      {!loading && filtered.length === 0 && (
        <p className="muted">
          No matches for these filters — try widening them or run a sync from the Dashboard.
        </p>
      )}

      <ul className="space-y-3">
        {filtered.map((j) => {
          const salary = fmtSalary(j.salary_min, j.salary_max, j.salary_currency);
          return (
            <li key={j.id} className="card p-4 transition-colors hover:border-[var(--card-hover-brd)]">
              <div className="flex items-start justify-between gap-4">
                <div className="min-w-0">
                  <a
                    href={j.url || "#"}
                    target="_blank"
                    rel="noreferrer"
                    className="font-medium hover:text-indigo-500"
                  >
                    {j.title}
                  </a>
                  <div className="muted text-sm mt-0.5 flex flex-wrap gap-x-2">
                    <span>{j.company_name}</span>
                    {j.location && <span>· {j.location}</span>}
                    {j.country && <span className="chip">{j.country}</span>}
                    {salary && <span className="text-emerald-600 dark:text-emerald-400">💰 {salary}</span>}
                    <span className="uppercase text-xs tracking-wide">{j.source}</span>
                  </div>
                  {j.reasons.length > 0 && (
                    <div className="mt-2 flex flex-wrap gap-1.5">
                      {j.reasons.slice(0, 4).map((r, i) => (
                        <span key={i} className="chip muted" style={{ background: "var(--hover)", color: "var(--muted)" }}>
                          {r}
                        </span>
                      ))}
                    </div>
                  )}
                </div>
                <div className="shrink-0 flex flex-col items-end gap-2">
                  <ScoreBadge score={j.score} />
                  <div className="flex gap-2 text-sm">
                    {j.applied ? (
                      <span className="rounded-lg border border-emerald-500/40 text-emerald-600 dark:text-emerald-300 px-3 py-1.5">
                        tracked ✓
                      </span>
                    ) : (
                      <>
                        <button
                          disabled={busyId === j.id}
                          onClick={() => track(j.id)}
                          className="btn-ghost !py-1.5"
                        >
                          Track
                        </button>
                        <a href={`/tailor/${j.id}`} className="btn-primary !py-1.5">
                          Tailor resume →
                        </a>
                        <button
                          disabled={busyId === j.id}
                          onClick={() => dismiss(j.id)}
                          className="btn-ghost !px-2 !py-1.5 hover:!text-red-500"
                          title="Dismiss"
                        >
                          ✕
                        </button>
                      </>
                    )}
                  </div>
                </div>
              </div>
            </li>
          );
        })}
      </ul>
    </div>
  );
}
