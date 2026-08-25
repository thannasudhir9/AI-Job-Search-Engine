from datetime import datetime
from typing import Optional

from pydantic import BaseModel


class ProfileUpdate(BaseModel):
    full_name: str = ""
    email: str = ""
    phone: str = ""
    location: str = ""
    links: list[dict] = []
    summary: str = ""
    skills: list[str] = []
    desired_titles: list[str] = []
    preferred_locations: list[str] = []
    remote_ok: bool = True
    min_salary: Optional[int] = None


class ProfileOut(ProfileUpdate):
    id: int
    updated_at: Optional[datetime] = None


class CompanyCreate(BaseModel):
    name: str
    source: str  # greenhouse | lever | ashby
    slug: str


class CompanyOut(CompanyCreate):
    id: int
    enabled: bool
    last_synced_at: Optional[datetime] = None


class SyncResult(BaseModel):
    companies_synced: int
    jobs_fetched: int
    jobs_new: int
    errors: list[str] = []


class ResumeOut(BaseModel):
    id: int
    name: str
    is_master: bool
    text_chars: int
    created_at: datetime


class JobOut(BaseModel):
    id: int
    company_name: str
    source: str
    title: str
    location: str
    url: str
    posted_at: Optional[datetime] = None
    created_at: datetime
    score: Optional[float] = None
    reasons: list[str] = []
    applied: bool = False
    country: Optional[str] = None
    role_family: Optional[str] = None
    salary_min: Optional[int] = None
    salary_max: Optional[int] = None
    salary_currency: Optional[str] = None


class TailorOut(BaseModel):
    job_id: int
    content: str
    model: str
    pdf_url: str


class ApplicationCreate(BaseModel):
    job_id: int
    status: str = "draft"
    variant_id: Optional[int] = None


class ApplicationUpdate(BaseModel):
    status: Optional[str] = None
    notes: Optional[str] = None
    variant_id: Optional[int] = None


class ApplicationOut(BaseModel):
    id: int
    job_id: int
    job_title: str = ""
    company_name: str = ""
    job_url: str = ""
    status: str
    notes: str
    events: list[dict] = []
    updated_at: Optional[datetime] = None
    variant_id: Optional[int] = None
    resume_pdf_url: Optional[str] = None
    resume_model: Optional[str] = None


class StatusOut(BaseModel):
    jobs: int
    matches: int
    applications: int
    resumes: int
    ollama_available: bool
    ollama_models: list[str] = []
    sync_interval_hours: float
