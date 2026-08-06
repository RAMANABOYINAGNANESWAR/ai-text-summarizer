# NEW:
from pathlib import Path

from fastapi import FastAPI, HTTPException, UploadFile, File, Form
from fastapi.responses import HTMLResponse

from app.schemas import SummarizeRequest, SummarizeResponse, ErrorResponse
from app.services.summarizer import summarize_text
from app.services.extractor import extract_text_from_upload

app = FastAPI(
    title="AI Text Summarizer",
    description="A small FastAPI service that summarizes text using an LLM.",
    version="1.0.0",
)

STATIC_DIR = Path(__file__).parent / "static"


@app.get("/", response_class=HTMLResponse)
def frontend():
    return (STATIC_DIR / "index.html").read_text(encoding="utf-8")


@app.get("/health")
def health_check():
    return {"status": "ok"}


@app.post(
    "/summarize",
    response_model=SummarizeResponse,
    responses={502: {"model": ErrorResponse}},
)
def summarize(payload: SummarizeRequest):
    try:
        summary = summarize_text(text=payload.text, max_words=payload.max_words)
    except RuntimeError as e:
        # Upstream LLM/provider failure -> 502 Bad Gateway, not a 500
        raise HTTPException(status_code=502, detail=str(e))

    return SummarizeResponse(
        summary=summary,
        original_length_words=len(payload.text.split()),
        summary_length_words=len(summary.split()),
    )


@app.post(
    "/summarize/file",
    response_model=SummarizeResponse,
    responses={400: {"model": ErrorResponse}, 502: {"model": ErrorResponse}},
)
def summarize_file(file: UploadFile = File(...), max_words: int = Form(default=60)):
    try:
        text = extract_text_from_upload(file)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

    if not (10 <= max_words <= 500):
        raise HTTPException(status_code=400, detail="max_words must be between 10 and 500.")

    try:
        summary = summarize_text(text=text, max_words=max_words)
    except RuntimeError as e:
        raise HTTPException(status_code=502, detail=str(e))

    return SummarizeResponse(
        summary=summary,
        original_length_words=len(text.split()),
        summary_length_words=len(summary.split()),
    )