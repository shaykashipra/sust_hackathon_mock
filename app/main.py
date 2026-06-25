from enum import Enum
import re
from typing import Optional

from fastapi import FastAPI
from pydantic import BaseModel, Field


class CaseType(str, Enum):
    WRONG_TRANSFER = "wrong_transfer"
    PAYMENT_FAILED = "payment_failed"
    REFUND_REQUEST = "refund_request"
    PHISHING_OR_SOCIAL_ENGINEERING = "phishing_or_social_engineering"
    OTHER = "other"


class Severity(str, Enum):
    CRITICAL = "critical"
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"


class Department(str, Enum):
    FRAUD_RISK = "fraud_risk"
    PAYMENTS_OPS = "payments_ops"
    DISPUTE_RESOLUTION = "dispute_resolution"
    CUSTOMER_SUPPORT = "customer_support"


class Channel(str, Enum):
    APP = "app"
    SMS = "sms"
    CALL_CENTER = "call_center"
    MERCHANT_PORTAL = "merchant_portal"


class Locale(str, Enum):
    BN = "bn"
    EN = "en"
    MIXED = "mixed"


class TicketRequest(BaseModel):
    ticket_id: str = Field(..., min_length=1)
    channel: Optional[Channel] = None
    locale: Optional[Locale] = None
    message: str = Field(..., min_length=1)


class TicketResponse(BaseModel):
    ticket_id: str
    case_type: CaseType
    severity: Severity
    department: Department
    agent_summary: str
    human_review_required: bool
    confidence: float = Field(..., ge=0.0, le=1.0)


app = FastAPI(
    title="Customer Support Triage API",
    version="1.0.0",
    description="Rules-based triage service for digital financial service complaints.",
)


PHISHING_TERMS = (
    "otp",
    "pin",
    "password",
    "passcode",
    "verification code",
    "secret code",
    "cvv",
    "card number",
    "scam",
    "fraud",
    "phishing",
    "fake",
    "someone called",
    "unknown number",
)

WRONG_TRANSFER_TERMS = (
    "wrong number",
    "wrong recipient",
    "wrong account",
    "wrong person",
    "sent by mistake",
    "mistakenly sent",
    "mistake transfer",
    "wrong transfer",
    "ভুল নম্বর",
    "ভুল করে",
)

PAYMENT_FAILED_TERMS = (
    "payment failed",
    "transaction failed",
    "failed but",
    "balance deducted",
    "money deducted",
    "amount deducted",
    "charged",
    "debited",
    "paid but not",
    "merchant did not receive",
    "পেমেন্ট ফেইল",
    "টাকা কেটে",
)

REFUND_TERMS = (
    "refund",
    "return my money",
    "money back",
    "reverse",
    "reversal",
    "cancel transaction",
    "changed my mind",
    "রিফান্ড",
    "টাকা ফেরত",
)

MEDIUM_SERVICE_TERMS = (
    "pending",
    "stuck",
    "not working",
    "cannot login",
    "can't login",
    "account locked",
    "service unavailable",
)


def contains_any(text: str, terms: tuple[str, ...]) -> bool:
    return any(term in text for term in terms)


def classify_case(message: str) -> tuple[CaseType, float]:
    text = message.casefold()

    if contains_any(text, PHISHING_TERMS):
        return CaseType.PHISHING_OR_SOCIAL_ENGINEERING, 0.95
    if contains_any(text, WRONG_TRANSFER_TERMS):
        return CaseType.WRONG_TRANSFER, 0.9
    if contains_any(text, PAYMENT_FAILED_TERMS):
        return CaseType.PAYMENT_FAILED, 0.88
    if contains_any(text, REFUND_TERMS):
        return CaseType.REFUND_REQUEST, 0.82

    return CaseType.OTHER, 0.68


def determine_severity(case_type: CaseType, message: str) -> Severity:
    text = message.casefold()

    if case_type == CaseType.PHISHING_OR_SOCIAL_ENGINEERING:
        return Severity.CRITICAL
    if case_type in {CaseType.WRONG_TRANSFER, CaseType.PAYMENT_FAILED}:
        return Severity.HIGH
    if case_type == CaseType.REFUND_REQUEST:
        if any(term in text for term in ("unauthorized", "not mine", "dispute", "fraud", "scam")):
            return Severity.HIGH
        return Severity.LOW
    if contains_any(text, MEDIUM_SERVICE_TERMS):
        return Severity.MEDIUM

    return Severity.LOW


def determine_department(case_type: CaseType, severity: Severity) -> Department:
    if case_type == CaseType.PHISHING_OR_SOCIAL_ENGINEERING:
        return Department.FRAUD_RISK
    if case_type == CaseType.PAYMENT_FAILED:
        return Department.PAYMENTS_OPS
    if case_type == CaseType.WRONG_TRANSFER:
        return Department.DISPUTE_RESOLUTION
    if case_type == CaseType.REFUND_REQUEST and severity == Severity.HIGH:
        return Department.DISPUTE_RESOLUTION
    return Department.CUSTOMER_SUPPORT


def clean_message(message: str) -> str:
    cleaned = re.sub(r"\s+", " ", message).strip()
    return re.sub(
        r"\b(?:otp|pin|password|passcode|cvv|card number)\b",
        "credential",
        cleaned,
        flags=re.IGNORECASE,
    )


def build_summary(case_type: CaseType, message: str) -> str:
    safe_message = clean_message(message)

    templates = {
        CaseType.WRONG_TRANSFER: "Customer reports a wrong recipient transfer and requests assistance.",
        CaseType.PAYMENT_FAILED: "Customer reports a failed payment with possible balance deduction.",
        CaseType.REFUND_REQUEST: "Customer requests a refund for a recent transaction.",
        CaseType.PHISHING_OR_SOCIAL_ENGINEERING: "Customer reports suspicious contact involving credential-related fraud risk.",
        CaseType.OTHER: "Customer reports a service issue requiring support review.",
    }

    if len(safe_message.split()) <= 18 and case_type != CaseType.PHISHING_OR_SOCIAL_ENGINEERING:
        summary = f"Customer reports: {safe_message}"
    else:
        summary = templates[case_type]

    words = summary.split()
    return " ".join(words[:25])


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok"}


@app.post("/sort-ticket", response_model=TicketResponse)
def sort_ticket(ticket: TicketRequest) -> TicketResponse:
    case_type, confidence = classify_case(ticket.message)
    severity = determine_severity(case_type, ticket.message)
    department = determine_department(case_type, severity)
    human_review_required = (
        severity == Severity.CRITICAL
        or case_type == CaseType.PHISHING_OR_SOCIAL_ENGINEERING
    )

    return TicketResponse(
        ticket_id=ticket.ticket_id,
        case_type=case_type,
        severity=severity,
        department=department,
        agent_summary=build_summary(case_type, ticket.message),
        human_review_required=human_review_required,
        confidence=confidence,
    )
