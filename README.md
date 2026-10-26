# ResumeRadar

Upload a resume (PDF, DOCX or TXT). Get an ATS score out of 100, the exact lines to change, and a ranked
list of fixes that says how many points each one is worth. Paste a job description to also see which
keywords your resume is missing for that job.

## Run it

```bash
pip install -r requirements.txt
uvicorn app:app --reload
```

Open http://127.0.0.1:8000, click **Strong resume** or **Weak resume** to try a sample, then **Check my resume**.

```bash
python -m pytest        # 34 tests
python tools/make_samples.py   # rebuilds the sample resumes
```

## Tech stack

| Part | Choice | Why |
|---|---|---|
| Language | Python 3.11+ | Same stack as Kleenly |
| PDF reading | pdfplumber | Gives text, page count, tables and images |
| Word reading | python-docx | Reads paragraphs, list bullets, tables, headers |
| Keyword similarity | scikit-learn TF-IDF + cosine | Small, explainable, no model download |
| API | FastAPI + uvicorn | Small, typed, easy to test |
| UI | HTML, CSS, JavaScript (no framework) | Served from `static/` |
| Tests | pytest | One test per rule |

## How the score works (100 points)

| Category | Points | What is checked |
|---|---|---|
| Contact details | 10 | email, phone, LinkedIn, GitHub or portfolio, professional email |
| Sections | 15 | Education, Experience or Internships, Skills, Projects |
| Keywords and skills | 25 | With a job description: % of its keywords you have. Without: number and variety of known skills |
| Impact of bullets | 15 | share of bullets with a number, share starting with a strong action verb |
| Formatting for ATS | 20 | text readable, length, no tables or pictures, bullets used, consistent dates, no emoji |
| Writing quality | 15 | summary, no "I/my", no clichés, short bullets, varied opening verbs |

Each check returns points, what it found, how to fix it and examples taken from the resume itself.
The suggestions list is each failed check sorted by points lost, so the first item is the biggest win.
"Could reach about N" adds the points of the top five fixes.

```
upload -> extract text -> find sections, bullets, contact, dates -> run 6 groups of checks
       -> score + ranked fixes -> JSON for the page, plus a downloadable action plan
```

## Files

```
app.py                 FastAPI app: /api/analyze, /api/plan/{id}, /api/report/{id}
analyzer/extract.py    PDF/DOCX/TXT to clean text, page count, tables, images
analyzer/parse.py      sections, bullets (wrapped lines glued back), contact, dates
analyzer/keywords.py   skill detection, job description matching, TF-IDF similarity
analyzer/score.py      the six categories, grades, ranked suggestions
analyzer/knowledge.py  word lists: section names, action verbs, skills, clichés
static/                index.html, style.css, app.js
sample_resumes/        strong and weak resume, sample job description
tests/                 test_analyzer.py (rules), test_api.py (endpoints)
```

## Decisions worth explaining in a viva

- **Rules, not a black box.** Every point can be traced to a check with a reason. A student can see why the score is 63 and what to change.
- **Resumes are not stored.** Reports sit in memory for the last 25 analyses only.
- **Job description is optional but changes the scoring.** Keywords are only judged against a real job when you supply one.
- **Ambiguous words are guarded.** "Go" and "R" count as languages only when written with capitals inside a Skills section, so "go to market" does not score.
- **PDF quirks are repaired.** Symbol-font bullets come out of PDF readers as `(cid:127)`; they are turned back into bullets.

## Limits (be honest about these)

- This is a rule-based checker with TF-IDF similarity. It is **not** a language model and it cannot judge whether your achievements are impressive or true.
- Real ATS products (Workday, Greenhouse, Lever, Taleo) each parse differently and publish no scoring formula. The number here estimates how well a resume follows common ATS advice. Treat it as a guide, not a guarantee.
- Scanned or picture-only PDFs are rejected: no text can be read from them (the same thing an ATS would face).
- Word and text files have no stored page count, so pages are estimated at about 550 words per page.
- The skill list covers common tech, data and business skills. Other fields would need their own list in `analyzer/knowledge.py`.
- Two-column layouts can be read in the wrong order by PDF readers; the app warns about tables and pictures but cannot always detect columns.
