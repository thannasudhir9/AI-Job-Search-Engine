"use client";

import { AnimatePresence, motion } from "framer-motion";
import { Cpu, Plus, RefreshCw, Star, Trash2 } from "lucide-react";
import { useCallback, useEffect, useState } from "react";
import { toast } from "sonner";
import { api, CompanyRow, Status } from "@/lib/api";

export default function SourcesPage() {
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
      toast.success(`Synced ${r.companies_synced} sources · ${r.jobs_new} new jobs`);
      setMessage(
        `Synced ${r.companies_synced} sources · ${r.jobs_fetched} fetched · ${r.jobs_new} new` +
        (r.errors.length ? ` · ${r.errors.length} errors` : ""),
      );
      await refresh();
    } catch (e) {
      toast.error(`Sync failed: ${(e as Error).message}`);
      setMessage(`Sync failed: ${(e as Error).message}`);
    } finally {
      setSyncing(false);
    }
  };

  const addCompany = async () => {
    if (!name || !slug) return;
    try {
      await api.addCompany(name, source, slug);
      toast.success(`${name} added — will sync on next cycle`);
      setName(""); setSlug("");
      await refresh();
    } catch (e) { toast.error((e as Error).message); }
  };

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-3xl font-bold tracking-tight flex items-center gap-2">
          <RefreshCw className="text-indigo-500" size={26} /> Sources
        </h1>
        <p className="muted text-sm mt-1">
          Where your jobs come from. Boards auto-sync every {status?.sync_interval_hours ?? 4}h.
        </p>
      </div>

      {/* stat strip */}
      <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
        {[
          { label: "Jobs in database", value: status?.jobs ?? "–" },
          { label: "Active matches", value: status?.matches ?? "–" },
          { label: "Tracked applications", value: status?.applications ?? "–" },
          { label: "Sources watched", value: companies.length },
        ].map((s) => (
          <div key={s.label} className="card p-5">
            <div className="text-3xl font-semibold">{s.value}</div>
            <div className="muted text-sm mt-1">{s.label}</div>
          </div>
        ))}
      </div>

      {/* sync */}
      <section className="card p-5 flex items-center justify-between gap-4 flex-wrap">
        <div>
          <h2 className="font-semibold">Sync now</h2>
          <p className="muted text-sm mt-0.5">Pulls fresh jobs from all enabled sources.</p>
        </div>
        <button onClick={sync} disabled={syncing} className="btn-primary inline-flex items-center gap-2">
          <RefreshCw size={15} className={syncing ? "animate-spin" : ""} />
          {syncing ? "Syncing…" : "Sync now"}
        </button>
      </section>
      {message && <p className="muted text-sm -mt-2">{message}</p>}

      {/* watchlist */}
      <section className="card p-5">
        <h2 className="font-semibold mb-1">Watched sources ({companies.length})</h2>
        <p className="muted text-sm">
          Greenhouse / Lever / Ashby board slugs, the Salesforce CDN feed and LinkedIn searches.
          Find slugs in a company&apos;s careers URL.
        </p>

        <div className="mt-4 flex flex-wrap gap-2 items-center">
          <input className="input w-44" value={name} onChange={(e) => setName(e.target.value)} placeholder="Display name" />
          <select className="input !w-auto" value={source} onChange={(e) => setSource(e.target.value)}>
            <option value="greenhouse">greenhouse</option>
            <option value="lever">lever</option>
            <option value="ashby">ashby</option>
            <option value="salesforce">salesforce</option>
            <option value="linkedin">linkedin*</option>
          </select>
          <input
            className="input w-56" value={slug} onChange={(e) => setSlug(e.target.value)}
            placeholder={source === "linkedin" ? "keywords|location" : "board slug"}
          />
          <button onClick={addCompany} className="btn-primary inline-flex items-center gap-1.5">
            <Plus size={15} /> Add source
          </button>
          {source === "linkedin" && (
            <span className="muted text-xs">* linkedin slug format: keywords|location</span>
          )}
        </div>

        <ul className="mt-4 divide-y" style={{ borderColor: "var(--brd)" }}>
          <AnimatePresence initial={false}>
            {companies.map((c) => (
              <motion.li
                key={c.id}
                layout
                initial={{ opacity: 0 }}
                animate={{ opacity: 1 }}
                exit={{ opacity: 0 }}
                className="flex items-center justify-between gap-3 py-2.5 text-sm"
                style={{ borderColor: "var(--brd)" }}
              >
                <span className="flex items-center gap-2 min-w-0">
                  {c.priority && <Star size={14} className="text-amber-400 fill-amber-400 shrink-0" />}
                  <span className="font-medium truncate">{c.name}</span>
                  <span className="chip font-mono">{c.source}/{c.slug}</span>
                </span>
                <span className="flex items-center gap-4 shrink-0">
                  <span className="muted">{c.job_count.toLocaleString()} jobs</span>
                  {c.last_synced_at && (
                    <span className="muted hidden md:inline text-xs">
                      {new Date(c.last_synced_at).toLocaleTimeString([], { hour: "2-digit", minute: "2-digit" })}
                    </span>
                  )}
                  <button
                    onClick={async () => {
                      await api.removeCompany(c.id);
                      toast.success("Source removed");
                      await refresh();
                    }}
                    className="muted hover:text-red-500"
                    title="Remove"
                  >
                    <Trash2 size={15} />
                  </button>
                </span>
              </motion.li>
            ))}
          </AnimatePresence>
        </ul>
      </section>

      {/* AI status */}
      <section className="card p-5 border-emerald-500/25 bg-emerald-500/[0.05]">
        <h2 className="font-semibold flex items-center gap-2"><Cpu size={17} className="text-emerald-500" /> AI status</h2>
        <p className="muted mt-1 text-sm">
          {status === null
            ? "Checking…"
            : status.ollama_available
              ? `Ollama connected (${status.ollama_models.join(", ")}) — full AI rewriting + semantic matching active.`
              : "Ollama not detected — keyword matching & template tailoring are active. Run `ollama pull llama3.1 nomic-embed-text` then restart the backend for full AI mode."}
        </p>
      </section>
    </div>
  );
}
