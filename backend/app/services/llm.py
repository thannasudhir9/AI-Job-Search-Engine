"""LLM access via Ollama, with a deterministic fallback tailoring mode."""
import re

import httpx

from ..config import OLLAMA_BASE_URL, OLLAMA_CHAT_MODEL


def ollama_chat_available() -> tuple[bool, list[str]]:
    try:
        r = httpx.get(f"{OLLAMA_BASE_URL}/api/tags", timeout=2)
        models = [m.get("name", "") for m in r.json().get("models", [])]
        return len(models) > 0, models
    except Exception:
        return False, []


def chat(system: str, user: str, temperature: float = 0.4) -> str | None:
    """Return model output, or None if Ollama is unavailable."""
    try:
        r = httpx.post(
            f"{OLLAMA_BASE_URL}/api/chat",
            json={
                "model": OLLAMA_CHAT_MODEL,
                "messages": [
                    {"role": "system", "content": system},
                    {"role": "user", "content": user},
                ],
                "stream": False,
                "options": {"temperature": temperature},
            },
            timeout=180,
        )
        r.raise_for_status()
        return r.json().get("message", {}).get("content")
    except Exception:
        return None


SYSTEM_PROMPT = (
    "You are an expert resume writer. You rewrite resumes so they are tailored to a specific job "
    "posting while staying 100% truthful to the source resume: never invent employers, dates, titles, "
    "schools, or skills the candidate does not have. Output plain text only (no markdown symbols like "
    "** or #), ATS-friendly single column, with UPPERCASE section headers such as SUMMARY, SKILLS, "
    "EXPERIENCE, EDUCATION, PROJECTS. Keep it within two pages."
)


def tailor_with_llm(master_text: str, job_title: str, company: str, job_description: str) -> str | None:
    user = f"""Tailor this resume for the role below.

JOB TITLE: {job_title}
COMPANY: {company}
JOB DESCRIPTION (first 6000 chars):
{job_description[:6000]}

MASTER RESUME:
{master_text[:8000]}

Rules:
- Emphasize the experience and skills most relevant to this job; reorder bullets if helpful.
- Mirror important keywords from the posting where they truthfully apply.
- Do not add new facts. Keep contact info exactly as in the master resume.
- Return ONLY the final resume plain text."""
    out = chat(SYSTEM_PROMPT, user)
    if not out:
        return None
    cleaned = out.replace("**", "").replace("#", "").replace("*", "")
    return cleaned.strip()


# ---------------- deterministic fallback ----------------

def _split_sections(text: str) -> dict[str, str]:
    sections: dict[str, str] = {}
    current = "HEADER"
    buf: list[str] = []
    for line in (text or "").splitlines():
        stripped = line.strip()
        is_header = bool(re.fullmatch(r"[A-Z][A-Z &/\-]{2,}", stripped)) and len(stripped) < 40
        if is_header:
            if buf:
                sections[current] = "\n".join(buf).strip()
            current = stripped.title()
            buf = []
        else:
            buf.append(line)
    if buf:
        sections[current] = "\n".join(buf).strip()
    return sections


def tailor_fallback(master_text: str, job_title: str, company: str, job_description: str,
                    skills: list[str]) -> str:
    from .matching import tokenize

    jd_tokens = set(tokenize(job_title + " " + job_description[:3000]))
    matched_skills = [s for s in skills if s.lower() in jd_tokens]
    other_skills = [s for s in skills if s not in matched_skills]

    lines = [f"TARGET ROLE: {job_title} — {company}", ""]
    if matched_skills:
        lines.append("RELEVANT SKILLS FOR THIS ROLE")
        lines.append(", ".join(matched_skills))
        lines.append("")
    sections = _split_sections(master_text)
    for name, body in sections.items():
        if not body.strip():
            continue
        lines.append(name.upper())
        lines.append(body.strip())
        lines.append("")
    if other_skills:
        lines.append("ADDITIONAL SKILLS")
        lines.append(", ".join(other_skills))
        lines.append("")
    lines.append("(Tailored with local keyword matching - install/run Ollama for full AI rewriting.)")
    return "\n".join(lines).strip()
