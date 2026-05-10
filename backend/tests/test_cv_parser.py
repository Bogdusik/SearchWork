import pytest
from services.cv_parser import extract_text_from_pdf


def test_extract_text_returns_string():
    with open("tests/fixtures/sample_cv.pdf", "rb") as f:
        result = extract_text_from_pdf(f.read())
    assert isinstance(result, str)


def test_extract_text_does_not_crash_on_valid_pdf():
    """Parser must not raise for a valid PDF — returning empty string is acceptable."""
    with open("tests/fixtures/sample_cv.pdf", "rb") as f:
        pdf_bytes = f.read()
    # This call must not raise
    result = extract_text_from_pdf(pdf_bytes)
    assert isinstance(result, str)


def test_extract_text_returns_string_for_garbage_input():
    """Parser must return a string (possibly empty) rather than raising for invalid input."""
    garbage = b"not a pdf at all"
    result = extract_text_from_pdf(garbage)
    assert isinstance(result, str)
