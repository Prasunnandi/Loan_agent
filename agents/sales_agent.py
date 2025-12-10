"""
Sales Agent: Handles loan negotiation - amount, tenure, interest.

This agent is responsible for:
- Capturing the initial requested loan amount
- Proposing a default tenure & interest rate
- Calculating EMI using the credit_rules.calculate_emi() function
- Handling user negotiation:
    * Change tenure (e.g. "36 months", "for 5 years")
    * Change amount (entering a new number)
    * Responding to "EMI too high" by increasing tenure
    * Accepting the offer on "ok / yes / proceed" etc. → moves to ASK_SALARY
"""

import re
from services.credit_rules import calculate_emi


def _extract_first_number(text: str):
    if not text:
        return None
    match = re.search(r"\d+", text.replace(",", ""))
    if match:
        return int(match.group())
    return None


def _parse_tenure_from_text(text: str, fallback_months: int) -> int:
    text_lower = text.lower()
    number = _extract_first_number(text_lower)
    if number is None:
        return fallback_months

    if "year" in text_lower:
        return number * 12
    return number


def handle_sales(message: str, session: dict):
    text = (message or "").strip()
    text_lower = text.lower()

    DEFAULT_TENURE = 24
    DEFAULT_INTEREST = 14.0

    # First time: no loan amount yet
    if session.get("loan_amount") is None:
        amount = _extract_first_number(text)
        if amount is None:
            return (
                "Please enter the loan amount you need, for example: 300000.",
                session,
            )

        tenure = DEFAULT_TENURE
        interest = DEFAULT_INTEREST
        emi = calculate_emi(amount, interest, tenure)

        session.update(
            {
                "loan_amount": amount,
                "tenure": tenure,
                "interest": interest,
                "emi": emi,
                "state": "SALES",
            }
        )

        reply = (
            "Here is a draft offer based on your requested amount:\n"
            f"• Loan Amount: ₹{amount:,}\n"
            f"• Tenure: {tenure} months\n"
            f"• Interest Rate: {interest:.1f}% p.a.\n"
            f"• Estimated EMI: ₹{emi:,} per month\n\n"
            "You can also use the quick tenure buttons on the right (12/24/36/48/60 months),\n"
            "or just type a new amount like '250000'.\n\n"
            "If you are happy with this offer, reply ""OK"" and we’ll proceed to your salary details."
        )
        return reply, session

    # We already have an offer
    amount = session.get("loan_amount")
    tenure = session.get("tenure", DEFAULT_TENURE)
    interest = session.get("interest", DEFAULT_INTEREST)
    emi = session.get("emi")

    # Accept offer → move to ASK_SALARY (Master Agent will handle actual question)
    acceptance_keywords = ["ok", "okay", "yes", "proceed", "looks good", "fine"]
    if any(word in text_lower for word in acceptance_keywords):
        session["state"] = "ASK_SALARY"
        reply = (
            "Great, we will proceed with this offer:\n"
            f"• Loan Amount: ₹{amount:,}\n"
            f"• Tenure: {tenure} months\n"
            f"• Interest Rate: {interest:.1f}% p.a.\n"
            f"• Estimated EMI: ₹{emi:,} per month\n\n"
            "Now, please tell me your approximate ""monthly net salary"" in ₹."
        )
        return reply, session

    # Change tenure
    if any(
        kw in text_lower
        for kw in ["tenure", "month", "months", "year", "years", "longer", "shorter"]
    ):
        new_tenure = _parse_tenure_from_text(text_lower, tenure)
        if new_tenure <= 0:
            return (
                "Please specify a valid tenure, like '36 months' or '3 years'.",
                session,
            )

        tenure = new_tenure
        emi = calculate_emi(amount, interest, tenure)
        session["tenure"] = tenure
        session["emi"] = emi

        reply = (
            "Updated offer with your requested tenure:\n"
            f"• Loan Amount: ₹{amount:,}\n"
            f"• Tenure: {tenure} months\n"
            f"• Interest Rate: {interest:.1f}% p.a.\n"
            f"• Estimated EMI: ₹{emi:,} per month\n\n"
            "Reply ""OK"" to proceed to salary details,\n"
            "or adjust tenure/amount again."
        )
        session["state"] = "SALES"
        return reply, session

    # EMI too high → increase tenure
    if any(
        phrase in text_lower
        for phrase in ["too high", "emi too high", "too much", "cant pay", "cannot pay"]
    ) or ("high" in text_lower and "emi" in text_lower):
        MAX_TENURE = 60
        STEP = 12

        if tenure < MAX_TENURE:
            tenure = min(MAX_TENURE, tenure + STEP)
            emi = calculate_emi(amount, interest, tenure)
            session["tenure"] = tenure
            session["emi"] = emi

            reply = (
                "Understood. I've increased the tenure to help reduce the EMI:\n"
                f"• Loan Amount: ₹{amount:,}\n"
                f"• New Tenure: {tenure} months\n"
                f"• Interest Rate: {interest:.1f}% p.a.\n"
                f"• New Estimated EMI: ₹{emi:,} per month\n\n"
                "If this is acceptable, reply ""OK"" to proceed.\n"
                "You can also specify an exact tenure, like '36 months'."
            )
        else:
            reply = (
                f"The tenure is already at the maximum I can offer ({MAX_TENURE} months).\n"
                "To reduce EMI further, you may need to lower the loan amount. "
                "Try typing a smaller amount, e.g. '200000'."
            )

        session["state"] = "SALES"
        return reply, session

    # New amount
    new_amount = _extract_first_number(text)
    if new_amount is not None and new_amount != amount:
        amount = new_amount
        emi = calculate_emi(amount, interest, tenure)
        session["loan_amount"] = amount
        session["emi"] = emi

        reply = (
            "Updated offer with your new requested amount:\n"
            f"• Loan Amount: ₹{amount:,}\n"
            f"• Tenure: {tenure} months\n"
            f"• Interest Rate: {interest:.1f}% p.a.\n"
            f"• Estimated EMI: ₹{emi:,} per month\n\n"
            "Reply ""OK"" to proceed to salary details, "
            "or adjust tenure/amount again."
        )
        session["state"] = "SALES"
        return reply, session

    # Fallback
    reply = (
        "To refine the loan offer, you can:\n"
        "  - Change tenure: 'make it 36 months' or 'for 3 years'\n"
        "  - Change amount: 'try 250000'\n"
        "  - Or reply ""OK"" to proceed to salary details."
    )
    session["state"] = "SALES"
    return reply, session
