"""Fetch jobs from public job-board APIs (Greenhouse, Lever, Ashby)."""
import re
from datetime import datetime

import html as html_lib
import httpx

from ..config import HTTP_TIMEOUT

HEADERS = {"User-Agent": "local-job-agent/0.1 (+personal use; contact: you@example.com)"}


def _clean_html(raw: str) -> str:
    text = re.sub(r"<br\s*/?>", "\n", raw or "", flags=re.I)
    text = re.sub(r"</(p|div|li|h[1-6])>", "\n", text, flags=re.I)
    text = re.sub(r"<[^>]+>", " ", text)
    text = html_lib.unescape(text)
    text = re.sub(r"[ \t]+", " ", text)
    text = re.sub(r"\n\s*\n+", "\n\n", text)
    return text.strip()


def _parse_date(value) -> datetime | None:
    if not value:
        return None
    try:
        return datetime.fromisoformat(str(value).replace("Z", "+00:00")).replace(tzinfo=None)
    except ValueError:
        return None


def fetch_greenhouse(client: httpx.Client, slug: str) -> list[dict]:
    url = f"https://boards-api.greenhouse.io/v1/boards/{slug}/jobs?content=true"
    r = client.get(url, headers=HEADERS, timeout=HTTP_TIMEOUT)
    r.raise_for_status()
    out = []
    for j in r.json().get("jobs", []):
        first_seen = j.get("first_published")
        out.append(
            {
                "ext_id": f"gh-{j.get('id')}",
                "title": (j.get("title") or "").strip(),
                "location": ((j.get("location") or {}).get("name") or "").strip(),
                "url": j.get("absolute_url") or "",
                "description": _clean_html(j.get("content") or "")[:8000],
                "posted_at": _parse_date(first_seen),
            }
        )
    return out


def fetch_lever(client: httpx.Client, slug: str) -> list[dict]:
    url = f"https://api.lever.co/v0/postings/{slug}?mode=json"
    r = client.get(url, headers=HEADERS, timeout=HTTP_TIMEOUT)
    r.raise_for_status()
    out = []
    for j in r.json():
        cats = j.get("categories") or {}
        desc = j.get("descriptionPlain") or ""
        for lst in j.get("lists") or []:
            desc += f"\n\n{lst.get('text','')}\n{lst.get('content','')}"
        out.append(
            {
                "ext_id": f"lv-{j.get('id')}",
                "title": (j.get("text") or "").strip(),
                "location": (cats.get("location") or "").strip(),
                "url": j.get("hostedUrl") or "",
                "description": desc.strip()[:8000],
                "posted_at": _parse_date(j.get("createdAt") / 1000 if j.get("createdAt") else None),
            }
        )
    return out


def fetch_ashby(client: httpx.Client, slug: str) -> list[dict]:
    url = f"https://api.ashbyhq.com/posting-api/job-board/{slug}"
    r = client.get(url, headers=HEADERS, timeout=HTTP_TIMEOUT)
    r.raise_for_status()
    out = []
    for j in r.json().get("jobs", []):
        parts = [j.get("descriptionPlain") or ""]
        for lst in j.get("lists") or []:
            parts.append(f"{lst.get('label','')}:\n{lst.get('content','')}")
        out.append(
            {
                "ext_id": f"as-{j.get('id')}",
                "title": (j.get("title") or "").strip(),
                "location": (j.get("location") or "").strip(),
                "url": j.get("jobUrl") or "",
                "description": "\n\n".join(p for p in parts if p).strip()[:8000],
                "posted_at": _parse_date(j.get("publishedAt")),
            }
        )
    return out


