"""
OCR Stub: Attempts to extract salary from uploaded PDF.
If it fails or the value looks unrealistic, falls back to a demo value (45,000).

This is still a "stub" because full OCR for images is not implemented.
But for PDF salary slips with text, it will often work and stay realistic.
"""

import re
from typing import Optional

from PyPDF2 import PdfReader


def _extract_salary_from_text(text: str) -> Optional[int]:
    """
    Try to extract a salary-like number from raw text.

    Strategy:
    - Remove commas
    - Find all numbers with 4–7 digits (e.g., 15000, 45000, 120000, 800000)
    - Apply simple heuristics to map annual → monthly when needed.
    """
    if not text:
        return None

    cleaned = text.replace(",", "")
    candidates = re.findall(r"\d{4,7}", cleaned)
    if not candidates:
        return None

    nums = [int(x) for x in candidates]

    # Heuristic:
    #  - If we see something like 3–9 LPA (300000–900000) → treat as annual, convert to monthly
    #  - If we see something between 25k–200k → treat as monthly (reasonable range)
    monthly_candidates = []

    for n in nums:
        # If it looks like annual CTC (3L–20L), convert to monthly
        if 300000 <= n <= 2000000:
            approx_monthly = int(n / 12)
            monthly_candidates.append(approx_monthly)
        # If it already looks like a monthly salary (25k–200k), keep as is
        elif 25000 <= n <= 200000:
            monthly_candidates.append(n)

    if not monthly_candidates:
        return None

    # Choose the largest "reasonable" monthly salary
    return max(monthly_candidates)


def parse_salary(file_storage) -> int:
    """
    Main OCR stub entry point.

    file_storage: Flask's FileStorage object from request.files["file"]

    - If it's a PDF:
        * Read first 1–2 pages with PyPDF2
        * Extract text
        * Try to find a realistic monthly salary
    - If parsing fails OR value looks unrealistic:
        * Return default 45,000

    This keeps the demo realistic and easy to explain.
    """
    filename = (file_storage.filename or "").lower()

    try:
        if filename.endswith(".pdf"):
            file_storage.stream.seek(0)

            reader = PdfReader(file_storage.stream)
            text_chunks = []

            # Read first 2 pages max (enough for most salary slips)
            for page in reader.pages[:2]:
                page_text = page.extract_text() or ""
                text_chunks.append(page_text)

            full_text = "\n".join(text_chunks)
            salary = _extract_salary_from_text(full_text)

            # If we found a salary and it is in a realistic monthly range, use it
            if salary and 20000 <= salary <= 200000:
                return salary

    except Exception:
        # For demo, swallow errors and fall back
        # (We don't want OCR failures to break the hackathon demo)
        pass

    # Fallback if anything goes wrong or value unrealistic
    return 45000
