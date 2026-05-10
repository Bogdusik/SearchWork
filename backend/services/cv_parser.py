import io
import pypdf
from pdfminer.high_level import extract_text as pdfminer_extract


def extract_text_from_pdf(pdf_bytes: bytes) -> str:
    """Extract plain text from PDF bytes. Falls back to pdfminer if pypdf yields nothing.

    Broad exception catch on pypdf is intentional — pypdf raises various exception types
    depending on PDF corruption/format issues, and we always want the pdfminer fallback.
    """
    try:
        reader = pypdf.PdfReader(io.BytesIO(pdf_bytes))
        text = "\n".join(page.extract_text() or "" for page in reader.pages)
        if text.strip():
            return text
    except Exception:
        pass
    try:
        return pdfminer_extract(io.BytesIO(pdf_bytes)) or ""
    except Exception:
        return ""
