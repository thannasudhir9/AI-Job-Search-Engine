"use client";

import { useCallback, useEffect, useRef, useState } from "react";
import { api, ProfileData, ResumeRow, TailorRow } from "@/lib/api";

const API = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

const EMPTY: ProfileData = {
  full_name: "",
  email: "",
  phone: "",
  location: "",
  summary: "",
  skills: [],
  desired_titles: [],
  preferred_locations: [],
  remote_ok: true,
};

function Field({
  label,
  value,
  onChange,
  placeholder,
}: {
  label: string;
  value: string;
  onChange: (v: string) => void;
  placeholder?: string;
}) {
  return (
    <label className="block">
      <span className="muted text-sm">{label}</span>
      <input
        className="input mt-1 w-full"
        value={value}
        onChange={(e) => onChange(e.target.value)}
        placeholder={placeholder}
      />
    </label>
  );
}

function ListField({
  label,
  values,
  onChange,
  placeholder,
}: {
  label: string;
  values: string[];
  onChange: (v: string[]) => void;
  placeholder?: string;
}) {
  const [input, setInput] = useState("");
  const add = () => {
    const v = input.trim();
    if (!v) return;
    onChange([...values, v]);
    setInput("");
  };
  return (
    <div>
      <span className="muted text-sm">{label}</span>
      <div className="mt-1 flex flex-wrap gap-1.5 input p-2" style={{ background: "var(--input-bg)" }}>
        {values.map((v, i) => (
          <span key={`${v}-${i}`} className="chip inline-flex items-center gap-1 !text-xs !py-0.5">
            {v}
            <button
              onClick={() => onChange(values.filter((_, j) => j !== i))}
              className="hover:text-red-400"
            >
              ✕
            </button>
          </span>
        ))}
        <input
          value={input}
          onChange={(e) => setInput(e.target.value)}
          onKeyDown={(e) => e.key === "Enter" && add()}
          onBlur={add}
          placeholder={values.length ? "" : (placeholder ?? "Type and press Enter…")}
          className="flex-1 min-w-32 bg-transparent px-1 py-0.5 text-sm outline-none"
          style={{ color: "var(--fg)" }}
        />
      </div>
    </div>
  );
}

