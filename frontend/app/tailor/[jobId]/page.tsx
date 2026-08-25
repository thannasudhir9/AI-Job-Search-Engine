"use client";

import Link from "next/link";
import { useParams } from "next/navigation";
import { useCallback, useEffect, useState } from "react";
import { toast } from "sonner";
import { api, pdfUrl } from "@/lib/api";

export default function TailorPage() {
  const params = useParams<{ jobId: string }>();
  const jobId = Number(params.jobId);

  const [content, setContent] = useState("");
  const [model, setModel] = useState("");
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");

  // career-ops style extras
  const [cover, setCover] = useState<{ content: string; model: string; pdf_url: string } | null>(null);
  const [coverBusy, setCoverBusy] = useState(false);
  const [email, setEmail] = useState<{ subject: string; body: string; model: string } | null>(null);
  const [emailBusy, setEmailBusy] = useState(false);

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

  const [jobTitle, setJobTitle] = useState("");
  const [jobCompany, setJobCompany] = useState("");
  const [jobLocation, setJobLocation] = useState("");

  useEffect(() => {
    (async () => {
      try {
        const j = await api.job(jobId);
        setJobTitle(j.title);
        setJobCompany(j.company_name);
        setJobLocation(j.location);
      } catch { /* non-fatal */ }
      await generate(false);
    })();
  }, [jobId, generate]);

  const genCover = async () => {
    setCoverBusy(true);
    try {
      setCover(await api.coverLetter(jobId));
      toast.success("Cover letter ready");
    } catch (e) { toast.error((e as Error).message); }
    setCoverBusy(false);
  };

  const genEmail = async () => {
    setEmailBusy(true);
    try {
      setEmail(await api.outreachEmail(jobId));
      toast.success("Outreach draft ready");
    } catch (e) { toast.error((e as Error).message); }
    setEmailBusy(false);
  };

  return (
    <div className="space-y-6">
      <div className="flex items-start justify-between gap-4 flex-wrap">
        <div>
          <Link href="/matches" className="text-sm text-indigo-500 hover:text-indigo-400">
            ← Back to matches
          </Link>
          <h1 className="text-2xl font-semibold mt-1">{jobTitle || `Job #${jobId}`}</h1>
          <p className="muted text-sm mt-0.5">
            {jobCompany}
            {jobLocation ? ` · ${jobLocation}` : ""}
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
        <section className="space-y-4">
          <pre className="code-view whitespace-pre-wrap rounded-xl p-6 text-sm leading-relaxed font-mono max-h-[55vh] overflow-auto">
{content}
          </pre>

          {/* career-ops style extras */}
          <div className="flex gap-2 flex-wrap">
            <button onClick={genCover} disabled={coverBusy} className="btn-ghost inline-flex items-center gap-2">
              ✉ {coverBusy ? "Writing…" : "Generate cover letter"}
            </button>
            <button onClick={genEmail} disabled={emailBusy} className="btn-ghost inline-flex items-center gap-2">
              📧 {emailBusy ? "Drafting…" : "Draft outreach email"}
            </button>
          </div>

          {cover && (
            <div className="card p-5 space-y-3">
              <div className="flex items-center justify-between flex-wrap gap-2">
                <h3 className="font-semibold">✉ Cover letter <span className="chip ml-1">{cover.model}</span></h3>
                <a href={`http://localhost:8000${cover.pdf_url}`} target="_blank" rel="noreferrer" className="btn-primary !py-1.5 !text-xs">
                  Download PDF ↗
                </a>
              </div>
              <pre className="code-view whitespace-pre-wrap rounded-lg p-4 text-xs leading-relaxed max-h-72 overflow-auto font-mono">
{cover.content}
              </pre>
            </div>
          )}

          {email && (
            <div className="card p-5 space-y-3">
              <div className="flex items-center justify-between flex-wrap gap-2">
                <h3 className="font-semibold">📧 Outreach draft <span className="chip ml-1">{email.model}</span></h3>
                <button
                  onClick={() => {
                    navigator.clipboard.writeText(`Subject: ${email.subject}\n\n${email.body}`);
                    toast.success("Email copied to clipboard");
                  }}
                  className="btn-primary !py-1.5 !text-xs"
                >
                  Copy to clipboard
                </button>
              </div>
              <p className="text-sm"><strong>Subject:</strong> {email.subject}</p>
              <pre className="code-view whitespace-pre-wrap rounded-lg p-4 text-xs leading-relaxed max-h-72 overflow-auto font-mono">
{email.body}
              </pre>
              <p className="muted text-[11px]">Draft only — nothing is sent automatically.</p>
            </div>
          )}
        </section>
      )}
    </div>
  );
}
