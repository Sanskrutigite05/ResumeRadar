"""Score a resume out of 100 across six categories. Every check says what it found and how to fix it."""
from __future__ import annotations

import re
import unicodedata
from collections import Counter

from .keywords import find_skills, match_job
from .knowledge import ACTION_VERBS, BUZZWORDS, UNPROFESSIONAL_EMAIL_WORDS, WEAK_STARTS
from .parse import bullets_in, contact_info, dates_in, split_sections

CATEGORY_LABELS = {
    "contact": "Contact details",
    "sections": "Sections",
    "keywords": "Keywords and skills",
    "impact": "Impact of your bullets",
    "format": "Formatting for ATS",
    "content": "Writing quality",
}


def _check(cid, label, max_pts, ratio, detail, fix, examples=None, status=None):
    ratio = max(0.0, min(1.0, ratio))
    pts = round(max_pts * ratio, 1)
    if status is None:
        status = "pass" if ratio >= 0.85 else "warn" if ratio >= 0.4 else "fail"
    return {"id": cid, "label": label, "max": max_pts, "points": pts, "status": status,
            "detail": detail, "fix": "" if status == "pass" else fix, "examples": examples or []}


def _first_word(text: str) -> str:
    m = re.match(r"[A-Za-z][A-Za-z'-]*", text.strip())
    return m.group().lower() if m else ""


def _weak_start(text: str) -> str | None:
    low = text.lower().lstrip()
    for phrase in sorted(WEAK_STARTS, key=len, reverse=True):
        if low.startswith(phrase):
            return phrase
    return None


_IRREGULAR = {"building": "Built", "making": "Built", "running": "Ran", "writing": "Wrote", "leading": "Led",
              "doing": "Completed", "taking": "Handled", "giving": "Provided", "keeping": "Maintained"}


def _past_tense(gerund: str) -> str | None:
    g = gerund.lower()
    if g in _IRREGULAR:
        return _IRREGULAR[g]
    if g.endswith("ing") and len(g) > 5:
        base = g[:-3]
        for cand in (base + "ed", base + "d"):
            if cand in ACTION_VERBS:
                return cand.capitalize()
    return None


def _rewrite_hint(bullet: str, phrase: str) -> str:
    rest = bullet[len(phrase):].lstrip(" ,:")
    words = rest.split()
    past = _past_tense(words[0]) if words else None
    tail = words[1:]
    if past and tail[:1] == ["of"]:
        tail = tail[1:]
    start = f"{past} {' '.join(tail)}" if past else f"{WEAK_STARTS[phrase].strip()} {rest}"
    start = start.strip()
    return f"{start[:75]}{'...' if len(start) > 75 else ''}  (then add a result)"


def _has_number(text: str) -> bool:
    cleaned = re.sub(r"\b(?:19|20)\d{2}\b", "", text)
    return bool(re.search(r"\d", cleaned))


def _short(text: str, n: int = 110) -> str:
    return text if len(text) <= n else text[: n - 1].rstrip() + "…"


# ---------------------------------------------------------------- categories
def contact_checks(text, sections):
    c = contact_info(text, sections.get("header", []))
    out = []
    out.append(_check("email", "Email address", 3, 1 if c["email"] else 0,
                      c["email"] or "No email address found.",
                      "Add a clear email address at the top, as plain text (not an image or icon)."))
    out.append(_check("phone", "Phone number", 3, 1 if c["phone"] else 0,
                      c["phone"] or "No phone number found.",
                      "Add a phone number with the country code, for example +91 98765 43210."))
    li, gh, pf = c["linkedin"], c["github"], c["portfolio"]
    links = [x for x in (li if li and li != "mentioned, no link" else None, gh, pf) if x]
    if li and li != "mentioned, no link" and (gh or pf):
        ratio, detail = 1, "LinkedIn and a code or portfolio link found."
    elif links:
        ratio, detail = 0.6, "Found: " + ", ".join(links) + "."
    elif li == "mentioned, no link":
        ratio, detail = 0.3, 'The word "LinkedIn" appears but there is no profile address.'
    else:
        ratio, detail = 0, "No LinkedIn, GitHub or portfolio link found."
    out.append(_check("links", "Profile links", 3, ratio, detail,
                      "Add the full LinkedIn address (linkedin.com/in/yourname) and your GitHub or portfolio link. "
                      "Write them out as text so the ATS can read them."))
    prof = 1.0
    detail = "Looks professional."
    if c["email"]:
        local = c["email"].split("@")[0].lower()
        if re.search(r"\d{4,}", local) or any(w in local for w in UNPROFESSIONAL_EMAIL_WORDS):
            prof, detail = 0.3, f'"{c["email"]}" may look unprofessional to a recruiter.'
    else:
        prof, detail = 0, "No email to check."
    out.append(_check("email_style", "Professional email", 1, prof, detail,
                      "Use an address based on your name, like firstname.lastname@gmail.com."))
    return out, c