def fetch_salesforce(client: httpx.Client, slug: str = "prod") -> list[dict]:
    """Salesforce careers publishes its full job list as static CDN JSON chunks
    (jobs_1.json, jobs_2.json, ...). No auth needed."""
    out: list[dict] = []
    for chunk in (1, 2):
        url = f"https://a.sfdcstatic.com/digital/xsf/careers/prod/jobs_{chunk}.json"
        r = client.get(url, headers=HEADERS, timeout=HTTP_TIMEOUT)
        if r.status_code == 404:
            break  # no more chunks
        r.raise_for_status()
        entries = r.json().get("Report_Entry", [])
        for j in entries:
            ref = j.get("Job_Requisition_Ref_ID") or ""
            if not ref:
                continue
            countries = ", ".join(j.get("Countries") or [])
            regions = ", ".join(j.get("Regions") or [])
            locations = ", ".join(j.get("Locations") or [])
            location = " - ".join(x for x in (countries, locations) if x)
            sal_min = int(float(j["EU_Min_Salary"])) if str(j.get("EU_Min_Salary") or "0") not in ("", "0") else None
            sal_max = int(float(j["EU_Max_Salary"])) if str(j.get("EU_Max_Salary") or "0") not in ("", "0") else None
            out.append(
                {
                    "ext_id": f"sf-{ref}",
                    "title": (j.get("Job_Posting_Title") or "").strip(),
                    "location": f"{location} ({regions})" if regions else location,
                    "url": j.get("External_Job_Posting_Site") or "",
                    "description": _clean_html(j.get("Job_Description") or "")[:8000],
                    "posted_at": _parse_date(j.get("External_Job_Posting_Start_Date")),
                    "salary_min": sal_min,
                    "salary_max": sal_max,
                }
            )
        if len(out) >= r.json().get("Total_Jobs", 0) > 0:
            break
    return out


def fetch_linkedin(client: httpx.Client, slug: str) -> list[dict]:
    """LinkedIn *public* job search via the guest endpoint.

    slug format: "keywords|location"  e.g. "forward deployed engineer|Germany".
    Polite by design: 2 pages x 25 cards per sync cycle, nothing more.
    """
    from urllib.parse import quote

    keywords, _, location = slug.partition("|")
    out: dict[str, dict] = {}
    for start in (0, 25):
        url = (
            "https://www.linkedin.com/jobs-guest/jobs/api/seeMoreJobPostings/search"
            f"?keywords={quote(keywords)}&location={quote(location)}&start={start}"
        )
        r = client.get(url, headers=HEADERS, timeout=HTTP_TIMEOUT)
        if r.status_code != 200:
            raise RuntimeError(f"linkedin responded {r.status_code} (rate limit?) for '{keywords}|{location}'")
        html = r.text
        chunks = html.split('<div class="base-card')
        for chunk in chunks[1:]:
            url_m = re.search(r'href="([^"]+/jobs/view/[^"]+)"', chunk)
            title_m = re.search(r'class="base-search-card__title[^"]*">\s*([^<]+?)\s*</h3>', chunk)
            comp_m = re.search(r'class="base-search-card__subtitle[^"]*">.*?>\s*([^<]+?)\s*</h4>', chunk, re.S)
            loc_m = re.search(r'job-search-card__location[^"]*">\s*([^<]+?)\s*</span>', chunk)
            date_m = re.search(r'datetime="([^"]+)"', chunk)
            if not (url_m and title_m):
                continue
            view_path = url_m.group(1)
            ext = re.search(r"/jobs/view/([^/?]+)", view_path)
            ext_id = f"li-{ext.group(1)}" if ext else f"li-{hash(view_path) & 0xfffffff}"
            company = re.sub(r"\s+", " ", comp_m.group(1)) if comp_m else ""
            loc = re.sub(r"\s+", " ", loc_m.group(1)) if loc_m else ""
            title = re.sub(r"\s+", " ", title_m.group(1))
            out.setdefault(
                ext_id,
                {
                    "ext_id": ext_id,
                    "title": title,
                    "location": loc,
                    "url": view_path.split("?")[0],
                    # list API has no description; give scoring a factual stub
                    "description": f"{title} at {company} ({loc}). Source: LinkedIn search for '{keywords}'.",
                    "posted_at": _parse_date(date_m.group(1)) if date_m else None,
                    "_company_override": company.strip(),
                },
            )
        if len(out) >= 40:
            break
    return list(out.values())


FETCHERS = {
    "greenhouse": fetch_greenhouse,
    "lever": fetch_lever,
    "ashby": fetch_ashby,
    "salesforce": fetch_salesforce,
    "linkedin": fetch_linkedin,
}
