import io

from pypdf import PdfReader
from fastapi import UploadFile


ALLOWED_EXTENSIONS = {".txt", ".pdf"}


def extract_text_from_upload(file: UploadFile) -> str:
    """
    Reads an uploaded .txt or .pdf file and returns its plain text content.
    Raises ValueError for unsupported file types or unreadable/empty content.
    """
    filename = file.filename or ""
    extension = "." + filename.rsplit(".", 1)[-1].lower() if "." in filename else ""

    if extension not in ALLOWED_EXTENSIONS:
        raise ValueError(
            f"Unsupported file type '{extension}'. Only .txt and .pdf are allowed."
        )

    raw_bytes = file.file.read()

    if extension == ".txt":
        text = raw_bytes.decode("utf-8", errors="ignore")
    else:  # .pdf
        try:
            reader = PdfReader(io.BytesIO(raw_bytes))
            pages_text = [page.extract_text() or "" for page in reader.pages]
            text = "\n".join(pages_text)
        except Exception as e:
            raise ValueError(f"Could not read PDF file: {e}") from e

    text = text.strip()
    if not text:
        raise ValueError(
            "No extractable text found in the file. "
            "(Scanned/image-only PDFs aren't supported without OCR.)"
        )

    return text