"""One test per rule. Resumes are built in memory so the tests need no files on disk."""
import io

import docx
import pytest

from analyzer import AnalyzerError, analyze_bytes
from analyzer.extract import extract
from analyzer.keywords import find_skills, match_job
from analyzer.parse import bullets_in, contact_info, split_sections

GOOD_TXT = """Riya Deshmukh
riya.deshmukh@gmail.com | +91 98765 43210 | linkedin.com/in/riyadeshmukh | github.com/riyadeshmukh

SUMMARY
Computer Science student with hands-on experience building data tools in Python and SQL. Shipped two projects used by 300 students.

EDUCATION
B.Tech in Computer Science, K.K. Wagh Institute, Nashik | 2023 - 2027

EXPERIENCE
Data Analyst Intern, BrightLeaf | Jun 2025 - Aug 2025
• Automated weekly sales reports with Python and pandas, cutting manual work by 12 hours per week.
• Built a Power BI dashboard tracking 8 KPIs for a team of 25 people across 3 departments.
• Cleaned 200,000 records using SQL, improving accuracy from 91% to 99% for the finance team.
• Presented findings to managers, leading to a 15% reduction in stock-outs last year.

PROJECTS
Kleenly - CSV Cleaner | Python, FastAPI, scikit-learn
• Developed a data-cleaning web app that detects missing values, duplicates and outliers in files.
• Implemented Isolation Forest and KNN imputation, with 36 automated tests passing in CI.
• Designed a two-page interface used by 40 classmates during a department demo day.

SKILLS
Languages: Python, SQL, Java, JavaScript, HTML, CSS
Data: pandas, NumPy, scikit-learn, Machine Learning, Power BI, Excel, Data Analysis
Tools: Git, GitHub, Docker, Flutter, Firebase, FastAPI, MySQL, REST API
"""

BAD_TXT = """rahul_cool_boy2002@gmail.com
RAHUL PATIL
I am a hard-working and passionate fresher and a team player.
EDUCATION
B.E. Computer, Pune University, 2024
EXPERIENCE
- Responsible for managing the college website
- Worked on a project about attendance
- Helped with testing of the software
SKILLS
C, Java
"""


def run(text, jd="", name="r.txt"):
    return analyze_bytes(text.encode(), name, jd)


def check(result, cid):
    for cat in result["categories"]:
        for c in cat["checks"]:
            if c["id"] == cid:
                return c
    raise KeyError(cid)


# ------------------------------------------------------------------ extraction
def test_txt_pdf_and_docx_all_extract():
    text, meta = extract(GOOD_TXT.encode(), "a.txt")
    assert "Riya" in text and meta["kind"] == "txt"

    d = docx.Document()
    d.add_paragraph("Jane Doe")
    d.add_paragraph("EXPERIENCE")
    d.add_paragraph("Built a dashboard that cut reporting time by 40 percent", style="List Bullet")
    buf = io.BytesIO(); d.save(buf)
    text, meta = extract(buf.getvalue(), "a.docx")
    assert meta["kind"] == "docx" and "• Built a dashboard" in text


def test_pdf_symbol_bullets_are_repaired(tmp_path):
    from reportlab.lib.styles import getSampleStyleSheet
    from reportlab.platypus import Paragraph, SimpleDocTemplate
    path = tmp_path / "x.pdf"
    st = getSampleStyleSheet()["BodyText"]
    SimpleDocTemplate(str(path)).build([Paragraph("EXPERIENCE", st), Paragraph("Built a thing", st, bulletText="•")])
    text, meta = extract(path.read_bytes(), "x.pdf")
    assert "(cid:" not in text and "• Built a thing" in text and meta["pages"] == 1


@pytest.mark.parametrize("data, name", [(b"", "a.pdf"), (b"%PDF-1.4 garbage", "a.pdf"), (b"PK\x03\x04junk", "a.docx"),
                                        (b"x" * 10, "old.doc"), (b"\x00\x01\x02" * 100, "a.bin")])
def test_bad_files_get_clear_errors(data, name):
    with pytest.raises(AnalyzerError):
        analyze_bytes(data, name)


def test_too_big_file_rejected():
    with pytest.raises(AnalyzerError):
        extract(b"a" * (5 * 1024 * 1024 + 1), "a.txt")


# ---------------------------------------------------------------------- parsing
def test_sections_found_with_aliases():
    s = split_sections("Name\nTECHNICAL SKILLS:\nPython\nAcademic Projects\n• x\nWork Experience\n• y")
    assert set(s) >= {"header", "skills", "projects", "experience"}


def test_wrapped_bullet_lines_are_joined():
    bl, marked = bullets_in(["• Built a tool that", "reduced time by 20%", "• Second bullet here."])
    assert marked == 2 and bl[0] == "Built a tool that reduced time by 20%"


