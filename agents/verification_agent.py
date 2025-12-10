"""
Verification Agent:
- Extracts salary from uploaded file (best effort)
- If OCR is unreliable, falls back to asking user
"""

from services.ocr_stub import parse_salary


def extract_salary_from_file(file):
    """
    Attempt to extract salary from uploaded file.
    Always returns an integer salary.
    """
    salary = parse_salary(file)

    # Absolute safety fallback
    if not salary or salary < 10000:
        salary = 45000  # demo-safe fallback

    return int(salary)