def section_checks(sections):
    has = lambda k: len(sections.get(k, [])) >= 1
    exp_or_proj = has("experience") or has("projects")
    out = [
        _check("sec_education", "Education section", 4, 1 if has("education") else 0,
               "Found." if has("education") else "No Education heading found.",
               'Add a section headed exactly "Education" with your degree, college and year.'),
        _check("sec_experience", "Experience or Internships", 4,
               1 if has("experience") else (0.5 if has("projects") else 0),
               "Found." if has("experience") else
               ("No Experience heading, but Projects found. Fine for a student, internships would help." if has("projects")
                else "No Experience or Internships heading found."),
               'Add "Experience" or "Internships". If you have none, add a strong "Projects" section instead.'),
        _check("sec_skills", "Skills section", 4, 1 if has("skills") else 0,
               "Found." if has("skills") else "No Skills heading found.",
               'Add a section headed "Skills" (or "Technical Skills") listing your tools and languages as plain text.'),
        _check("sec_projects", "Projects section", 3, 1 if has("projects") else (0.5 if exp_or_proj else 0),
               "Found." if has("projects") else "No Projects heading found.",
               'Add a "Projects" section with 2 to 3 projects. Say what you built, with which tools, and the result.'),
    ]
    return out


def keyword_checks(text, sections, jd_text):
    skills_text = " ".join(sections.get("skills", []))
    found = find_skills(text, skills_text)
    by_cat: dict[str, list[str]] = {}
    for skill, cat in found.items():
        by_cat.setdefault(cat, []).append(skill)
    tech = {s: c for s, c in found.items() if c != "soft skills"}
    out = []
    job = None
    if jd_text and len(jd_text.split()) >= 15:
        job = match_job(text, found, jd_text)
    if job and job["percent"] is not None:
        pct = job["percent"]
        out.append(_check("jd_match", "Match with the job description", 20, min(1, pct / 75),
                          f"{pct}% of the job's keywords appear in your resume "
                          f"({len(job['found'])} of {len(job['required'])})."
                          + (f" Overall text similarity: {job['similarity']}%." if job["similarity"] is not None else ""),
                          "Add the missing keywords where they are true for you: in your Skills section and inside bullets "
                          "that show you used them. Use the same spelling as the job post.",
                          examples=job["missing"][:12]))
        out.append(_check("skills_listed", "Skills listed", 5, min(1, len(tech) / 8),
                          f"{len(tech)} recognised skills found.",
                          "List more of the tools and languages you really use, as plain words, in a Skills section."))
    else:
        out.append(_check("skills_listed", "Technical skills listed", 15, min(1, len(tech) / 12),
                          f"{len(tech)} recognised skills found" + (f": {', '.join(list(tech)[:10])}." if tech else "."),
                          "List 12 or more tools, languages and technologies you actually use. "
                          "Group them (Languages, Web, Databases, Tools) in a Skills section.",
                          ))
        cats = [c for c in by_cat if c != "soft skills"]
        out.append(_check("skill_variety", "Skills across different areas", 10, min(1, len(cats) / 4),
                          f"Skills found in {len(cats)} area(s): {', '.join(cats) or 'none'}.",
                          "Show range: languages plus a framework, a database and a tool such as Git or Docker."))
    return out, {"mode": "job" if job else "general", "found_skills": found, "by_category": by_cat, "job": job}


