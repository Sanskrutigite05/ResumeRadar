"""Creates the two sample resumes in sample_resumes/. Run: python tools/make_samples.py"""
from pathlib import Path

import docx
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import mm
from reportlab.platypus import Paragraph, SimpleDocTemplate, Spacer

OUT = Path(__file__).resolve().parent.parent / "sample_resumes"
OUT.mkdir(exist_ok=True)

GOOD = [
    ("h", "Riya Deshmukh"),
    ("p", "riya.deshmukh@gmail.com | +91 98765 43210 | Nashik, Maharashtra"),
    ("p", "linkedin.com/in/riyadeshmukh | github.com/riyadeshmukh"),
    ("s", "Summary"),
    ("p", "Computer Science student with hands-on experience building data tools in Python and SQL. "
          "Shipped two full-stack projects used by 300+ students. Seeking a data analyst internship."),
    ("s", "Education"),
    ("p", "B.Tech in Computer Science and Design, K.K. Wagh Institute of Engineering, Nashik | 2023 - 2027"),
    ("p", "CGPA: 9.01 / 10"),
    ("s", "Experience"),
    ("p", "Data Analyst Intern, BrightLeaf Analytics | Jun 2025 - Aug 2025"),
    ("b", "Automated weekly sales reports with Python and pandas, cutting manual work by 12 hours per week."),
    ("b", "Built a Power BI dashboard tracking 8 KPIs for a team of 25, adopted by 3 departments."),
    ("b", "Cleaned and validated 200,000+ records using SQL, improving data accuracy from 91% to 99%."),
    ("b", "Presented findings to senior managers, leading to a 15% reduction in stock-outs."),
    ("s", "Projects"),
    ("p", "Kleenly - Automatic CSV Cleaner | Python, FastAPI, scikit-learn"),
    ("b", "Developed a data-cleaning web app that detects missing values, duplicates and outliers in uploaded files."),
    ("b", "Implemented Isolation Forest and KNN imputation, with 36 automated tests passing."),
    ("b", "Designed a two-page interface used by 40 classmates during a department demo."),
    ("p", "Expense Tracker App | Flutter, Firebase"),
    ("b", "Launched an Android app with 150 active users and a 4.6 star rating."),
    ("b", "Optimised database queries, reducing screen load time by 35%."),
    ("s", "Skills"),
    ("p", "Languages: Python, SQL, Java, JavaScript, HTML, CSS"),
    ("p", "Data and AI: pandas, NumPy, scikit-learn, Machine Learning, Power BI, Excel, Data Analysis"),
    ("p", "Tools: Git, GitHub, Docker, Flutter, Firebase, FastAPI, MySQL, REST API"),
    ("s", "Achievements"),
    ("b", "Won first place in a college hackathon among 60 teams."),
    ("b", "Led a team of 6 for the department technical fest."),
]


def pdf(path: Path, items):
    styles = getSampleStyleSheet()
    h = ParagraphStyle("h", parent=styles["Title"], fontSize=20, alignment=0, spaceAfter=2)
    s = ParagraphStyle("s", parent=styles["Heading2"], fontSize=12, spaceBefore=8, spaceAfter=2)
    p = ParagraphStyle("p", parent=styles["BodyText"], fontSize=9.5, leading=12)
    b = ParagraphStyle("b", parent=p, leftIndent=12, bulletIndent=2)
    doc = SimpleDocTemplate(str(path), pagesize=A4, leftMargin=16 * mm, rightMargin=16 * mm,
                            topMargin=14 * mm, bottomMargin=12 * mm)
    flow = []
    for kind, text in items:
        if kind == "h": flow.append(Paragraph(text, h))
        elif kind == "s": flow.append(Paragraph(text.upper(), s))
        elif kind == "p": flow.append(Paragraph(text, p))
        else: flow.append(Paragraph(text, b, bulletText="•"))
    doc.build(flow)


def weak_docx(path: Path):
    d = docx.Document()
    d.add_paragraph("rahul_cool_boy2002@gmail.com")
    d.add_paragraph("RAHUL PATIL")
    d.add_paragraph("I am a hard-working and passionate fresher and a team player seeking a challenging position "
                    "in a reputed company where I can use my skills.")
    d.add_paragraph("EDUCATION")
    d.add_paragraph("B.E. Computer, Pune University, 2024")
    d.add_paragraph("EXPERIENCE")
    for t in ["Responsible for managing the college website",
              "Worked on a project about attendance",
              "Helped with testing of the software and did many tasks",
              "I was involved in making reports for my teacher and I learned a lot about teamwork and many other things "
              "that are useful for my career and future growth in the industry as a whole"]:
        d.add_paragraph(t, style="List Bullet")
    d.add_paragraph("SKILLS")
    table = d.add_table(rows=2, cols=2)
    table.cell(0, 0).text = "Programming"; table.cell(0, 1).text = "C, Java"
    table.cell(1, 0).text = "Other"; table.cell(1, 1).text = "MS Office, Good communication skills"
    d.save(str(path))


if __name__ == "__main__":
    pdf(OUT / "strong_resume.pdf", GOOD)
    weak_docx(OUT / "weak_resume.docx")
    (OUT / "job_description_data_analyst.txt").write_text(
        "Data Analyst Intern\n\nWe are looking for a data analyst intern to work with our analytics team. "
        "You will clean and analyse data using Python and SQL, build dashboards in Tableau or Power BI, "
        "and present insights to stakeholders. Experience with pandas, Excel and statistics is required. "
        "Knowledge of machine learning, A/B testing and cloud platforms such as AWS is a plus. "
        "Strong communication skills and attention to detail. You will automate recurring reporting "
        "and maintain dashboards used by business teams.\n", encoding="utf-8")
    print("sample resumes written to", OUT)
