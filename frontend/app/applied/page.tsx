"use client";

import { useCallback, useEffect, useState } from "react";
import { api, ApplicationRow } from "@/lib/api";

const STATUS_STYLE: Record<string, string> = {
  draft: "score-lo",
  applied: "chip",
  interview: "score-mid",
  offer: "score-hi",
  rejected: "rounded-md px-2 py-0.5 text-xs bg-red-500/15 text-red-500 dark:text-red-300",
};

export default function AppliedPage() {
  const [apps, setApps] = useState<ApplicationRow[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");
  const [filter, setFilter] = useState("");

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

  const shown = filter ? apps.filter((a) => a.status === filter) : apps;
  const appliedCount = apps.filter((a) => a.status !== "draft").length;

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-2xl font-semibold">Applied jobs</h1>
        <p className="muted text-sm mt-1">
          {appliedCount} submitted · each with the tailored resume that was sent.
        </p>
      </div>

      <div className="flex flex-wrap gap-2">
        {[["", "All"], ["applied", "Applied"], ["interview", "Interview"], ["offer", "Offer"], ["rejected", "Rejected"], ["draft", "Drafts"]].map(
          ([value, label]) => (
            <button
              key={value}
              onClick={() => setFilter(value)}
              className={filter === value ? "btn-primary !py-1.5" : "btn-ghost !py-1.5"}
            >
              {label}
              {` (${apps.filter((a) => (!value ? true : a.status === value)).length})`}
            </button>
          ),
        )}
      </div>

      {error && (
        <p className="rounded-lg bg-red-500/10 border border-red-500/30 px-4 py-2 text-sm text-red-500 dark:text-red-300">
          {error}
        </p>
      )}
      {loading && <p className="muted">Loading…</p>}
      {!loading && shown.length === 0 && (
        <p className="muted">
          Nothing here yet — track jobs from the{" "}
          <a href="/matches" className="text-indigo-500 underline">
            Matches
          </a>{" "}
          page.
        </p>
      )}

      <ul className="space-y-3">
        {shown.map((a) => (
          <li key={a.id} className="card p-4">
            <div className="flex items-start justify-between gap-4 flex-wrap">
              <div className="min-w-0">
                <div className="flex items-center gap-2 flex-wrap">
                  <span
                    className={`inline-block rounded-md px-2 py-0.5 text-xs font-medium ${STATUS_STYLE[a.status] ?? "chip"}`}
                  >
                    {a.status.toUpperCase()}
                  </span>
                  <a
                    href={a.job_url || "#"}
                    target="_blank"
                    rel="noreferrer"
                    className="font-medium hover:text-indigo-500"
                  >
                    {a.job_title || `Job #${a.job_id}`}
                  </a>
                </div>
                <div className="muted text-sm mt-1">
                  {a.company_name}
                  {a.updated_at && (
                    <span>
                      {" "}
                      · updated {new Date(a.updated_at).toLocaleDateString()}
                    </span>
                  )}
                  <span> · {a.events.length} events</span>
                </div>
              </div>
              <div className="flex gap-2 text-sm items-center flex-wrap">
                {a.resume_pdf_url ? (
                  <>
                    <span className="muted text-xs">
                      via <code className="font-mono">{a.resume_model}</code>
                    </span>
                    <a
                      href={`http://localhost:8000${a.resume_pdf_url}`}
                      target="_blank"
                      rel="noreferrer"
                      className="btn-ghost !py-1.5"
                    >
                      📄 Resume PDF
                    </a>
                    <a href={`/tailor/${a.job_id}`} className="btn-primary !py-1.5">
                      Open tailored
                    </a>
                  </>
                ) : (
                  <span className="muted text-xs">no tailored resume yet</span>
                )}
              </div>
            </div>
          </li>
        ))}
      </ul>
    </div>
  );
}