def impact_checks(sections):
    pool = []
    for key in ("experience", "projects", "achievements"):
        bl, marked = bullets_in(sections.get(key, []))
        pool += [(key, b) for b in bl]
    n = len(pool)
    stats = {"bullets": n, "quantified": 0, "strong_verbs": 0}
    if n < 3:
        msg = "Fewer than 3 bullet points found under Experience or Projects."
        fix = ("Describe each job or project in 2 to 4 bullet points. Start each with a verb and end with a result, "
               'for example "Built a quiz app used by 200 students".')
        return [
            _check("quantified", "Numbers and results", 8, 0, msg, fix),
            _check("verbs", "Strong action verbs", 7, 0, msg, fix),
        ], stats

    quant = [b for _, b in pool if _has_number(b)]
    plain = [b for _, b in pool if not _has_number(b)]
    stats["quantified"] = len(quant)
    ratio = len(quant) / n
    out = [_check("quantified", "Numbers and results", 8, min(1, ratio / 0.5),
                  f"{len(quant)} of {n} bullets contain a number ({round(ratio * 100)}%). Aim for at least half.",
                  "Add a number to more bullets: users, % faster, hours saved, rows processed, team size, accuracy. "
                  'Example: "Built a dashboard" becomes "Built a dashboard that cut weekly reporting time by 40%".',
                  examples=[_short(b) for b in plain[:4]])]

    strong, weak, other = [], [], []
    for _, b in pool:
        wp = _weak_start(b)
        fw = _first_word(b)
        if wp:
            weak.append((b, wp))
        elif fw in ACTION_VERBS or (fw.endswith("ed") and len(fw) > 4):
            strong.append(b)
        else:
            other.append(b)
    stats["strong_verbs"] = len(strong)
    r2 = len(strong) / n
    examples = [f'"{_short(b, 80)}"  ->  {_rewrite_hint(b, wp)}' for b, wp in weak[:3]]
    examples += [f'"{_short(b, 90)}"  ->  start with a verb like Built, Led or Improved' for b in other[:max(0, 4 - len(examples))]]
    out.append(_check("verbs", "Strong action verbs", 7, min(1, r2 / 0.75),
                      f"{len(strong)} of {n} bullets start with a strong action verb ({round(r2 * 100)}%)."
                      + (f" {len(weak)} start with a weak phrase like \"Responsible for\"." if weak else ""),
                      "Start every bullet with a past-tense verb: Built, Designed, Led, Automated, Reduced. "
                      'Replace "Responsible for" and "Worked on".',
                      examples=examples))
    return out, stats


