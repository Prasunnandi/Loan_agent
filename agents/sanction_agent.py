
"""
Sanction Agent: Generates PDF sanction letter for approved loans.
"""
from services.pdf_generator import build_pdf
import io

def create_pdf(session):
    buffer = io.BytesIO()
    build_pdf(session, buffer)
    buffer.seek(0)
    return buffer.read()
