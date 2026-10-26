"""Web app: upload a resume, get an ATS score and a list of fixes."""
from __future__ import annotations

import json
import secrets
import time
from collections import OrderedDict
from pathlib import Path

from fastapi import FastAPI, File, Form, HTTPException, UploadFile
from fastapi.concurrency import run_in_threadpool
from fastapi.responses import FileResponse, PlainTextResponse, Response
from fastapi.staticfiles import StaticFiles

from analyzer import MAX_BYTES, AnalyzerError, analyze_bytes

BASE = Path(__file__).parent
MAX_JOBS = 25

app = FastAPI(title="ResumeRadar")
app.mount("/static", StaticFiles(directory=BASE / "static"), name="static")
RESULTS: "OrderedDict[str, dict]" = OrderedDict()


@app.get("/")
def home():
    return FileResponse(BASE / "static" / "index.html")


@app.get("/api/sample/{name}")
def sample(name: str):
    allowed = {"strong": "strong_resume.pdf", "weak": "weak_resume.docx", "job": "job_description_data_analyst.txt"}
    if name not in allowed:
        raise HTTPException(404, "Unknown sample.")
    path = BASE / "sample_resumes" / allowed[name]
    if not path.exists():
        raise HTTPException(404, "Sample file is missing. Run: python tools/make_samples.py")
    return FileResponse(path, filename=path.name)


@app.post("/api/analyze")
async def analyze(file: UploadFile = File(...), job_description: str = Form("")):
    data = await file.read(MAX_BYTES + 1)
    if len(data) > MAX_BYTES:
        raise HTTPException(413, f"The file is larger than {MAX_BYTES // (1024 * 1024)} MB.")
    if len(job_description) > 20000:
        raise HTTPException(413, "The job description is too long. Paste the main part only.")
    try:
        result = await run_in_threadpool(analyze_bytes, data, file.filename or "resume", job_description)
    except AnalyzerError as exc:
        raise HTTPException(422, str(exc))
    except Exception:
        raise HTTPException(500, "Something went wrong while reading this file. Try exporting it as a fresh PDF.")
    job_id = secrets.token_urlsafe(8)
    RESULTS[job_id] = result
    while len(RESULTS) > MAX_JOBS:
        RESULTS.popitem(last=False)
    return {"job_id": job_id, "result": result}


def _get(job_id: str) -> dict:
    if job_id not in RESULTS:
        raise HTTPException(404, "That report has expired. Analyse the resume again.")
    return RESULTS[job_id]


@app.get("/api/report/{job_id}")
def report_json(job_id: str):
    r = _get(job_id)
    return Response(json.dumps(r, indent=2), media_type="application/json",
                    headers={"Content-Disposition": 'attachment; filename="resume_report.json"'})


@app.get("/api/plan/{job_id}")
def action_plan(job_id: str):
    r = _get(job_id)
    lines = [f"ATS REPORT - {r['file']['name']}", f"Score: {r['score']}/100 ({r['grade']})",
             f"Could reach about {r['potential_score']}/100 after the fixes below.", "", "WHAT TO FIX, BIGGEST WIN FIRST", ""]
    for i, s in enumerate(r["suggestions"], 1):
        lines += [f"{i}. [{s['priority'].upper()}] {s['title']}  (+{s['gain']} points)",
                  f"   Found: {s['problem']}", f"   Fix:   {s['fix']}"]
        for ex in s["examples"]:
            lines.append(f"     - {ex}")
        lines.append("")
    if r["keywords"]["missing"]:
        lines += ["MISSING KEYWORDS FROM THE JOB DESCRIPTION", "  " + ", ".join(r["keywords"]["missing"]), ""]
    return PlainTextResponse("\n".join(lines), headers={"Content-Disposition": 'attachment; filename="resume_action_plan.txt"'})
