"""
PDF Generator: Builds a professional-looking sanction letter using reportlab.

Design goals:
- Clean corporate layout (suitable for bank use)
- No broken glyphs (use "INR" instead of the ₹ symbol)
- Clear sections: Header, Customer info, Loan details, Terms
- Light diagonal watermark to feel like real bank stationery
"""

from datetime import date
from reportlab.lib.pagesizes import A4
from reportlab.pdfgen import canvas
from reportlab.lib import colors


def _draw_watermark(c, width, height):
    """
    Draw a very light diagonal watermark across the page.
    E.g. "FinTech Fusion Bank – Digital Loan Officer"

    Note:
    - ReportLab's setFillColorRGB() does NOT support an 'alpha' argument.
    - For transparency we try setFillAlpha() if available, else fall back
      to an opaque but light color.
    """
    c.saveState()

    # Try to set alpha (transparency) if the ReportLab version supports it
    try:
        c.setFillAlpha(0.18)  # may not exist in older versions
    except Exception:
        # No alpha support; we'll just use a very light color
        pass

    # Very light blue-grey color
    c.setFillColorRGB(0.85, 0.9, 0.95)

    c.setFont("Helvetica-Bold", 50)

    # Rotate around center and draw text
    c.translate(width / 2.0, height / 2.0)
    c.rotate(35)
    c.drawCentredString(0, 0, "FinTech Fusion Bank")
    c.setFont("Helvetica", 26)
    c.drawCentredString(0, -40, "Digital Loan Officer")

    # Restore alpha/color/state
    c.restoreState()


def build_pdf(session: dict, buffer) -> None:
    """
    Build a sanction letter PDF into the given buffer (BytesIO).

    Expected keys in session:
        - name
        - loan_amount
        - tenure
        - interest
        - emi
        - credit_score
        - loan_id (optional)
    """
    c = canvas.Canvas(buffer, pagesize=A4)
    width, height = A4

    # --- Global watermark on page 1 ---
    _draw_watermark(c, width, height)

    x_margin = 60
    y = height - 60

    # 1) Header bar
    c.setFillColor(colors.HexColor("#0f172a"))  # dark navy
    c.rect(0, height - 80, width, 80, fill=1, stroke=0)

    c.setFillColor(colors.white)
    c.setFont("Helvetica-Bold", 18)
    c.drawString(x_margin, height - 45, "FinTech Fusion Bank")

    c.setFont("Helvetica", 10)
    c.drawString(x_margin, height - 63, "Digital Loan Officer · Sanction Letter")

    # 2) Back to normal page area
    c.setFillColor(colors.black)
    y -= 80

    # Date & reference
    c.setFont("Helvetica", 10)
    today_str = date.today().strftime("%d-%m-%Y")
    c.drawString(x_margin, y, f"Date: {today_str}")
    y -= 16

    loan_id = session.get("loan_id", "LOAN-DEMO-001")
    c.drawString(x_margin, y, f"Reference ID: {loan_id}")
    y -= 30

    # Fetch data safely
    name = (session.get("name") or "Applicant").upper()
    loan_amount = int(session.get("loan_amount") or 0)
    tenure = int(session.get("tenure") or 0)
    interest = float(session.get("interest") or 0.0)
    emi = int(session.get("emi") or 0)
    credit_score = session.get("credit_score", "N/A")

    # Addressing
    c.setFont("Helvetica", 11)
    c.drawString(x_margin, y, "To,")
    y -= 16
    c.setFont("Helvetica-Bold", 11)
    c.drawString(x_margin, y, name)
    y -= 24

    # Subject
    c.setFont("Helvetica-Bold", 11)
    c.drawString(x_margin, y, "Subject: Sanction of Personal Loan")
    y -= 24

    # Body intro
    c.setFont("Helvetica", 11)
    lines_intro = [
        f"Dear {name},",
        "",
        "We are pleased to inform you that your personal loan application has been",
        "assessed and the following offer has been sanctioned:",
        "",
    ]
    for line in lines_intro:
        c.drawString(x_margin, y, line)
        y -= 16

    # 3) Loan Details "card" section
    y -= 4
    box_top = y
    box_height = 110
    c.setFillColor(colors.whitesmoke)
    c.roundRect(
        x_margin,
        box_top - box_height,
        width - 2 * x_margin,
        box_height,
        radius=8,
        fill=1,
        stroke=0,
    )

    c.setFillColor(colors.black)
    c.setFont("Helvetica-Bold", 11)
    y = box_top - 18
    c.drawString(x_margin + 10, y, "Sanctioned Loan Details")
    y -= 12

    c.setStrokeColor(colors.lightgrey)
    c.setLineWidth(0.4)
    c.line(x_margin + 10, y, width - x_margin - 10, y)
    y -= 16

    c.setFont("Helvetica", 10)
    c.drawString(x_margin + 14, y, f"Sanctioned Amount : INR {loan_amount:,.0f}")
    y -= 15
    c.drawString(x_margin + 14, y, f"Tenure            : {tenure} months")
    y -= 15
    c.drawString(x_margin + 14, y, f"Interest Rate     : {interest:.1f}% p.a.")
    y -= 15
    c.drawString(x_margin + 14, y, f"Monthly EMI       : INR {emi:,.0f}")
    y -= 15
    c.drawString(x_margin + 14, y, f"Derived Credit Score : {credit_score}")
    y -= 30

    # 4) Terms & conditions section
    c.setFont("Helvetica", 11)
    body_paragraph = [
        "This sanction is subject to successful completion of all KYC and document",
        "verification as per our internal credit policies and regulatory guidelines.",
        "The bank reserves the right to withdraw or modify this offer in case of any",
        "discrepancy in the information or documents provided.",
        "",
        "Please review the above details carefully. In case of any queries or clarifications,",
        "you may contact our customer service team with the reference ID mentioned above.",
        "",
        "Thank you for choosing FinTech Fusion Bank.",
        "",
        "Sincerely,",
        "",
        "Digital Loan Officer",
        "FinTech Fusion Bank",
    ]

    for line in body_paragraph:
        c.drawString(x_margin, y, line)
        y -= 16
        if y < 80:
            c.showPage()
            y = height - 80
            # watermark on new pages as well
            _draw_watermark(c, width, height)
            c.setFont("Helvetica", 11)

    c.showPage()
    c.save()
