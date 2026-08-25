"use client";

import { useCallback, useEffect, useState } from "react";
import { api, CompanyRow, Status } from "@/lib/api";

function Stat({ label, value, hint }: { label: string; value: number | string; hint?: string }) {
  return (
    <div className="card p-5">
      <div className="text-3xl font-semibold">{value}</div>
      <div className="muted text-sm mt-1">{label}</div>
      {hint && <div className="text-xs mt-1" style={{ color: "var(--muted)", opacity: 0.7 }}>{hint}</div>}
    </div>
  );
}

export default function Dashboard() {
  const [status, setStatus] = useState<Status | null>(null);
  const [companies, setCompanies] = useState<CompanyRow[]>([]);
  const [syncing, setSyncing] = useState(false);
  const [message, setMessage] = useState("");
  const [name, setName] = useState("");
  const [source, setSource] = useState("greenhouse");
  const [slug, setSlug] = useState("");

  const refresh = useCallback(async () => {
    setStatus(await api.status());
    setCompanies(await api.companies());
  }, []);

  useEffect(() => {
    refresh().catch((e) => setMessage(`Backend unreachable: ${e.message}`));
  }, [refresh]);

  const sync = async () => {
    setSyncing(true);
    setMessage("Syncing boards… (can take ~30s)");
    try {
      const r = await api.syncNow();
      setMessage(
        `Synced ${r.companies_synced} boards · ${r.jobs_fetched} jobs fetched · ${r.jobs_new} new` +
          (r.errors.length ? ` · errors: ${r.errors.slice(0, 2).join("; ")}` : ""),
      );
      await refresh();
    } catch (e) {
      setMessage(`Sync failed: ${(e as Error).message}`);
    } finally {
      setSyncing(false);
    }
  };

  const addCompany = async () => {
    if (!name || !slug) return;
    try {
      await api.addCompany(name, source, slug);
      setName("");
      setSlug("");
      await refresh();
    } catch (e) {
      setMessage((e as Error).message);
    }
  };

  return (
    <div className="space-y-8">
      <div>
        <h1 className="text-2xl font-semibold">Dashboard</h1>
        <p className="muted text-sm mt-1">
          Your local job agent. Boards sync every {status?.sync_interval_hours ?? 4}h.
        </p>
      </div>

      <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
        <Stat label="Jobs in database" value={status?.jobs ?? "–"} />
        <Stat label="Active matches" value={status?.matches ?? "–"} />
        <Stat label="Tracked applications" value={status?.applications ?? "–"} />
        <Stat label="Resumes uploaded" value={status?.resumes ?? "–"} />
      </div>

      <section className="card p-5">
        <div className="flex items-center justify-between gap-4 flex-wrap">
          <div>
            <h2 className="font-medium">Job board sync</h2>
            <p className="muted text-sm mt-1">
              Pulls fresh jobs from public Greenhouse / Lever / Ashby APIs.
            </p>
          </div>
          <button onClick={sync} disabled={syncing} className="btn-primary">
            {syncing ? "Syncing…" : "Sync now"}
          </button>
        </div>
        {message && <p className="muted text-sm mt-3">{message}</p>}
      </section>

      <section className="card p-5">
        <h2 className="font-medium">Watched companies ({companies.length})</h2>
        <p className="muted text-sm mt-1">
          Find the board slug on a company&apos;s careers page URL, e.g.
          <code className="mx-1 rounded px-1.5 py-0.5 font-mono text-xs" style={{ background: "var(--hover)" }}>
            boards.greenhouse.io/stripe → greenhouse / stripe
          </code>
        </p>
        <div className="mt-4 flex flex-wrap gap-2">
          <input
            className="input w-44"
            value={name}
            onChange={(e) => setName(e.target.value)}
            placeholder="Company name"
          />
          <select className="input" value={source} onChange={(e) => setSource(e.target.value)}>
            <option value="greenhouse">greenhouse</option>
            <option value="lever">lever</option>
            <option value="ashby">ashby</option>
          </select>
          <input
            className="input w-40"
            value={slug}
            onChange={(e) => setSlug(e.target.value)}
            placeholder="board slug"
          />
          <button onClick={addCompany} className="btn-ghost">
            Add
          </button>
        </div>
        <ul className="mt-4 divide-y" style={{ borderColor: "var(--brd)" }}>
          {companies.map((c) => (
            <li key={c.id} className="flex items-center justify-between py-2 text-sm" style={{ borderColor: "var(--brd)" }}>
              <span>
                <span className="font-medium">{c.name}</span>
                <span className="ml-2 text-xs uppercase tracking-wide muted">
                  {c.source}/{c.slug}
                </span>
              </span>
              <span className="flex items-center gap-4">
                <span className="muted">{c.job_count} jobs</span>
                <button
                  onClick={async () => {
                    await api.removeCompany(c.id);
                    await refresh();
                  }}
                  className="text-red-500/80 hover:text-red-500"
                >
                  remove
                </button>
              </span>
            </li>
          ))}
        </ul>
      </section>

      <section className="rounded-xl border border-emerald-500/25 p-5 bg-emerald-500/[0.06] dark:bg-emerald-500/[0.05]">
        <h2 className="font-medium">AI status</h2>
        <p className="muted mt-1 text-sm">
          {status === null
            ? "Checking…"
            : status.ollama_available
              ? `Ollama connected (${status.ollama_models.join(", ")}). Resume tailoring uses full AI rewriting + semantic matching.`
              : "Ollama not detected - the app works with keyword matching and template-based tailoring. Start Ollama (e.g. `ollama run llama3.1` and `ollama pull nomic-embed-text`) for AI rewriting."}
        </p>
      </section>
    </div>
  );
}
