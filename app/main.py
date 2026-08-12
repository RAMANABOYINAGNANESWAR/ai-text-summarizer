# NEW:
from pathlib import Path

from fastapi import FastAPI, HTTPException, UploadFile, File, Form
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles

from app.schemas import SummarizeRequest, SummarizeResponse, ErrorResponse
from app.services.summarizer import summarize_text
from app.services.extractor import extract_text_from_upload

from app.schemas import ClassifyRequest, ClassifyResponse
from app.services.classifier import classify_text

from app.database import init_db, save_record, get_history

app = FastAPI(
    title="AI Text Summarizer",
    description="A small FastAPI service that summarizes text using an LLM.",
    version="1.0.0",
)

@app.on_event("startup")
def on_startup():
    init_db()

STATIC_DIR = Path(__file__).parent / "static"
app.mount("/static", StaticFiles(directory=STATIC_DIR), name="static")


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
        raise HTTPException(status_code=502, detail=str(e))

    response = SummarizeResponse(
        summary=summary,
        original_length_words=len(payload.text.split()),
        summary_length_words=len(summary.split()),
    )
    save_record("summarize", payload.text, response.model_dump_json())
    return response


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
    
@app.post(
    "/classify",
    response_model=ClassifyResponse,
    responses={502: {"model": ErrorResponse}},
)
def classify(payload: ClassifyRequest):
    try:
        result = classify_text(text=payload.text)
    except RuntimeError as e:
        raise HTTPException(status_code=502, detail=str(e))

    response = ClassifyResponse(**result)
    save_record("classify", payload.text, response.model_dump_json())
    return response

@app.get("/history")
def history(limit: int = 20):
    records = get_history(limit=limit)
    return [
        {
            "id": r.id,
            "request_type": r.request_type,
            "input_text": r.input_text,
            "output": r.output_json,
            "created_at": r.created_at.isoformat(),
        }
        for r in records
    ]