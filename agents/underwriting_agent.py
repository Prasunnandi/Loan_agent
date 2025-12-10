"""
Underwriting Agent: Applies credit rules to determine eligibility.
"""

"""
Underwriting Agent: Applies credit rules to determine eligibility.

This agent is called by the Master Agent once:
- Sales Agent has captured loan amount, tenure, and interest
- Verification Agent has extracted (or mocked) the salary from the
  uploaded salary slip.

It delegates the actual decision logic to services.credit_rules.check_eligibility,
then turns that into a human-friendly explanation for the user.
"""

from services.credit_rules import check_eligibility, calculate_emi


def evaluate_eligibility(session):
    if session.get("state") in ("APPROVED", "REJECTED"):
        return "Decision already made.", session
    """
    Evaluate eligibility for the current session.

    Uses the credit_rules.check_eligibility(session) function, which returns:
        status ∈ {"approved", "rejected"}
        info   : dict with reason, credit_score, dti, suggested_amount, etc.

    This function:
    - Updates session['state'] to APPROVED / REJECTED
    - Returns a conversational reply explaining the decision.
    """
    status, info = check_eligibility(session)

    credit_score = info.get("credit_score")
    dti = info.get("dti")
    suggested_amount = info.get("suggested_amount")
    reason = info.get("reason", "")

    loan_amount = session.get("loan_amount")
    tenure = session.get("tenure")
    interest = session.get("interest")
    emi = session.get("emi")

    if status == "approved":
        # Set state for the rest of the flow
        session["state"] = "APPROVED"

        reply_lines = [
            "🎉 *Good news!* Your profile is **eligible** for this loan.",
            "",
            f"• Loan Amount: ₹{int(loan_amount):,}",
            f"• Tenure: {tenure} months",
            f"• Interest Rate: {interest:.1f}% p.a.",
            f"• Estimated EMI: ₹{int(emi):,} per month",
        ]
        if credit_score:
            reply_lines.append(f"• Derived Credit Score: {credit_score}")
        if dti is not None:
            reply_lines.append(f"• EMI-to-Income Ratio: {dti*100:.1f}%")

        reply_lines.append("")
        reply_lines.append(reason)  # e.g. explanation of why approved
        reply_lines.append(
            "\nI'm generating your sanction letter now. "
            "Click on **Download Sanction Letter** to view it."
        )

        reply = "\n".join(reply_lines)
        return reply, session

    # ----- Rejected path -----
    session["state"] = "REJECTED"

    reply_lines = [
        "❌ *Unfortunately, your current profile doesn’t meet our policy criteria.*",
        "",
        f"Reason: {reason}",
    ]

    # If we have a suggested lower amount, present it nicely
    if suggested_amount and loan_amount:
        if suggested_amount < loan_amount:
            reply_lines.append(
                f"\n💡 Based on your income, you could be eligible for a "
                f"lower amount of around **₹{int(suggested_amount):,}** "
                f"for the same tenure ({tenure} months)."
            )
            reply_lines.append(
                "You can try again with a lower loan amount or a longer tenure."
            )
        else:
            # suggested >= requested, just generic message
            reply_lines.append(
                "\nYou may try reducing the EMI by either lowering the amount "
                "or increasing the tenure."
            )
    else:
        reply_lines.append(
            "\nYou may try reducing the loan amount or increasing the tenure, "
            "or speak to a human loan officer for alternatives."
        )

    reply = "\n".join(reply_lines)
    return reply, session
