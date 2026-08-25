"use client";

import { AnimatePresence, motion } from "framer-motion";
import {
  Banknote,
  BookmarkPlus,
  Building2,
  CalendarDays,
  FilterX,
  Globe2,
  MapPin,
  Search,
  Sparkles,
  X,
} from "lucide-react";
import { useCallback, useEffect, useMemo, useState } from "react";
import { toast } from "sonner";
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

const SCORE_OPTIONS = [
  { value: "", label: "Any score" },
  { value: "70", label: "70+ strong" },
  { value: "50", label: "50+ good" },
  { value: "30", label: "30+" },
  { value: "15", label: "15+" },
];

const SORT_OPTIONS = [
  { value: "score", label: "Best match" },
  { value: "newest", label: "Newest first" },
  { value: "salary", label: "Highest salary" },
];

const FLAGS: Record<string, string> = {
  Germany: "🇩🇪",
  Netherlands: "🇳🇱",
  Switzerland: "🇨🇭",
  UAE: "🇦🇪",
};

const CURRENCY_SYMBOLS: Record<string, string> = {
  EUR: "€", USD: "$", GBP: "£", CHF: "CHF ", AED: "AED ",
};

function fmtSalary(min: number | null, max: number | null, currency?: string | null) {
  if (!min && !max) return "";
  const sym = CURRENCY_SYMBOLS[currency || "EUR"] ?? `${currency} `;
  const fmt = (n: number) => (n >= 1000 ? `${Math.round(n / 1000)}k` : String(n));
  if (min && max && min !== max) return `${sym}${fmt(min)} – ${sym}${fmt(max)}`;
  return `${sym}${fmt((max ?? min) as number)}`;
}

function relDate(iso?: string | null) {
  if (!iso) return "";
  const days = Math.floor((Date.now() - new Date(iso).getTime()) / 86400000);
  if (days <= 0) return "today";
  if (days === 1) return "1d ago";
  if (days < 30) return `${days}d ago`;
  return new Date(iso).toLocaleDateString();
}

function avatarColor(name: string) {
  let h = 0;
  for (let i = 0; i < name.length; i++) h = (h * 31 + name.charCodeAt(i)) % 360;
  return `hsl(${h} 55% 42%)`;
}

function ScoreBadge({ score }: { score: number | null }) {
  if (score === null) return null;
  const cls =
    score >= 70 ? "score-hi" :
    score >= 50 ? "score-mid" :
    "score-lo";
  return (
    <span className={`inline-flex items-center gap-1 rounded-full px-2.5 py-1 text-xs font-bold ${cls}`}>
      <Sparkles size={12} /> {Math.round(score)}/100
    </span>
  );
}

function Skeletons() {
  return (
    <div className="space-y-3">
      {Array.from({ length: 6 }).map((_, i) => (
        <div key={i} className="card p-4 animate-pulse">
          <div className="flex gap-3">
            <div className="h-10 w-10 rounded-lg bg-black/10 dark:bg-white/10" />
            <div className="flex-1 space-y-2">
              <div className="h-4 w-2/3 rounded bg-black/10 dark:bg-white/10" />
              <div className="h-3 w-1/3 rounded bg-black/10 dark:bg-white/10" />
            </div>
            <div className="h-8 w-16 rounded bg-black/10 dark:bg-white/10" />
          </div>
        </div>
      ))}
    </div>
  );
}

