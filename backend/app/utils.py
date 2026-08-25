"""Lightweight classification helpers shared by sync + API layers."""
import re

COUNTRY_RULES = [
    (("germany", "berlin", "munich", "frankfurt", "hesse", "deutschland", "cologne", "hamburg"), "Germany"),
    (("netherlands", "amsterdam", "the hague", "den haag", "rotterdam"), "Netherlands"),
    (("switzerland", "zurich", "zürich", "geneva", "genève", "baar", "lausanne", "basel"), "Switzerland"),
    (("dubai", "abu dhabi", "united arab emirates", "uae"), "UAE"),
]

ROLE_RULES = [
    ("fde", ("forward deployed", "deployment strategist", "(fde)", " ai-fde ", " fde")),
    ("pm", (
        "project manager", "program manager", "project lead",
        "delivery manager", "project management officer",
    )),
    ("solutions", (
        "solutions engineer", "solution engineer", "solutions architect",
        "solution architect", "customer engineer", "solution consultant",
        "solutions consultant", "sales engineer", "pre-sales", "presales",
    )),
    ("implementation", (
        "technical consultant", "implementation consultant", "implementation engineer",
        "professional services", "onboarding consultant",
    )),
    ("field", ("field engineer", "field engineering", "service engineer")),
    ("architecture", ("technical architect", "enterprise architect", "platform architect")),
]


def country_of(location: str | None) -> str | None:
    loc = (location or "").lower()
    for keys, country in COUNTRY_RULES:
        if any(k in loc for k in keys):
            return country
    return None


def role_family(title: str | None) -> str | None:
    t = f" {(title or '').lower()} "
    for family, words in ROLE_RULES:
        if any(w in t for w in words):
            return family
    return None


# ---- salary extraction (best-effort, as-posted currency) ----

CURRENCY_SYMBOLS = {
    "EUR": "€",
    "USD": "$",
    "GBP": "£",
    "CHF": "CHF ",
    "AED": "AED ",
}

CURRENCY_BY_COUNTRY = {
    "Germany": "EUR",
    "Netherlands": "EUR",
    "Switzerland": "CHF",
    "UAE": "AED",
}

_SAL_TOKEN = re.compile(
    r"(€|eur\b|chf\b|aed\b|\$|usd\b|gbp\b|£)"
    r"\s?(\d{1,3}(?:[.,\u202f'\s]\d{3})+|\d{2,6})"
    r"\s?(k\b)?",
    re.I,
)

_TOKEN_CURRENCY = {"€": "EUR", "eur": "EUR", "chf": "CHF", "aed": "AED",
                   "$": "USD", "usd": "USD", "gbp": "GBP", "£": "GBP"}


def _norm_amount(raw: str, has_k: bool) -> int | None:
    digits = re.sub(r"\D", "", raw)
    if not digits:
        return None
    val = int(digits)
    if has_k:
        val *= 1000
    elif val < 1000 and len(digits) <= 2:
        return None  # likely hourly/monthly short form - unusable
    elif 1000 <= val < 15000:
        return None  # ambiguous (monthly/hourly) - skip rather than mislead
    if not (15000 <= val <= 600000):
        return None
    return val


def extract_salary(text: str | None) -> tuple[int | None, int | None, str | None]:
    """Return (min, max, currency-code) annual amounts, if stated."""
    if not text:
        return None, None, None
    vals: list[int] = []
    currency: str | None = None
    for m in _SAL_TOKEN.finditer(text[:4000]):
        sym = m.group(1)
        cur = _TOKEN_CURRENCY.get(sym.lower(), sym.upper())
        val = _norm_amount(m.group(2), bool(m.group(3)))
        if val:
            vals.append(val)
            currency = currency or cur
    if not vals:
        return None, None, None
    lo, hi = min(vals), max(vals)
    return lo, hi, currency


def currency_for_country(country: str | None) -> str | None:
    return CURRENCY_BY_COUNTRY.get(country or "", None)
