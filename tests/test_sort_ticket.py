from fastapi.testclient import TestClient

from app.main import app


client = TestClient(app)


def sort_message(message: str) -> dict:
    response = client.post(
        "/sort-ticket",
        json={"ticket_id": "T-001", "message": message},
    )
    assert response.status_code == 200
    return response.json()


def test_health() -> None:
    response = client.get("/health")

    assert response.status_code == 200
    assert response.json() == {"status": "ok"}


def test_wrong_transfer() -> None:
    data = sort_message("I sent 3000 to wrong number")

    assert data["case_type"] == "wrong_transfer"
    assert data["severity"] == "high"
    assert data["department"] == "dispute_resolution"
    assert data["human_review_required"] is False


def test_payment_failed() -> None:
    data = sort_message("Payment failed but balance deducted")

    assert data["case_type"] == "payment_failed"
    assert data["severity"] == "high"
    assert data["department"] == "payments_ops"


def test_phishing_requires_review() -> None:
    data = sort_message("Someone called asking my OTP, is that bKash?")

    assert data["case_type"] == "phishing_or_social_engineering"
    assert data["severity"] == "critical"
    assert data["department"] == "fraud_risk"
    assert data["human_review_required"] is True
    assert "OTP" not in data["agent_summary"]


def test_refund_low() -> None:
    data = sort_message("Please refund my last transaction, I changed my mind")

    assert data["case_type"] == "refund_request"
    assert data["severity"] == "low"
    assert data["department"] == "customer_support"


def test_other_low() -> None:
    data = sort_message("App crashed when I opened it")

    assert data["case_type"] == "other"
    assert data["severity"] == "low"
    assert data["department"] == "customer_support"