export default function JobSearchEngine() {
  const [jobs, setJobs] = useState<JobMatch[]>([]);
  const [countries, setCountries] = useState<string[]>(Object.keys(FLAGS));
  const [companies, setCompanies] = useState<string[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");
  const [busyId, setBusyId] = useState<number | null>(null);

  const [q, setQ] = useState("");
  const [country, setCountry] = useState("");
  const [role, setRole] = useState("");
  const [company, setCompany] = useState("");
  const [minSalary, setMinSalary] = useState("");
  const [minScore, setMinScore] = useState("");
  const [sort, setSort] = useState("score");

  const load = useCallback(async () => {
    setLoading(true);
    try {
      setJobs(
        await api.matches({
          limit: 500, country, role, company, sort,
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
  }, [country, role, company, minSalary, minScore, sort]);

  useEffect(() => { load(); }, [load]);

  useEffect(() => {
    api.facets().then((f) => {
      if (f.countries.length) setCountries(f.countries);
      setCompanies(f.companies);
    }).catch(() => {});
  }, []);

  const dismiss = async (id: number) => {
    setBusyId(id);
    try {
      await api.dismissMatch(id);
      toast.success("Job dismissed");
      await load();
    } catch (e) { toast.error(`Dismiss failed: ${(e as Error).message}`); }
    setBusyId(null);
  };

  const track = async (id: number) => {
    setBusyId(id);
    try {
      await api.trackJob(id, "draft");
      toast.success("Added to tracker");
      await load();
    } catch (e) { toast.error((e as Error).message); }
    setBusyId(null);
  };

  const filtered = useMemo(
    () =>
      jobs.filter(
        (j) =>
          !q ||
          `${j.title} ${j.company_name} ${j.location}`.toLowerCase().includes(q.toLowerCase()),
      ),
    [jobs, q],
  );

  const activeChips: { key: string; label: string; clear: () => void }[] = [];
  if (country) activeChips.push({ key: "c", label: `🌍 ${country}`, clear: () => setCountry("") });
  if (role) activeChips.push({ key: "r", label: ROLE_OPTIONS.find((o) => o.value === role)?.label ?? role, clear: () => setRole("") });
  if (company) activeChips.push({ key: "co", label: `🏢 ${company}`, clear: () => setCompany("") });
  if (minSalary) activeChips.push({ key: "s", label: `💰 ≥ ${Number(minSalary).toLocaleString()}`, clear: () => setMinSalary("") });
  if (minScore) activeChips.push({ key: "sc", label: `⭐ ${minScore}+/100`, clear: () => setMinScore("") });
  if (q) activeChips.push({ key: "q", label: `"${q}"`, clear: () => setQ("") });

  return (
    <div className="space-y-5">
      {/* header */}
      <div className="flex items-end justify-between gap-4 flex-wrap">
        <div>
          <h1 className="text-3xl font-bold tracking-tight flex items-center gap-2">
            <Search className="text-indigo-500" size={28} /> Job Search Engine
          </h1>
          <p className="muted text-sm mt-1">
            {loading ? "Scoring your job pool…" : `${filtered.length} ranked opportunities out of ${jobs.length} loaded · scored against your profile`}
          </p>
        </div>
        <select className="input !w-auto" value={sort} onChange={(e) => setSort(e.target.value)} aria-label="Sort">
          {SORT_OPTIONS.map((o) => (
            <option key={o.value} value={o.value}>↕ {o.label}</option>
          ))}
        </select>
      </div>

      {/* filter bar */}
      <div className="card p-4 space-y-3 sticky top-16 z-[5] backdrop-blur-md" style={{ background: "var(--header-bg)" }}>
        <div className="grid grid-cols-2 md:grid-cols-6 gap-2.5">
          <label className="relative md:col-span-2">
            <Search size={15} className="absolute left-3 top-1/2 -translate-y-1/2 muted pointer-events-none" />
            <input
              className="input w-full !pl-9"
              placeholder="Search title or company…"
              value={q}
              onChange={(e) => setQ(e.target.value)}
            />
          </label>
          <select className="input" value={country} onChange={(e) => setCountry(e.target.value)} aria-label="Country">
            <option value="">🌍 All countries</option>
            {countries.map((c) => <option key={c} value={c}>{FLAGS[c] ?? "🌍"} {c}</option>)}
          </select>
          <select className="input" value={role} onChange={(e) => setRole(e.target.value)} aria-label="Role">
            {ROLE_OPTIONS.map((o) => <option key={o.value} value={o.value}>{o.label}</option>)}
          </select>
          <select className="input" value={company} onChange={(e) => setCompany(e.target.value)} aria-label="Company">
            <option value="">🏢 All companies</option>
            {companies.map((c) => <option key={c} value={c}>{c}</option>)}
          </select>
          <input
            type="number" inputMode="numeric" className="input"
            placeholder="Min salary" value={minSalary}
            onChange={(e) => setMinSalary(e.target.value.replace(/\D/g, ""))}
            aria-label="Minimum salary"
          />
        </div>
        <div className="flex items-center gap-2 flex-wrap text-xs">
          <FilterX size={14} className="muted" />
          <select className="input !py-1 !text-xs !w-auto" value={minScore} onChange={(e) => setMinScore(e.target.value)} aria-label="Minimum score">
            {SCORE_OPTIONS.map((o) => <option key={o.value} value={o.value}>{o.label}</option>)}
          </select>
          <AnimatePresence>
            {activeChips.map((chip) => (
              <motion.span
                key={chip.key}
                initial={{ opacity: 0, scale: 0.85 }}
                animate={{ opacity: 1, scale: 1 }}
                exit={{ opacity: 0, scale: 0.85 }}
                className="inline-flex items-center gap-1 rounded-full px-2.5 py-1 font-medium"
                style={{ background: "var(--chip)", color: "var(--chip-fg)" }}
              >
                {chip.label}
                <button onClick={chip.clear} className="hover:text-red-500"><X size={11} /></button>
              </motion.span>
            ))}
          </AnimatePresence>
          {activeChips.length > 0 && (
            <button
              onClick={() => { setCountry(""); setRole(""); setCompany(""); setMinSalary(""); setMinScore(""); setQ(""); }}
              className="muted underline hover:text-red-500"
            >
              clear all
            </button>
          )}
        </div>
      </div>

      {error && (
        <p className="rounded-lg bg-red-500/10 border border-red-500/30 px-4 py-2 text-sm text-red-500 dark:text-red-300">{error}</p>
      )}

      {loading ? (
        <Skeletons />
      ) : filtered.length === 0 ? (
        <div className="card p-12 text-center space-y-2">
          <Globe2 className="mx-auto muted" size={36} />
          <p className="font-medium">No jobs match these filters</p>
          <p className="muted text-sm">Try widening them, or run a sync from Sources.</p>
        </div>
      ) : (
        <motion.ul layout className="space-y-3">
          <AnimatePresence mode="popLayout">
            {filtered.map((j, i) => {
              const salary = fmtSalary(j.salary_min, j.salary_max, j.salary_currency);
              const initials = j.company_name.slice(0, 2).toUpperCase();
              return (
                <motion.li
                  key={j.id}
                  layout
                  initial={{ opacity: 0, y: 14 }}
                  animate={{ opacity: 1, y: 0 }}
                  exit={{ opacity: 0, scale: 0.97 }}
                  transition={{ duration: 0.22, delay: Math.min(i * 0.02, 0.4) }}
                  className="card p-4 transition-all hover:border-indigo-400/60 hover:shadow-lg"
                >
                  <div className="flex items-start justify-between gap-4">
                    <div className="flex gap-3 min-w-0">
                      <div
                        className="shrink-0 h-10 w-10 rounded-lg grid place-items-center text-white text-sm font-bold"
                        style={{ background: avatarColor(j.company_name) }}
                      >
                        {initials}
                      </div>
                      <div className="min-w-0">
                        <a
                          href={j.url || "#"} target="_blank" rel="noreferrer"
                          className="font-semibold leading-snug hover:text-indigo-500 line-clamp-2"
                        >
                          {j.title}
                        </a>
                        <div className="muted text-sm mt-0.5 flex items-center flex-wrap gap-x-2 gap-y-1">
                          <span className="inline-flex items-center gap-1"><Building2 size={13} />{j.company_name}</span>
                          {j.location && <span className="inline-flex items-center gap-1"><MapPin size={13} />{j.location}</span>}
                          {j.country && <span>{FLAGS[j.country] ?? "🌍"} {j.country}</span>}
                          {j.posted_at && <span className="inline-flex items-center gap-1"><CalendarDays size={13} />{relDate(j.posted_at)}</span>}
                          {salary && (
                            <span className="inline-flex items-center gap-1 font-medium text-emerald-600 dark:text-emerald-400">
                              <Banknote size={13} />{salary}
                            </span>
                          )}
                          <span className="uppercase text-[10px] tracking-widest muted border rounded px-1.5 py-0.5" style={{ borderColor: "var(--brd)" }}>{j.source}</span>
                        </div>
                        {(j.scam_flags?.length > 0 || j.work_auth_flags?.length > 0) && (
                          <div className="mt-1.5 flex flex-wrap gap-1.5">
                            {j.scam_flags.map((f) => (
                              <span key={f} className="rounded-md px-2 py-0.5 text-[11px] font-medium bg-red-500/15 text-red-500 dark:text-red-300">⚠ {f}</span>
                            ))}
                            {j.work_auth_flags.map((f) => (
                              <span key={f} className="rounded-md px-2 py-0.5 text-[11px] font-medium bg-amber-500/15 text-amber-600 dark:text-amber-300">🛂 {f}</span>
                            ))}
                          </div>
                        )}
                        {j.reasons.length > 0 && (
                          <div className="mt-2 flex flex-wrap gap-1.5">
                            {j.reasons.slice(0, 3).map((r, k) => (
                              <span key={k} className="chip" style={{ background: "var(--hover)", color: "var(--muted)" }}>{r}</span>
                            ))}
                          </div>
                        )}
                      </div>
                    </div>
                    <div className="shrink-0 flex flex-col items-end gap-2">
                      <ScoreBadge score={j.score} />
                      <div className="flex gap-2 text-sm">
                        {j.applied ? (
                          <span className="rounded-lg border border-emerald-500/40 text-emerald-600 dark:text-emerald-300 px-3 py-1.5 text-xs font-medium inline-flex items-center gap-1">
                            <BookmarkPlus size={13} /> tracked ✓
                          </span>
                        ) : (
                          <>
                            <button disabled={busyId === j.id} onClick={() => track(j.id)} className="btn-ghost !py-1.5 !text-xs">
                              Track
                            </button>
                            <a href={`/tailor/${j.id}`} className="btn-primary !py-1.5 !text-xs">Tailor resume →</a>
                            <button
                              disabled={busyId === j.id} onClick={() => dismiss(j.id)}
                              className="btn-ghost !px-2 !py-1.5 hover:!text-red-500" title="Dismiss"
                            >
                              <X size={13} />
                            </button>
                          </>
                        )}
                      </div>
                    </div>
                  </div>
                </motion.li>
              );
            })}
          </AnimatePresence>
        </motion.ul>
      )}
    </div>
  );
}
