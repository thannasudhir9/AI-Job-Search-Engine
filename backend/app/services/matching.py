"""Score jobs against the profile.

Primary method: weighted keyword/skill scoring (pure python).
Upgrade: if Ollama is running with an embedding model, blend in cosine similarity.
"""
import math
import re
from datetime import datetime

import httpx
from sqlalchemy.orm import Session

from ..config import OLLAMA_BASE_URL, OLLAMA_EMBED_MODEL
from ..models import Job, Profile

STOPWORDS = set(
    """a an and are as at be by for from has have in into is it its of on or that the to was were will
    with you your our we they their this those these about across after all also any been before being
    both but can could did do does down during each even every few more most much must not now only over
    own same should so some such than then there they'd under until up very what when where which while
    who why work working works role team teams job jobs company companies years year experience strong
    etc using use used new other others including include includes""".split()
)

_word_re = re.compile(r"[a-z][a-z+#.\-]{1,}")


def tokenize(text: str) -> list[str]:
    tokens = []
    for raw in _word_re.findall((text or "").lower()):
        token = raw.strip(".-")
        if len(token) > 1 and token not in STOPWORDS:
            tokens.append(token)
    return tokens


def _tf(tokens: list[str]) -> dict[str, float]:
    tf: dict[str, float] = {}
    for t in tokens:
        tf[t] = tf.get(t, 0.0) + 1.0
    norm = math.sqrt(sum(v * v for v in tf.values())) or 1.0
    return {k: v / norm for k, v in tf.items()}


def cosine(a: dict[str, float], b: dict[str, float]) -> float:
    if len(a) > len(b):
        a, b = b, a
    return sum(v * b.get(k, 0.0) for k, v in a.items())


# ---------------- Ollama embeddings (optional upgrade) ----------------

_ollama_cache = {"ok": None, "checked_at": 0.0}


def ollama_embed_available() -> bool:
    import time

    if time.time() - _ollama_cache["checked_at"] < 30:
        return bool(_ollama_cache["ok"])
    try:
        r = httpx.get(f"{OLLAMA_BASE_URL}/api/tags", timeout=2)
        models = [m.get("name", "") for m in r.json().get("models", [])]
        _ollama_cache["ok"] = any(m.startswith(OLLAMA_EMBED_MODEL) for m in models)
    except Exception:
        _ollama_cache["ok"] = False
    _ollama_cache["checked_at"] = time.time()
    return bool(_ollama_cache["ok"])


def embed(text: str) -> list[float] | None:
    try:
        r = httpx.post(
            f"{OLLAMA_BASE_URL}/api/embeddings",
            json={"model": OLLAMA_EMBED_MODEL, "prompt": text[:4000]},
            timeout=20,
        )
        r.raise_for_status()
        return r.json().get("embedding")
    except Exception:
        return None


def _cosine_vec(a: list[float], b: list[float]) -> float:
    dot = sum(x * y for x, y in zip(a, b))
    na = math.sqrt(sum(x * x for x in a)) or 1.0
    nb = math.sqrt(sum(x * x for x in b)) or 1.0
    return dot / (na * nb)


# ---------------- keyword score ----------------

def profile_query_text(profile: Profile) -> str:
    parts = [
        " ".join(profile.desired_titles or []),
        " ".join(profile.skills or []),
        profile.summary or "",
        " ".join(profile.preferred_locations or []),
    ]
    return " ".join(p for p in parts if p)


def keyword_score(profile: Profile, job: Job) -> tuple[float, list[str]]:
    reasons: list[str] = []
    title_tokens = set(tokenize(job.title))
    haystack_tokens = set(tokenize(job.title + " " + (job.location or "") + " " + job.description[:3000]))

    # 1) desired titles overlap (0-40)
    desired_tokens: set[str] = set()
    for dt in profile.desired_titles or []:
        desired_tokens.update(tokenize(dt))
    if desired_tokens:
        overlap = desired_tokens & title_tokens
        ratio = len(overlap) / max(1, len(desired_tokens))
        points = min(40.0, 40.0 * (ratio + 0.25 if overlap else 0))
        if overlap:
            reasons.append(f"Title matches: {', '.join(sorted(overlap)[:5])}")
    elif profile.skills:
        points = 20.0  # no titles configured; neutral base
    else:
        points = 10.0

    # 2) skills coverage (0-35)
    skills = [s for s in (profile.skills or []) if s]
    if skills:
        found = []
        for s in skills:
            if s.lower() in haystack_tokens or s.lower() in (job.title.lower() + " " + job.description[:3000].lower()):
                found.append(s)
        points += 35.0 * len(found) / len(skills)
        if found:
            reasons.append(f"Skills hit ({len(found)}/{len(skills)}): {', '.join(found[:8])}")
    else:
        points += 15.0

    # 3) location / remote (0-15)
    loc = (job.location or "").lower()
    desc_head = job.description[:1500].lower()
    if profile.remote_ok and ("remote" in loc or "remote" in desc_head.split("\n")[0]):
        points += 15.0
        reasons.append("Remote-friendly")
    else:
        prefs = [p.lower() for p in (profile.preferred_locations or [])]
        if any(p and p in loc for p in prefs):
            points += 15.0
            reasons.append(f"Location match: {job.location}")
        elif not prefs and not loc:
            points += 7.5

    # 4) freshness bonus (0-10)
    if job.posted_at:
        age_days = (datetime.utcnow() - job.posted_at).days
        if age_days <= 3:
            points += 10.0
            reasons.append("Posted within 3 days")
        elif age_days <= 14:
            points += 6.0
        elif age_days <= 30:
            points += 2.0

    return min(100.0, points), reasons


def score_job(db_profile: Profile, job: Job) -> tuple[float, str, list[str]]:
    kw, reasons = keyword_score(db_profile, job)
    if ollama_embed_available():
        qvec = embed(profile_query_text(db_profile))
        jvec = embed(job.title + "\n" + job.description[:2500])
        if qvec and jvec:
            emb = (_cosine_vec(qvec, jvec) + 1.0) / 2.0 * 100.0
            final = 0.55 * kw + 0.45 * emb
            reasons.insert(0, f"Semantic similarity {emb:.0f}/100")
            return round(final, 1), "hybrid", reasons
    return round(kw, 1), "keyword", reasons


def recompute_matches(db: Session) -> int:
    """Re-score all jobs for profile id=1. Returns number of matches updated."""
    from ..models import Company, Match

    profile = db.get(Profile, 1)
    if profile is None:
        return 0
    priority_names = {
        c.name.lower()
        for c in db.query(Company).filter(Company.priority.is_(True)).all()
    }
    count = 0
    for job in db.query(Job).all():
        score, method, reasons = score_job(profile, job)
        if job.company_name.lower() in priority_names:
            score = min(100.0, score + 12.0)
            reasons.insert(0, "High-priority source")
        m = db.query(Match).filter(Match.job_id == job.id).first()
        if m is None:
            m = Match(job_id=job.id)
            db.add(m)
        m.score = score
        m.method = method
        m.reasons = reasons
        count += 1
    db.commit()
    return count
