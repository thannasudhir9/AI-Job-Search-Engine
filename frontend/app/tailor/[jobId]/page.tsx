"use client";

import Link from "next/link";
import { useParams } from "next/navigation";
import { useCallback, useEffect, useState } from "react";
import { api, JobMatch, pdfUrl } from "@/lib/api";

export default function TailorPage() {
  const params = useParams<{ jobId: string }>();
  const jobId = Number(params.jobId);

  const [content, setContent] = useState("");
  const [model, setModel] = useState("");
  const [job, setJob] = useState<JobMatch | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");

  const generate = useCallback(
    async (force: boolean) => {
      setLoading(true);
      setError("");
      try {
        const r = await api.tailor(jobId, force);
        setContent(r.content);
        setModel(r.model);
      } catch (e) {
        setError((e as Error).message);
      } finally {
        setLoading(false);
      }
    },
    [jobId],
  );

  useEffect(() => {
    (async () => {
      try {
        setJob((await api.job(jobId)) as JobMatch);
      } catch { /* non-fatal */ }
      await generate(false);
    })();
  }, [jobId, generate]);

  return (
    <div className="space-y-6">
      <div className="flex items-start justify-between gap-4 flex-wrap">
        <div>
          <Link href="/matches" className="text-sm text-indigo-500 hover:text-indigo-400">
            ← Back to matches
          </Link>
          <h1 className="text-2xl font-semibold mt-1">{job?.title ?? `Job #${jobId}`}</h1>
          <p className="muted text-sm mt-0.5">
            {job?.company_name}
            {job?.location ? ` · ${job.location}` : ""}
          </p>
        </div>
        <div className="flex gap-2">
          <button onClick={() => generate(true)} disabled={loading} className="btn-ghost">
            Regenerate
          </button>
          <a
            href={pdfUrl(jobId)}
            target="_blank"
            rel="noreferrer"
            className={`btn-primary ${content ? "" : "pointer-events-none opacity-40"}`}
          >
            Open PDF ↗
          </a>
        </div>
      </div>

      {model && (
        <p className="text-xs muted">
          Generated with: <code className="font-mono">{model}</code>
          {model.includes("fallback") && " — start Ollama for full AI rewriting."}
        </p>
      )}

      {error && (
        <p className="rounded-lg bg-red-500/10 border border-red-500/30 px-4 py-2 text-sm text-red-500 dark:text-red-300">
          {error}
        </p>
      )}
      {loading && <p className="muted">Generating tailored resume…</p>}

      {content && (
        <pre className="code-view whitespace-pre-wrap rounded-xl p-6 text-sm leading-relaxed font-mono max-h-[65vh] overflow-auto">
{content}
        </pre>
      )}
    </div>
  );
}
