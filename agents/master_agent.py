"""
Master Agent: Central orchestrator for the conversation.

New flow:
INIT → ASK_NAME → ASK_PHONE → ASK_LOAN_AMOUNT → SALES (EMI negotiation)
→ ASK_SALARY → ASK_PAN → WAIT_UPLOAD → UNDERWRITE → APPROVED/REJECTED

User can type "menu" / "main menu" / "restart" anytime to reset.
"""

from agents.sales_agent import handle_sales
from agents.verification_agent import extract_salary_from_file
from agents.underwriting_agent import evaluate_eligibility
from agents.sanction_agent import create_pdf


def handle_message(message, session):
    text = (message or "").strip()
    text_lower = text.lower()

    # 🔁 Global "return to menu" command
    if any(kw in text_lower for kw in ["menu", "main menu", "restart", "start over"]):
        # Hard reset, and jump directly to ASK_NAME (not INIT)
        session.clear()
        session["state"] = "ASK_NAME"
        return (
            "You have returned to the main menu.\n"
            "👋 Hi again, I'm your Digital Loan Officer.\n"
            "Let's start fresh.\n\n"
            "What is your full name?",
            session,
        )

    state = session.get("state", "INIT")

    # 1️⃣ Start
    if state == "INIT":
        session["state"] = "ASK_NAME"
        return (
            "👋 Hi, I'm your Digital Loan Officer.\n"
            "To begin, may I know your full name?",
            session,
        )

    # 2️⃣ Name
    if state == "ASK_NAME":
        if not text:
            return "Please share your full name to proceed.", session

        session["name"] = text
        session["state"] = "ASK_PHONE"
        return (
            f"Thanks, {session['name']}.\n"
            "Please share your 10-digit mobile number.",
            session,
        )

    # 3️⃣ Phone
    if state == "ASK_PHONE":
        digits_only = "".join(ch for ch in text if ch.isdigit())
        if len(digits_only) < 10:
            return (
                "Please enter a valid 10-digit mobile number (digits only).",
                session,
            )

        session["phone"] = digits_only
        session["state"] = "ASK_LOAN_AMOUNT"
        return (
            "Noted.\n"
            "How much personal loan do you need? (e.g. 300000)",
            session,
        )

    # 4️⃣ Loan amount → delegate to Sales Agent for EMI & negotiation
    if state == "ASK_LOAN_AMOUNT" or state == "SALES":
        # Sales agent handles:
        # - first amount
        # - tenure changes
        # - EMI recalculation
        # - on 'OK' it will set state = 'ASK_SALARY'
        return handle_sales(text, session)

    # 5️⃣ Ask salary BEFORE salary slip
    if state == "ASK_SALARY":
        # Expect a numeric salary input
        try:
            salary = int("".join(ch for ch in text if ch.isdigit()))
        except ValueError:
            salary = None

        if not salary or salary <= 0:
            return (
                "Please enter your approximate monthly net salary in ₹, "
                "for example: 45000.",
                session,
            )

        session["salary"] = salary
        session["state"] = "ASK_PAN"
        return (
            f"Thanks. I have noted your monthly income as ₹{salary:,}.\n"
            "Now, please enter your PAN (dummy is fine for this demo).",
            session,
        )

    # 6️⃣ Ask PAN
    if state == "ASK_PAN":
        pan = text.replace(" ", "")
        session["pan"] = pan
        session["state"] = "WAIT_UPLOAD"
        return (
            "PAN captured.\n"
            "Now please upload your latest salary slip (PDF or image) "
            "using the upload button on the right.\n\n"
            "You can type 'menu' anytime to restart.",
            session,
        )

    # 7️⃣ Waiting for salary slip upload
    if state == "WAIT_UPLOAD":
        return (
            "Please upload your salary slip using the 'Upload & Run Eligibility' "
            "button on the right panel.",
            session,
        )

    # 8️⃣ Underwriting (only used if manually triggered)
    if state == "UNDERWRITE":
        required = ["loan_amount", "tenure", "emi", "salary"]
        if not all(k in session for k in required):
            return (
                "Some required details are missing. "
                "Please complete the loan details and salary first.",
                session,
            )
        return evaluate_eligibility(session)

    # 9️⃣ Approved
    if state == "APPROVED":
        return (
            "✅ Your loan is approved.\n"
            "You can now download your sanction letter using the button on the right.",
            session,
        )

    # 🔟 Rejected
    if state == "REJECTED":
        return (
            "❌ Your profile was not approved for the requested loan.\n"
            "You may try a lower loan amount or a longer tenure, or type 'menu' to restart.",
            session,
        )

    return "Let’s continue your loan journey. You can type 'menu' to restart anytime.", session


def process_salary_slip(file, session):
    """
    Called from /upload endpoint.
    - Extract salary (OCR stub)
    - Overwrite or complement existing salary
    - Immediately run underwriting & return combined reply
    """
    # Save previously declared salary (if any) for explanation
    previously_declared = session.get("salary")

    detected_salary = extract_salary_from_file(file)
    # Use OCR-detected salary as primary for underwriting
    session["salary"] = detected_salary

    reply, session = evaluate_eligibility(session)

    lines = [
        "📄 Salary slip received.",
        f"Verified monthly income from salary slip: ₹{detected_salary:,}.",
    ]

    if previously_declared and previously_declared != detected_salary:
        lines.append(
            f"(Previously declared in chat: ₹{previously_declared:,}.)"
        )

    lines.append("")  # blank line before underwriting result
    combined_reply = "\n".join(lines) + reply

    return combined_reply, session


def generate_sanction_letter(session):
    return create_pdf(session)
