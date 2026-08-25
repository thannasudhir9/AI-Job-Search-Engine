"use client";

import { useCallback, useEffect, useState } from "react";
import { api, ApplicationRow } from "@/lib/api";

const COLUMNS = [
  { key: "draft", label: "Draft", accent: "#71717a" },
  { key: "applied", label: "Applied", accent: "#6366f1" },
  { key: "interview", label: "Interview", accent: "#f59e0b" },
  { key: "offer", label: "Offer", accent: "#10b981" },
  { key: "rejected", label: "Rejected", accent: "#ef4444" },
];

export default function TrackerPage() {
  const [apps, setApps] = useState<ApplicationRow[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");

  const load = useCallback(async () => {
    try {
      setApps(await api.applications());
      setError("");
    } catch (e) {
      setError((e as Error).message);
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    load();
  }, [load]);

  const move = async (app: ApplicationRow, dir: -1 | 1) => {
    const idx = COLUMNS.findIndex((c) => c.key === app.status);
    const next = COLUMNS[Math.min(COLUMNS.length - 1, Math.max(0, idx + dir))];
    if (!next || next.key === app.status) return;
    await api.updateApplication(app.id, { status: next.key }).catch((e) => setError(e.message));
    await load();
  };

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-2xl font-semibold">Application tracker</h1>
        <p className="muted text-sm mt-1">
          Every job you&apos;re tracking, with its full history.
        </p>
      </div>

      {error && (
        <p className="rounded-lg bg-red-500/10 border border-red-500/30 px-4 py-2 text-sm text-red-500 dark:text-red-300">
          {error}
        </p>
      )}
      {loading && <p className="muted">Loading…</p>}

      <div className="grid grid-cols-2 md:grid-cols-5 gap-3 items-start">
        {COLUMNS.map((col) => {
          const items = apps.filter((a) => a.status === col.key);
          return (
            <div
              key={col.key}
              className="card p-3 min-h-40"
              style={{ borderTopColor: col.accent, borderTopWidth: 2 }}
            >
              <div className="flex justify-between text-sm font-medium mb-3">
                <span>{col.label}</span>
                <span className="muted">{items.length}</span>
              </div>
              <ul className="space-y-2">
                {items.map((a) => (
                  <li
                    key={a.id}
                    className="rounded-lg p-2.5 text-xs space-y-2"
                    style={{ background: "var(--input-bg)", border: "1px solid var(--brd)" }}
                  >
                    <div>
                      <a
                        href={a.job_url || "#"}
                        target="_blank"
                        rel="noreferrer"
                        className="font-medium leading-snug hover:text-indigo-500"
                      >
                        {a.job_title}
                      </a>
                      <div className="muted mt-0.5">{a.company_name}</div>
                    </div>
                    {a.events.length > 1 && (
                      <div className="text-[11px] muted">
                        {a.events.length} events · since{" "}
                        {new Date(a.events[0].at).toLocaleDateString()}
                      </div>
                    )}
                    <div className="flex gap-1.5">
                      <button onClick={() => move(a, -1)} className="btn-ghost !px-1.5 !py-0.5 !text-xs">
                        ◀
                      </button>
                      <button onClick={() => move(a, 1)} className="btn-ghost !px-1.5 !py-0.5 !text-xs">
                        ▶
                      </button>
                      <button
                        onClick={async () => {
                          await api.deleteApplication(a.id).catch((e) => setError(e.message));
                          await load();
                        }}
                        className="ml-auto muted hover:text-red-500 px-1"
                        title="Remove"
                      >
                        ✕
                      </button>
                    </div>
                  </li>
                ))}
                {items.length === 0 && <li className="muted text-xs pt-1">Nothing here yet.</li>}
              </ul>
            </div>
          );
        })}
      </div>
    </div>
  );
}
