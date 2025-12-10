"""
Credit Rules Service: Calculates EMI and evaluates loan eligibility.

This module centralizes all credit logic used by the Underwriting Agent:

- EMI calculation using the standard reducing balance formula.
- Fake credit score generation based on salary (for demo only).
- Eligibility checks using:
    * Minimum income threshold
    * Minimum credit score threshold
    * Debt-to-Income (DTI) ratio limit
    * Maximum loan amount as a multiple of annual income
- Suggesting a lower loan amount the customer could realistically afford.

All numbers / thresholds are tunable and documented so they can be
explained easily to a panel (EY Techathon jury).
"""

from math import pow
from typing import Dict, Tuple


# ---------- Core Financial Utilities ---------- #

def calculate_emi(principal: float, annual_rate: float, months: int) -> int:
    """
    Calculate EMI using the standard amortization formula:

        EMI = P * r * (1 + r)^N / [(1 + r)^N - 1]

    where:
        P = principal (loan amount)
        r = monthly interest rate (annual_rate / 12 / 100)
        N = number of monthly installments

    Returns the EMI rounded to the nearest rupee.
    """
    if months <= 0:
        raise ValueError("Tenure (months) must be positive")

    monthly_rate = annual_rate / 12.0 / 100.0

    # Edge-case: Zero interest
    if monthly_rate == 0:
        return round(principal / months)

    factor = pow(1 + monthly_rate, months)
    emi = principal * monthly_rate * factor / (factor - 1)
    return int(round(emi))


def fake_credit_score_from_salary(salary: float) -> int:
    """
    Demo-friendly credit score generator.

    Heuristic:
        base  = 620
        bump  = (salary / 1000) * 2
        score = min(800, base + bump)

    So higher salary => better score, capped at 800.

    Examples:
        - salary = 30,000 -> score ≈ 680
        - salary = 45,000 -> score ≈ 710
        - salary = 60,000 -> score ≈ 740
    """
    if salary <= 0:
        return 0
    base = 620
    bump = (salary / 1000.0) * 2.0
    score = int(base + bump)
    return min(800, score)


def max_affordable_loan(
    monthly_salary: float,
    annual_rate: float,
    months: int,
    max_emi_ratio: float = 0.45,
) -> int:
    """
    Given a monthly salary and a target EMI-to-income ratio, compute
    the maximum principal the user can afford for a given tenure.

    Steps:
    - Allowed EMI = monthly_salary * max_emi_ratio
    - Invert the EMI formula to solve for P (principal).

    This is used to suggest a lower eligible loan amount when the
    requested loan is not approved.
    """
    if monthly_salary <= 0 or months <= 0:
        return 0

    allowed_emi = monthly_salary * max_emi_ratio
    monthly_rate = annual_rate / 12.0 / 100.0

    if monthly_rate == 0:
        # Simple: P = EMI * N
        return int(allowed_emi * months)

    factor = pow(1 + monthly_rate, months)
    # From EMI formula rearranged for principal:
    # EMI = P * r * (1+r)^N / ((1+r)^N - 1)
    # => P  = EMI * ((1+r)^N - 1) / (r * (1+r)^N)
    principal = allowed_emi * (factor - 1) / (monthly_rate * factor)
    return int(principal)


# ---------- Eligibility Engine ---------- #