export default function ProfilePage() {
  const [profile, setProfile] = useState<ProfileData>(EMPTY);
  const [resumes, setResumes] = useState<ResumeRow[]>([]);
  const [saving, setSaving] = useState(false);
  const [uploading, setUploading] = useState(false);
  const [message, setMessage] = useState("");
  const fileRef = useRef<HTMLInputElement>(null);
  const [masterText, setMasterText] = useState<string | null>(null);
  const [showMaster, setShowMaster] = useState(false);
  const [tailors, setTailors] = useState<TailorRow[]>([]);

  const refresh = useCallback(async () => {
    setProfile(await api.profile());
    setResumes(await api.resumes());
    setTailors(await api.tailorsList().catch(() => []));
  }, []);

  useEffect(() => {
    refresh().catch((e) => setMessage((e as Error).message));
  }, [refresh]);

  const toggleMaster = async () => {
    if (!showMaster && masterText === null) {
      try {
        const r = await api.masterResume();
        setMasterText(r.text);
      } catch (e) {
        setMasterText(`Could not load: ${(e as Error).message}`);
      }
    }
    setShowMaster((s) => !s);
  };

  const save = async () => {
    setSaving(true);
    try {
      await api.saveProfile(profile);
      setMessage("Profile saved — matches re-scored.");
    } catch (e) {
      setMessage(`Save failed: ${(e as Error).message}`);
    } finally {
      setSaving(false);
    }
  };

  const upload = async (file: File) => {
    setUploading(true);
    setMessage("");
    try {
      const form = new FormData();
      form.append("file", file);
      const res = await fetch(`${API}/api/resumes/upload`, {
        method: "POST",
        body: form,
      });
      if (!res.ok) throw new Error((await res.json()).detail ?? res.statusText);
      await refresh();
      setMessage(`Uploaded "${file.name}".`);
    } catch (e) {
      setMessage(`Upload failed: ${(e as Error).message}`);
    } finally {
      setUploading(false);
    }
  };

  const set =
    <K extends keyof ProfileData>(k: K) =>
    (v: ProfileData[K]) =>
      setProfile((p) => ({ ...p, [k]: v }));

  return (
    <div className="space-y-8">
      <div>
        <h1 className="text-2xl font-semibold">Profile &amp; resume</h1>
        <p className="muted text-sm mt-1">This drives matching and resume tailoring.</p>
      </div>

      <section className="card p-5 space-y-4">
        <h2 className="font-medium">Master resume</h2>
        <div
          onDragOver={(e) => e.preventDefault()}
          onDrop={(e) => {
            e.preventDefault();
            const f = e.dataTransfer.files?.[0];
            if (f) upload(f);
          }}
          onClick={() => fileRef.current?.click()}
          className="drop-zone cursor-pointer rounded-lg px-4 py-8 text-center text-sm"
        >
          {uploading ? "Parsing…" : "Drop your resume PDF here, or click to browse (.pdf / .txt)"}
        </div>
        <input
          ref={fileRef}
          type="file"
          accept=".pdf,.txt,.md"
          hidden
          onChange={(e) => e.target.files?.[0] && upload(e.target.files[0])}
        />
        <ul className="divide-y text-sm" style={{ borderColor: "var(--brd)" }}>
          {resumes.map((r) => (
            <li key={r.id} className="flex items-center justify-between py-2" style={{ borderColor: "var(--brd)" }}>
              <span>
                {r.name}{" "}
                {r.is_master && (
                  <span className="ml-1 rounded px-1.5 py-0.5 text-xs score-hi">master</span>
                )}
                <span className="ml-2 muted">{r.text_chars.toLocaleString()} chars</span>
              </span>
              <span className="flex gap-3 text-xs">
                {!r.is_master && (
                  <button
                    onClick={async () => {
                      await fetch(`${API}/api/resumes/${r.id}/set-master`, { method: "POST" });
                      await refresh();
                    }}
                    className="text-indigo-500 hover:text-indigo-400"
                  >
                    set as master
                  </button>
                )}
                <button
                  onClick={async () => {
                    await fetch(`${API}/api/resumes/${r.id}`, { method: "DELETE" });
                    await refresh();
                  }}
                  className="muted hover:text-red-500"
                >
                  delete
                </button>
              </span>
            </li>
          ))}
          {resumes.length === 0 && <li className="py-2 muted">No resumes uploaded yet.</li>}
        </ul>

        {resumes.some((r) => r.is_master) && (
          <div>
            <button onClick={toggleMaster} className="btn-ghost !py-1.5 !text-xs">
              {showMaster ? "Hide master resume" : "👁 View master resume text"}
            </button>
            {showMaster && masterText !== null && (
              <pre className="code-view mt-3 whitespace-pre-wrap rounded-lg p-4 text-xs leading-relaxed max-h-[420px] overflow-auto font-mono">
{masterText}
              </pre>
            )}
          </div>
        )}
      </section>

      <section className="card p-5">
        <h2 className="font-medium">Tailored resumes ({tailors.length})</h2>
        <p className="muted text-sm mt-1">
          Every job-specific resume generated so far — open the editable preview or download the PDF.
        </p>
        <ul className="mt-3 divide-y text-sm" style={{ borderColor: "var(--brd)" }}>
          {tailors.map((t) => (
            <li key={t.job_id} className="flex items-center justify-between gap-3 py-2 flex-wrap" style={{ borderColor: "var(--brd)" }}>
              <span className="min-w-0">
                <a href={`/tailor/${t.job_id}`} className="font-medium hover:text-indigo-500">
                  {t.title}
                </a>
                <span className="muted"> · {t.company_name}</span>
                <span className="ml-2 text-xs muted">{new Date(t.created_at).toLocaleDateString()}</span>
              </span>
              <span className="flex gap-2 text-xs">
                <span className="chip">{t.model}</span>
                <a href={`/tailor/${t.job_id}`} className="text-indigo-500 hover:text-indigo-400">
                  view
                </a>
                <a
                  href={`http://localhost:8000${t.pdf_url}`}
                  target="_blank"
                  rel="noreferrer"
                  className="muted hover:text-indigo-400"
                >
                  PDF ↗
                </a>
              </span>
            </li>
          ))}
          {tailors.length === 0 && (
            <li className="py-2 muted">
              None yet — hit “Tailor resume” on any match and it will appear here.
            </li>
          )}
        </ul>
      </section>

      <section className="card p-5 space-y-4">
        <h2 className="font-medium">Your details</h2>
        <div className="grid md:grid-cols-2 gap-4">
          <Field label="Full name" value={profile.full_name} onChange={set("full_name")} placeholder="Jane Doe" />
          <Field label="Email" value={profile.email} onChange={set("email")} placeholder="jane@example.com" />
          <Field label="Phone" value={profile.phone} onChange={set("phone")} placeholder="+49 …" />
          <Field label="Current location" value={profile.location} onChange={set("location")} placeholder="City, Country" />
        </div>
        <label className="block">
          <span className="muted text-sm">Summary</span>
          <textarea
            value={profile.summary}
            onChange={(e) => setProfile((p) => ({ ...p, summary: e.target.value }))}
            rows={3}
            className="input mt-1 w-full"
          />
        </label>
        <ListField label="Skills" values={profile.skills} onChange={set("skills")} placeholder="python…" />
        <ListField
          label="Desired titles"
          values={profile.desired_titles}
          onChange={set("desired_titles")}
          placeholder="Forward Deployed Engineer…"
        />
        <ListField
          label="Preferred locations"
          values={profile.preferred_locations}
          onChange={set("preferred_locations")}
          placeholder="Zurich…"
        />
        <label className="flex items-center gap-2 text-sm">
          <input
            type="checkbox"
            checked={profile.remote_ok}
            onChange={(e) => setProfile((p) => ({ ...p, remote_ok: e.target.checked }))}
            className="accent-indigo-500"
          />
          Open to remote roles
        </label>

        <div className="flex items-center gap-4">
          <button onClick={save} disabled={saving} className="btn-primary">
            {saving ? "Saving & rescoring…" : "Save profile"}
          </button>
          {message && <span className="muted text-sm">{message}</span>}
        </div>
      </section>
    </div>
  );
}
