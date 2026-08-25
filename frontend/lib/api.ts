const API = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

export interface Status {
  jobs: number;
  matches: number;
  applications: number;
  resumes: number;
  ollama_available: boolean;
  ollama_models: string[];
  sync_interval_hours: number;
}

export interface JobMatch {
  id: number;
  company_name: string;
  source: string;
  title: string;
  location: string;
  url: string;
  posted_at: string | null;
  created_at: string;
  score: number | null;
  reasons: string[];
  applied: boolean;
  country: string | null;
  role_family: string | null;
  salary_min: number | null;
  salary_max: number | null;
  salary_currency: string | null;
}

export interface CompanyRow {
  id: number;
  name: string;
  source: string;
  slug: string;
  enabled: boolean;
  last_synced_at: string | null;
  job_count: number;
}

export interface ResumeRow {
  id: number;
  name: string;
  is_master: boolean;
  text_chars: number;
  created_at: string;
}

export interface ApplicationRow {
  id: number;
  job_id: number;
  job_title: string;
  company_name: string;
  job_url: string;
  status: string;
  notes: string;
  events: { at: string; status: string; note: string }[];
  updated_at: string | null;
  variant_id?: number | null;
  resume_pdf_url?: string | null;
  resume_model?: string | null;
}

export interface TailorRow {
  job_id: number;
  title: string;
  company_name: string;
  location: string;
  model: string;
  pdf_url: string;
  created_at: string;
}

export interface ProfileData {
  full_name: string;
  email: string;
  phone: string;
  location: string;
  summary: string;
  skills: string[];
  desired_titles: string[];
  preferred_locations: string[];
  remote_ok: boolean;
}

async function req<T>(path: string, init?: RequestInit): Promise<T> {
  const res = await fetch(`${API}${path}`, {
    headers: init?.body ? { "Content-Type": "application/json" } : undefined,
    ...init,
  });
  if (!res.ok) {
    let detail = `${res.status} ${res.statusText}`;
    try {
      const body = await res.json();
      detail = typeof body.detail === "string" ? body.detail : JSON.stringify(body.detail ?? body);
    } catch { /* ignore */ }
    throw new Error(detail);
  }
  return res.json() as Promise<T>;
}

export const api = {
  status: () => req<Status>("/api/status"),
  syncNow: () =>
    req<{ companies_synced: number; jobs_fetched: number; jobs_new: number; errors: string[] }>(
      "/api/sync?wait=true", { method: "POST" },
    ),
  addCompany: (name: string, source: string, slug: string) =>
    req<{ id: number }>("/api/companies", {
      method: "POST",
      body: JSON.stringify({ name, source, slug }),
    }),
  removeCompany: (id: number) => req<{ ok: boolean }>(`/api/companies/${id}`, { method: "DELETE" }),
  companies: () => req<CompanyRow[]>("/api/companies"),
  matches: (
    params: {
      limit?: number;
      country?: string;
      role?: string;
      company?: string;
      min_salary?: number;
      min_score?: number;
    } = {},
  ) => {
    const qs = new URLSearchParams();
    if (params.limit) qs.set("limit", String(params.limit));
    if (params.country) qs.set("country", params.country);
    if (params.role) qs.set("role", params.role);
    if (params.company) qs.set("company", params.company);
    if (params.min_salary) qs.set("min_salary", String(params.min_salary));
    if (params.min_score) qs.set("min_score", String(params.min_score));
    return req<JobMatch[]>(`/api/matches?${qs.toString()}`);
  },
  facets: () =>
    req<{ countries: string[]; companies: string[] }>("/api/matches/facets"),
  tailorsList: () => req<TailorRow[]>("/api/tailor/list"),
  masterResume: () => req<{ id: number; name: string; text: string }>("/api/resumes/master"),
  job: (id: number) =>
    req<{
      id: number;
      title: string;
      company_name: string;
      location: string;
      url: string;
      salary_min: number | null;
      salary_max: number | null;
    }>(`/api/jobs/${id}`),
  dismissMatch: (jobId: number) =>
    req<{ ok: boolean }>(`/api/matches/${jobId}/dismiss`, { method: "POST" }),
  trackJob: (jobId: number, status = "draft") =>
    req<ApplicationRow>("/api/applications", {
      method: "POST",
      body: JSON.stringify({ job_id: jobId, status }),
    }),
  tailor: (jobId: number, force = false) =>
    req<{ job_id: number; content: string; model: string; pdf_url: string }>(
      `/api/tailor/${jobId}?force=${force}`, { method: "POST" },
    ),
  applications: () => req<ApplicationRow[]>("/api/applications"),
  updateApplication: (id: number, patch: { status?: string; notes?: string }) =>
    req<ApplicationRow>(`/api/applications/${id}`, {
      method: "PATCH",
      body: JSON.stringify(patch),
    }),
  deleteApplication: (id: number) =>
    req<{ ok: boolean }>(`/api/applications/${id}`, { method: "DELETE" }),
  profile: () => req<ProfileData>("/api/profile"),
  saveProfile: (p: ProfileData) =>
    req<ProfileData>("/api/profile", { method: "PUT", body: JSON.stringify(p) }),
  resumes: () => req<ResumeRow[]>("/api/resumes"),
};

export const pdfUrl = (jobId: number) => `${API}/api/tailor/${jobId}/pdf`;
export default API;
