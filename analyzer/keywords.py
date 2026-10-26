"""Skill detection and job-description matching.

Plain pattern matching finds known skills. TF-IDF cosine similarity gives one overall
'how alike are these two texts' number. No model is downloaded and nothing leaves the machine.
"""
from __future__ import annotations

import re
from collections import Counter

from .knowledge import SKILLS, STOPWORDS

# Words that are also ordinary English or single letters. Only counted inside a skills section, and
# case-sensitively, so "go to market" does not count as the Go language.
AMBIGUOUS = {"go": "Go", "r": "R", "c": "C"}

_CATEGORY_OF: dict[str, str] = {}
_PATTERNS: dict[str, re.Pattern] = {}
_ALIAS_TO_CANON: dict[str, str] = {}

for _cat, _skills in SKILLS.items():
    for _canon, _aliases in _skills.items():
        _CATEGORY_OF[_canon] = _cat
        for _name in [_canon, *_aliases]:
            _ALIAS_TO_CANON[_name] = _canon


def _pattern(name: str) -> re.Pattern:
    if name not in _PATTERNS:
        body = re.escape(name).replace(r"\ ", r"[\s\-]+")
        _PATTERNS[name] = re.compile(rf"(?<![\w+#./-]){body}(?![\w+#]|\.\w)", re.I)
    return _PATTERNS[name]


def find_skills(text: str, skills_text: str = "") -> dict[str, str]:
    """Return {canonical skill: category} for every known skill found in the text."""
    found: dict[str, str] = {}
    lowered = text.lower()
    for name, canon in _ALIAS_TO_CANON.items():
        if name in AMBIGUOUS:
            continue
        if canon not in found and name in lowered and _pattern(name).search(text):
            found[canon] = _CATEGORY_OF[canon]
    for name, cased in AMBIGUOUS.items():
        if re.search(rf"(?<![\w+#./-]){cased}(?![\w+#]|\.\w)", skills_text or ""):
            found[name] = _CATEGORY_OF[name]
    return found


def _words(text: str) -> list[str]:
    return [w for w in re.findall(r"[a-z][a-z+#.\-]{2,}", text.lower())]


def _stem(w: str) -> str:
    w = w.strip(".-")
    for suffix in ("ing", "es", "s", "ed"):
        if w.endswith(suffix) and len(w) - len(suffix) >= 4:
            return w[: -len(suffix)]
    return w


def match_job(resume_text: str, resume_skills: dict[str, str], jd_text: str) -> dict:
    jd_skills = find_skills(jd_text, jd_text)
    jd_words = [w for w in _words(jd_text) if w not in STOPWORDS]
    covered = {_stem(a) for a in _ALIAS_TO_CANON}
    counts = Counter(_stem(w) for w in jd_words if _stem(w) not in covered)
    others = [w for w, c in counts.most_common(40) if c >= 2][:10]

    resume_stems = {_stem(w) for w in _words(resume_text)}
    required, found, missing = [], [], []
    for canon in list(jd_skills)[:25]:
        required.append(canon)
        (found if canon in resume_skills else missing).append(canon)
    for w in others:
        required.append(w)
        (found if w in resume_stems else missing).append(w)

    similarity = None
    try:
        from sklearn.feature_extraction.text import TfidfVectorizer
        from sklearn.metrics.pairwise import cosine_similarity

        vec = TfidfVectorizer(stop_words="english", ngram_range=(1, 2), sublinear_tf=True)
        m = vec.fit_transform([resume_text, jd_text])
        similarity = round(float(cosine_similarity(m[0], m[1])[0][0]) * 100)
    except Exception:
        pass

    pct = round(100 * len(found) / len(required)) if required else None
    return {"required": required, "found": found, "missing": missing, "percent": pct, "similarity": similarity}