def check_eligibility(session: Dict) -> Tuple[str, Dict]:
    """
    Main underwriting function.

    Input:  session dict with at least:
        - 'salary'       : monthly salary (int/float)
        - 'emi'          : calculated EMI for requested loan
        - 'loan_amount'  : requested principal
        - 'tenure'       : tenure in months
        - 'interest'     : annual interest rate (percent)

    Output:
        (status, info_dict)

        status ∈ {"approved", "rejected"}

        info_dict contains:
            - 'reason'            : human-readable explanation
            - 'credit_score'      : derived demo credit score
            - 'dti'               : Debt-to-Income ratio (emi / salary)
            - 'max_allowed_loan'  : max loan allowed by income multiple rule
            - 'suggested_amount'  : suggested lower amount (if rejected)
    """
    salary = session.get("salary")
    emi = session.get("emi")
    amount = session.get("loan_amount")
    tenure = session.get("tenure")
    interest = session.get("interest", 14.0)

    # Basic presence check
    if salary is None or emi is None or amount is None or tenure is None:
        info = {
            "reason": "Missing required data (salary / EMI / amount / tenure).",
            "credit_score": 0,
            "dti": None,
            "max_allowed_loan": None,
            "suggested_amount": None,
        }
        return "rejected", info

    salary = float(salary)
    emi = float(emi)
    amount = float(amount)
    tenure = int(tenure)

    # ---- Tunable thresholds (EY demo tuned) ---- #
    MIN_INCOME = 25000          # Minimum monthly salary
    MIN_CREDIT_SCORE = 680      # Minimum acceptable credit score
    MAX_DTI = 0.45              # Max allowable EMI-to-income ratio (45%)
    MAX_LOAN_MULTIPLE = 4       # Loan <= 4x annual income

    # ---- Derived values ---- #
    if salary <= 0:
        dti = None
    else:
        dti = emi / salary

    annual_income = salary * 12
    max_allowed_loan_income_rule = MAX_LOAN_MULTIPLE * annual_income

    credit_score = fake_credit_score_from_salary(salary)
    session["credit_score"] = credit_score  # store back for later use

    # Pre-compute a suggested amount (subject to rules)
    suggested_by_dti = max_affordable_loan(
        monthly_salary=salary,
        annual_rate=interest,
        months=tenure,
        max_emi_ratio=MAX_DTI,
    )
    suggested_amount = int(
        min(suggested_by_dti, max_allowed_loan_income_rule)
    ) if suggested_by_dti > 0 else None

    # ---- Sequential rules with clear reasons ---- #
    # 1) Minimum income
    if salary < MIN_INCOME:
        info = {
            "reason": (
                f"Monthly income ₹{int(salary):,} is below the minimum "
                f"required ₹{MIN_INCOME:,}."
            ),
            "credit_score": credit_score,
            "dti": dti,
            "max_allowed_loan": int(max_allowed_loan_income_rule),
            "suggested_amount": None,
        }
        return "rejected", info

    # 2) Minimum credit score
    if credit_score < MIN_CREDIT_SCORE:
        info = {
            "reason": (
                f"Derived credit score {credit_score} is below the "
                f"required minimum of {MIN_CREDIT_SCORE}."
            ),
            "credit_score": credit_score,
            "dti": dti,
            "max_allowed_loan": int(max_allowed_loan_income_rule),
            "suggested_amount": suggested_amount,
        }
        return "rejected", info

    # 3) DTI threshold
    if dti is not None and dti > MAX_DTI:
        info = {
            "reason": (
                f"EMI-to-income ratio is {dti*100:.1f}% which exceeds "
                f"our limit of {MAX_DTI*100:.0f}%."
            ),
            "credit_score": credit_score,
            "dti": dti,
            "max_allowed_loan": int(max_allowed_loan_income_rule),
            "suggested_amount": suggested_amount,
        }
        return "rejected", info

    # 4) Maximum loan multiple of income
    if amount > max_allowed_loan_income_rule:
        info = {
            "reason": (
                f"Requested amount ₹{int(amount):,} is higher than the "
                f"maximum allowed (~₹{int(max_allowed_loan_income_rule):,}) "
                f"based on your income."
            ),
            "credit_score": credit_score,
            "dti": dti,
            "max_allowed_loan": int(max_allowed_loan_income_rule),
            "suggested_amount": suggested_amount,
        }
        return "rejected", info

    # ---- If all rules passed → approved ---- #
    info = {
        "reason": (
            "Profile approved based on income, EMI-to-income ratio "
            f"{dti*100:.1f}% and credit score {credit_score}."
        ),
        "credit_score": credit_score,
        "dti": dti,
        "max_allowed_loan": int(max_allowed_loan_income_rule),
        "suggested_amount": None,
    }
    return "approved", info
