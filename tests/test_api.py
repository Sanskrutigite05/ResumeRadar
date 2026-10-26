from pathlib import Path

import pytest
from fastapi.testclient import TestClient

import app as app_module
from app import app

SAMPLES = Path(__file__).parent.parent / "sample_resumes"
client = TestClient(app)


def post(content: bytes, name="r.txt", jd=""):
    return client.post("/api/analyze", files={"file": (name, content)}, data={"job_description": jd})


def test_home_assets_and_samples_load():
    assert client.get("/").status_code == 200
    assert client.get("/static/app.js").status_code == 200
    assert client.get("/static/style.css").status_code == 200
    for key in ("strong", "weak", "job"):
        assert client.get(f"/api/sample/{key}").status_code == 200
    assert client.get("/api/sample/nope").status_code == 404


def test_analyze_then_download_plan_and_report():
    res = post((SAMPLES / "weak_resume.docx").read_bytes(), "weak_resume.docx",
               (SAMPLES / "job_description_data_analyst.txt").read_text())
    assert res.status_code == 200
    body = res.json()
    assert 0 <= body["result"]["score"] <= 100 and body["result"]["suggestions"]
    plan = client.get(f"/api/plan/{body['job_id']}")
    assert plan.status_code == 200 and "WHAT TO FIX" in plan.text
    assert client.get(f"/api/report/{body['job_id']}").json()["score"] == body["result"]["score"]


def test_strong_sample_scores_higher_than_weak():
    strong = post((SAMPLES / "strong_resume.pdf").read_bytes(), "s.pdf").json()["result"]["score"]
    weak = post((SAMPLES / "weak_resume.docx").read_bytes(), "w.docx").json()["result"]["score"]
    assert strong >= 85 and weak <= 50


@pytest.mark.parametrize("content, name", [(b"", "a.pdf"), (b"%PDF-1.4 junk", "a.pdf"), (b"abc", "a.doc")])
def test_bad_uploads_get_clear_errors(content, name):
    res = post(content, name)
    assert res.status_code == 422 and res.json()["detail"]


def test_oversized_upload_rejected(monkeypatch):
    monkeypatch.setattr(app_module, "MAX_BYTES", 1000)
    res = post(b"a" * 5000)
    assert res.status_code == 413


def test_unknown_report_is_404():
    assert client.get("/api/plan/missing").status_code == 404
