"""Find sections, bullets, contact details and dates in resume text."""
from __future__ import annotations

import re

from .knowledge import BULLET_CHARS, SECTION_ALIASES

_ALIAS_TO_SECTION = {a: sec for sec, aliases in SECTION_ALIASES.items() for a in aliases}
_BULLET_START = re.compile(rf"^\s*[{re.escape(BULLET_CHARS)}]\s+|^\s*\d+[.)]\s+")

EMAIL = re.compile(r"[A-Za-z0-9._%+-]+@[A-Za-z0-9-]+(?:\.[A-Za-z0-9-]+)+")
PHONE = re.compile(r"(?<!\d)(?:\+?\d{1,3}[\s-]?)?(?:\(?\d{3,5}\)?[\s.-]?)?\d{3,5}[\s.-]?\d{3,5}(?!\d)")
LINKEDIN = re.compile(r"(?:https?://)?(?:www\.)?linkedin\.com/(?:in|pub)/[\w\-%]+/?", re.I)
GITHUB = re.compile(r"(?:https?://)?(?:www\.)?github\.com/[\w\-]+/?", re.I)
PORTFOLIO = re.compile(r"(?<![\w.])(?:https?://)?(?:www\.)?[\w\-]{3,}\.(?:dev|io|me|tech|vercel\.app|netlify\.app|github\.io)\b/?\S*", re.I)

MONTHS = r"(?:jan(?:uary)?|feb(?:ruary)?|mar(?:ch)?|apr(?:il)?|may|jun(?:e)?|jul(?:y)?|aug(?:ust)?|sep(?:t(?:ember)?)?|oct(?:ober)?|nov(?:ember)?|dec(?:ember)?)"
DATE_MON_YEAR = re.compile(rf"\b{MONTHS}\.?\s*,?\s*(?:19|20)\d{{2}}\b", re.I)
DATE_NUMERIC = re.compile(r"\b(?:0?[1-9]|1[0-2])[/-](?:19|20)\d{2}\b")
DATE_YEAR_RANGE = re.compile(r"\b(?:19|20)\d{2}\s*(?:[-–—]|to)\s*(?:(?:19|20)\d{2}|present|current|now|ongoing)\b", re.I)
DATE_YEAR = re.compile(r"\b(?:19|20)\d{2}\b")


def heading_of(line: str) -> str | None:
    """Return the section name if this line looks like a section heading."""
    s = re.sub(r"^[\W_]+|[\W_]+$", "", line.strip()).lower()
    s = re.sub(r"\s+", " ", s)
    if not s or len(s) > 45 or len(s.split()) > 5 or line.strip().endswith("."):
        return None
    return _ALIAS_TO_SECTION.get(s) or _ALIAS_TO_SECTION.get(s.replace("&", "and"))


def split_sections(text: str) -> dict[str, list[str]]:
    sections: dict[str, list[str]] = {"header": []}
    current = "header"
    for raw in text.split("\n"):
        line = raw.strip()
        if not line:
            continue
        sec = heading_of(line) if not _BULLET_START.match(line) else None
        if sec:
            current = sec
            sections.setdefault(current, [])
            continue
        sections.setdefault(current, []).append(line)
    return sections


def is_bullet_line(line: str) -> bool:
    return bool(_BULLET_START.match(line))


def strip_bullet(line: str) -> str:
    return _BULLET_START.sub("", line, count=1).strip()


def bullets_in(lines: list[str]) -> tuple[list[str], int]:
    """Return (bullet texts, how many real bullet characters were used).
    Wrapped lines are glued back onto the bullet they belong to."""
    out: list[str] = []
    marked = 0
    for line in lines:
        if is_bullet_line(line):
            out.append(strip_bullet(line))
            marked += 1
        elif out and marked and (line[:1].islower() or not out[-1].rstrip().endswith((".", "!", ";"))) \
                and len(line.split()) < 25 and not heading_of(line):
            out[-1] += " " + line
    if not marked:  # PDF lost the bullet characters: treat sentence-like lines as bullets
        out = [l for l in lines if len(l.split()) >= 7 and not heading_of(l)]
    return out, marked


def contact_info(text: str, header_lines: list[str]) -> dict:
    email = EMAIL.search(text)
    phone = None
    for m in PHONE.finditer(text):
        digits = re.sub(r"\D", "", m.group())
        if 10 <= len(digits) <= 13 and not re.fullmatch(r"(?:19|20)\d{2}(?:19|20)\d{2}", digits):
            phone = m.group().strip()
            break
    linkedin = LINKEDIN.search(text)
    github = GITHUB.search(text)
    portfolio = PORTFOLIO.search(text)
    has_li_word = bool(re.search(r"linkedin", text, re.I))
    return {
        "email": email.group() if email else None,
        "phone": phone,
        "linkedin": linkedin.group() if linkedin else ("mentioned, no link" if has_li_word else None),
        "github": github.group() if github else None,
        "portfolio": portfolio.group() if portfolio and not (github and portfolio.group() in github.group()) else None,
    }


def dates_in(text: str) -> dict:
    mon = DATE_MON_YEAR.findall(text)
    num = DATE_NUMERIC.findall(text)
    rng = DATE_YEAR_RANGE.findall(text)
    years = DATE_YEAR.findall(text)
    styles = []
    if mon: styles.append("Month YYYY")
    if num: styles.append("MM/YYYY")
    return {"month_year": len(mon), "numeric": len(num), "year_ranges": len(rng),
            "years": len(years), "styles": styles}