def test_contact_detection():
    c = contact_info("a.b@c.com +91 98765 43210 linkedin.com/in/ab github.com/ab", [])
    assert c["email"] and c["phone"] and c["linkedin"] and c["github"]
    assert contact_info("B.Tech 2023 - 2027 CGPA 9.01", [])["portfolio"] is None
    assert contact_info("Phone 2023 2027", [])["phone"] is None


# --------------------------------------------------------------------- keywords
def test_skill_detection_and_aliases():
    found = find_skills("Used JS, node.js, scikit-learn, ML and Power BI. Went to market.")
    assert {"javascript", "node.js", "scikit-learn", "machine learning", "power bi"} <= set(found)
    assert "go" not in found  # "market" must not count as Go


def test_single_letter_languages_only_in_skills_section():
    assert "r" not in find_skills("R is mentioned here", "")
    assert "r" in find_skills("x", "Languages: Python, R, SQL")


def test_job_match_finds_missing_keywords():
    skills = find_skills("Python and SQL", "Python, SQL")
    m = match_job("Python and SQL", skills, "We need Python, SQL, Tableau and Power BI skills for this analytics role today.")
    assert "tableau" in m["missing"] and "python" in m["found"] and 0 < m["percent"] < 100


# ---------------------------------------------------------------------- scoring
def test_good_resume_scores_high_and_bad_scores_low():
    good, bad = run(GOOD_TXT), run(BAD_TXT)
    assert good["score"] >= 80, good["score"]
    assert bad["score"] < 55, bad["score"]
    assert good["score"] - bad["score"] >= 35


def test_category_maximums_add_to_100():
    r = run(GOOD_TXT)
    assert sum(c["max"] for c in r["categories"]) == 100
    assert sum(c["max"] for c in run(GOOD_TXT, "x " * 5)["categories"]) == 100
    jd = "Looking for a data analyst skilled in Python, SQL and Tableau to build dashboards for business teams every day."
    assert sum(c["max"] for c in run(GOOD_TXT, jd)["categories"]) == 100


def test_score_equals_sum_of_check_points():
    r = run(BAD_TXT)
    assert r["score"] == round(sum(c["points"] for cat in r["categories"] for c in cat["checks"]))


def test_missing_contact_details_are_reported():
    r = run(BAD_TXT)
    assert check(r, "phone")["status"] == "fail" and check(r, "links")["status"] == "fail"
    assert check(r, "email_style")["points"] < 1  # cool_boy2002


def test_weak_bullets_get_rewrite_suggestions():
    r = run(BAD_TXT)
    verbs = check(r, "verbs")
    assert verbs["status"] != "pass"
    assert any("Managed the college website" in e for e in verbs["examples"])


def test_quantified_bullets_counted():
    r = run(GOOD_TXT)
    assert check(r, "quantified")["status"] == "pass"
    assert r["stats"]["quantified"] >= 6


def test_cliches_and_pronouns_flagged():
    r = run(BAD_TXT)
    assert "hard-working" in " ".join(check(r, "buzzwords")["examples"])
    r2 = run(BAD_TXT + "\nI built a thing and my team liked it, I think.")
    assert check(r2, "pronouns")["status"] != "pass"


def test_job_description_changes_keyword_scoring():
    jd = ("We want a backend engineer with Rust, Kubernetes, Terraform and GraphQL experience to join our platform team "
          "and build services every day with strong testing habits.")
    plain, with_jd = run(GOOD_TXT), run(GOOD_TXT, jd)
    assert plain["keywords"]["mode"] == "general" and with_jd["keywords"]["mode"] == "job"
    assert "kubernetes" in with_jd["keywords"]["missing"]
    assert with_jd["score"] < plain["score"]


def test_short_job_description_is_ignored_with_a_note():
    r = run(GOOD_TXT, "python please")
    assert r["keywords"]["mode"] == "general" and r["notes"]


def test_suggestions_sorted_by_gain_and_potential_is_capped():
    r = run(BAD_TXT)
    gains = [s["gain"] for s in r["suggestions"]]
    assert gains == sorted(gains, reverse=True) and gains[0] > 0
    assert r["score"] < r["potential_score"] <= 100


def test_scanned_pdf_is_detected(tmp_path):
    from reportlab.pdfgen import canvas
    path = tmp_path / "scan.pdf"
    c = canvas.Canvas(str(path)); c.rect(50, 50, 300, 300, fill=1); c.save()
    with pytest.raises(AnalyzerError):
        analyze_bytes(path.read_bytes(), "scan.pdf")  # no text at all


def test_analysis_is_deterministic():
    assert run(GOOD_TXT) == run(GOOD_TXT)