def format_checks(text, meta, sections, bullets_marked):
    out = []
    scanned = meta.get("scanned")
    out.append(_check("parseable", "Text can be read by an ATS", 5, 0 if scanned else 1,
                      "Almost no text could be read. The file looks like a scan or a picture." if scanned else "Text extracted cleanly.",
                      "Export the resume as a text-based PDF from Word or Google Docs (File > Download > PDF). "
                      "Do not scan paper or save pictures of text."))
    words, pages = meta["words"], meta["pages"]
    est = " (estimated)" if meta.get("pages_estimated") else ""
    if pages > 2:
        r, d = 0.2, f"{pages} pages{est} and {words} words. Too long."
    elif words < 200:
        r, d = 0.3, f"Only {words} words. Too short for an ATS to find enough to match."
    elif words < 300:
        r, d = 0.7, f"{words} words on {pages} page(s){est}. A little short."
    elif words > 950:
        r, d = 0.6, f"{words} words. A bit long, trim the oldest or weakest points."
    else:
        r, d = 1, f"{words} words on {pages} page(s){est}. Good length."
    out.append(_check("length", "Length", 5, r, d,
                      "Keep it to 1 page if you are a student or have under 5 years of experience, 2 pages at most."))
    tables, images = meta.get("tables", 0), meta.get("images", 0)
    if tables or images:
        r = 0.4 if (tables and images) else 0.6
        d = f"Found {tables} table(s) and {images} image(s)."
    else:
        r, d = 1, "No tables or pictures found."
    out.append(_check("layout", "No tables, columns or pictures", 3, r, d,
                      "Many ATS read tables and text boxes in the wrong order and skip pictures. "
                      "Use a single column of plain text with simple headings. Remove photos, icons and skill-bar graphics."))
    if bullets_marked >= 3:
        r, d = 1, f"{bullets_marked} bullet points found."
    elif bullets_marked:
        r, d = 0.5, f"Only {bullets_marked} bullet point(s) found."
    else:
        r, d = 0, "No bullet characters found. Long paragraphs are hard to scan."
    out.append(_check("bullets", "Uses bullet points", 3, r, d,
                      "Put each achievement on its own bullet (•) with one idea per line."))
    dt = dates_in(text)
    total = dt["month_year"] + dt["numeric"] + dt["year_ranges"]
    if total + dt["years"] < 2:
        r, d = 0, "Almost no dates found."
    elif len(dt["styles"]) > 1:
        r, d = 0.6, "Mixed date styles: " + " and ".join(dt["styles"]) + "."
    else:
        r, d = 1, f"{total or dt['years']} dates found in a consistent style."
    out.append(_check("dates", "Dates present and consistent", 2, r, d,
                      'Add dates to education and experience and use one style everywhere, such as "Jun 2024 - Aug 2024".'))
    odd = [ch for ch in text if unicodedata.category(ch) in ("So", "Cs") or ord(ch) > 0x1F000]
    r = 1 if len(odd) <= 2 else 0.4 if len(odd) <= 8 else 0
    out.append(_check("symbols", "No odd symbols or emoji", 2, r,
                      "No unusual symbols." if r == 1 else f"{len(odd)} unusual symbols or emoji found.",
                      "Remove emoji and decorative symbols. Some ATS turn them into garbage characters."))
    return out


def content_checks(text, sections):
    out = []
    summary = " ".join(sections.get("summary", []))
    n = len(summary.split())
    out.append(_check("summary", "Short summary at the top", 3, 1 if n >= 15 else (0.4 if n else 0),
                      f"{n} words." if n else "No summary or objective found.",
                      "Add a 2 to 3 line summary under your name: who you are, your strongest skills, and the role you want. "
                      "Mention the job title you are applying for."))
    body = text
    pron = len(re.findall(r"\b(?:I|my|me|myself)\b", body))
    pron = max(0, pron - len(re.findall(r"\bI\s*[/&]\s*O\b", body)))
    out.append(_check("pronouns", 'No "I", "me" or "my"', 3, 1 if pron == 0 else 0.5 if pron <= 2 else 0,
                      "None found." if pron == 0 else f'{pron} first-person word(s) found.',
                      'Resumes are written without "I" or "my". Say "Built a chatbot" instead of "I built a chatbot".'))
    low = text.lower()
    hits = sorted({b for b in BUZZWORDS if b in low})
    out.append(_check("buzzwords", "Few clichés", 3, 1 if not hits else 0.5 if len(hits) <= 2 else 0,
                      "None found." if not hits else "Found: " + ", ".join(f'"{h}"' for h in hits) + ".",
                      "Replace claims like \"team player\" or \"hard-working\" with proof: a result, a number or a project.",
                      examples=hits))
    pool = []
    for key in ("experience", "projects", "achievements"):
        pool += bullets_in(sections.get(key, []))[0]
    if pool:
        lengths = [len(b.split()) for b in pool]
        long_ones = [b for b in pool if len(b.split()) > 35]
        avg = sum(lengths) / len(lengths)
        r = 1 if avg <= 25 and not long_ones else 0.6 if avg <= 32 else 0.3
        out.append(_check("bullet_length", "Short, readable bullets", 3, r,
                          f"Average {avg:.0f} words per bullet" + (f"; {len(long_ones)} are over 35 words." if long_ones else "."),
                          "Keep bullets to one or two lines (15 to 25 words). Split long ones into two.",
                          examples=[_short(b, 100) for b in long_ones[:3]]))
        starts = Counter(_first_word(b) for b in pool if _first_word(b))
        rep = [(w, c) for w, c in starts.items() if c >= 3]
        out.append(_check("variety", "Varied opening verbs", 3, 1 if not rep else 0.5,
                          "Good variety." if not rep else "Repeated openers: " + ", ".join(f'"{w}" x{c}' for w, c in rep) + ".",
                          "Use a different verb to open each bullet. Try Developed, Designed, Automated, Optimised, Delivered.",
                          examples=[f'"{w}" opens {c} bullets' for w, c in rep]))
    else:
        for cid, label in (("bullet_length", "Short, readable bullets"), ("variety", "Varied opening verbs")):
            out.append(_check(cid, label, 3, 0, "No bullet points to check.",
                              "Add bullet points under Experience or Projects first."))
    return out


