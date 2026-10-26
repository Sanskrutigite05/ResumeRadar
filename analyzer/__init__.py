from .errors import AnalyzerError
from .extract import MAX_BYTES, extract
from .score import score_resume


def analyze_bytes(data: bytes, filename: str, job_description: str = "") -> dict:
    text, meta = extract(data, filename)
    if meta["words"] < 5:
        raise AnalyzerError("No readable text was found in this file.")
    result = score_resume(text, meta, (job_description or "").strip())
    result["file"] = {"name": filename, "kind": meta["kind"], "pages": meta["pages"], "words": meta["words"],
                      "pages_estimated": bool(meta.get("pages_estimated"))}
    return result
