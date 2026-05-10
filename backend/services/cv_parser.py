import io
import PyPDF2
from pdfminer.high_level import extract_text as pdfminer_extract


def extract_text_from_pdf(pdf_bytes: bytes) -> str:
    """Extract plain text from PDF bytes. Falls back to pdfminer if PyPDF2 yields nothing."""
    try:
        reader = PyPDF2.PdfReader(io.BytesIO(pdf_bytes))
        text = "\n".join(page.extract_text() or "" for page in reader.pages)
        if text.strip():
            return text
    except Exception:
        pass
    return pdfminer_extract(io.BytesIO(pdf_bytes)) or ""