# ----------------------------------------------------------------- the whole thing
def grade(score: float) -> tuple[str, str]:
    if score >= 85:
        return "Excellent", "Your resume is in strong shape for ATS screening."
    if score >= 70:
        return "Good", "A solid base. A few fixes will lift it into the top range."
    if score >= 50:
        return "Needs work", "Several things will cost you interviews. The fixes below are quick."
    return "Needs a rebuild", "An ATS will struggle with this resume. Start with the biggest fixes below."


def score_resume(text: str, meta: dict, jd_text: str = "") -> dict:
    sections = split_sections(text)
    contact_c, contact = contact_checks(text, sections)
    kw_c, kw = keyword_checks(text, sections, jd_text)
    impact_c, stats = impact_checks(sections)
    marked = 0
    for key in ("experience", "projects", "achievements"):
        marked += bullets_in(sections.get(key, []))[1]
    categories = {
        "contact": contact_c,
        "sections": section_checks(sections),
        "keywords": kw_c,
        "impact": impact_c,
        "format": format_checks(text, meta, sections, marked),
        "content": content_checks(text, sections),
    }
    cats = []
    total = 0.0
    for cid, checks in categories.items():
        got = round(sum(c["points"] for c in checks), 1)
        mx = sum(c["max"] for c in checks)
        total += got
        cats.append({"id": cid, "label": CATEGORY_LABELS[cid], "score": got, "max": mx, "checks": checks})
    total = round(total)

    suggestions = []
    for cat in cats:
        for c in cat["checks"]:
            gain = round(c["max"] - c["points"], 1)
            if c["status"] != "pass" and gain > 0:
                suggestions.append({
                    "id": c["id"], "category": cat["label"], "title": c["label"], "gain": gain,
                    "priority": "high" if gain >= 5 else "medium" if gain >= 2.5 else "low",
                    "problem": c["detail"], "fix": c["fix"], "examples": c["examples"],
                })
    suggestions.sort(key=lambda s: -s["gain"])
    potential = min(100, round(total + sum(s["gain"] for s in suggestions[:5])))
    label, blurb = grade(total)

    found_sections = [k for k in ("summary", "education", "experience", "projects", "skills", "certifications", "achievements")
                      if sections.get(k)]
    missing_sections = [k for k in ("education", "experience", "projects", "skills") if not sections.get(k)]
    notes = []
    if meta.get("scanned"):
        notes.append("This file looks like a scan. An ATS cannot read pictures of text, so most scores are low.")
    if meta.get("pages_estimated"):
        notes.append("Word and text files do not store page counts, so the page count is an estimate.")
    if jd_text and kw["mode"] == "general":
        notes.append("The job description was too short to use (needs at least 15 words), so general skills scoring was used.")

    job = kw["job"]
    return {
        "score": total, "grade": label, "blurb": blurb, "potential_score": potential,
        "categories": cats, "suggestions": suggestions,
        "keywords": {
            "mode": kw["mode"],
            "skills_by_category": kw["by_category"],
            "match_percent": job["percent"] if job else None,
            "similarity": job["similarity"] if job else None,
            "found": job["found"] if job else [],
            "missing": job["missing"] if job else [],
        },
        "sections": {"found": found_sections, "missing": missing_sections},
        "contact": contact, "stats": stats, "notes": notes,
    }
