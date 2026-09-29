"""
Integration and End-to-End API tests for /applications router endpoints.
"""

from fastapi.testclient import TestClient

from app.schemas import ApplicationStatus, ProductType
from app.strategies import ApplicationEvaluator, PhonePolicy, default_evaluator


def test_create_application_phone_approved(client: TestClient):
    payload = {
        "amount": 1_200_000,
        "monthly_income": 2_000_000,
        "employment_months": 24,
        "external_score": 750,
        "product": "PHONE",
    }
    response = client.post("/applications", json=payload)
    assert response.status_code == 201
    data = response.json()
    assert data["id"] is not None
    assert data["status"] == ApplicationStatus.APPROVED.value
    assert data["rejection_reasons"] == []
    assert data["amount"] == 1_200_000
    assert data["product"] == "PHONE"


def test_create_application_phone_rejected(client: TestClient):
    payload = {
        "amount": 1_200_000,
        "monthly_income": 2_000_000,
        "employment_months": 6,  # < 12
        "external_score": 650,  # < 700
        "product": "PHONE",
    }
    response = client.post("/applications", json=payload)
    assert response.status_code == 201
    data = response.json()
    assert data["status"] == ApplicationStatus.REJECTED.value
    assert len(data["rejection_reasons"]) == 2


def test_create_application_twist_approved(client: TestClient):
    payload = {
        "amount": 2_400_000,
        "monthly_income": 3_000_000,
        "employment_months": 8,
        "external_score": 620,
        "product": "TWIST",
    }
    response = client.post("/applications", json=payload)
    assert response.status_code == 201
    data = response.json()
    assert data["status"] == ApplicationStatus.APPROVED.value
    assert data["rejection_reasons"] == []


def test_create_application_twist_rejected(client: TestClient):
    payload = {
        "amount": 6_000_000,  # cuota = 500,000 > 35% of 1,000,000 (350,000)
        "monthly_income": 1_000_000,
        "employment_months": 8,
        "external_score": 580,  # < 600
        "product": "TWIST",
    }
    response = client.post("/applications", json=payload)
    assert response.status_code == 201
    data = response.json()
    assert data["status"] == ApplicationStatus.REJECTED.value
    assert len(data["rejection_reasons"]) == 2


def test_create_application_card_approved_direct(client: TestClient):
    payload = {
        "amount": 5_000_000,
        "monthly_income": 1_500_000,
        "employment_months": 3,
        "external_score": 550,
        "product": "CARD",
    }
    response = client.post("/applications", json=payload)
    assert response.status_code == 201
    data = response.json()
    assert data["status"] == ApplicationStatus.APPROVED.value
    assert data["rejection_reasons"] == []


def test_create_application_card_approved_conditional(client: TestClient):
    payload = {
        "amount": 5_000_000,
        "monthly_income": 3_500_000,
        "employment_months": 3,
        "external_score": 510,
        "product": "CARD",
    }
    response = client.post("/applications", json=payload)
    assert response.status_code == 201
    data = response.json()
    assert data["status"] == ApplicationStatus.APPROVED.value
    assert data["rejection_reasons"] == []


def test_create_application_card_rejected(client: TestClient):
    payload = {
        "amount": 5_000_000,
        "monthly_income": 2_500_000,  # < 3,000,000
        "employment_months": 3,
        "external_score": 510,  # < 550
        "product": "CARD",
    }
    response = client.post("/applications", json=payload)
    assert response.status_code == 201
    data = response.json()
    assert data["status"] == ApplicationStatus.REJECTED.value
    assert len(data["rejection_reasons"]) == 1


def test_validation_errors_score_out_of_range(client: TestClient):
    payload = {
        "amount": 1_000_000,
        "monthly_income": 2_000_000,
        "employment_months": 12,
        "external_score": 1001,  # Invalid: max 1000
        "product": "PHONE",
    }
    response = client.post("/applications", json=payload)
    assert response.status_code == 422


def test_validation_errors_negative_amount(client: TestClient):
    payload = {
        "amount": -500,  # Invalid: must be gt 0
        "monthly_income": 2_000_000,
        "employment_months": 12,
        "external_score": 750,
        "product": "PHONE",
    }
    response = client.post("/applications", json=payload)
    assert response.status_code == 422


def test_validation_errors_invalid_product(client: TestClient):
    payload = {
        "amount": 1_000_000,
        "monthly_income": 2_000_000,
        "employment_months": 12,
        "external_score": 750,
        "product": "INVALID_PRODUCT",
    }
    response = client.post("/applications", json=payload)
    assert response.status_code == 422


def test_get_application_by_id_success(client: TestClient):
    # First create one
    payload = {
        "amount": 1_200_000,
        "monthly_income": 4_000_000,
        "employment_months": 18,
        "external_score": 750,
        "product": "PHONE",
    }
    create_res = client.post("/applications", json=payload)
    created_id = create_res.json()["id"]

    # Now get it
    get_res = client.get(f"/applications/{created_id}")
    assert get_res.status_code == 200
    data = get_res.json()
    assert data["id"] == created_id
    assert data["amount"] == 1_200_000
    assert data["status"] == "APPROVED"


def test_get_application_by_id_not_found(client: TestClient):
    response = client.get("/applications/999999")
    assert response.status_code == 404
    assert "not found" in response.json()["detail"].lower()


def test_list_applications_and_filters(client: TestClient):
    # Create TWIST APPROVED
    client.post(
        "/applications",
        json={
            "amount": 1_200_000,
            "monthly_income": 3_000_000,
            "employment_months": 12,
            "external_score": 650,
            "product": "TWIST",
        },
    )
    # Create TWIST REJECTED
    client.post(
        "/applications",
        json={
            "amount": 1_200_000,
            "monthly_income": 3_000_000,
            "employment_months": 12,
            "external_score": 500,
            "product": "TWIST",
        },
    )
    # Create CARD APPROVED
    client.post(
        "/applications",
        json={
            "amount": 2_000_000,
            "monthly_income": 3_000_000,
            "employment_months": 12,
            "external_score": 600,
            "product": "CARD",
        },
    )

    # 1. Filter status=APPROVED & product=TWIST
    res = client.get("/applications?status=APPROVED&product=TWIST")
    assert res.status_code == 200
    apps = res.json()
    assert len(apps) == 1
    assert apps[0]["product"] == "TWIST"
    assert apps[0]["status"] == "APPROVED"

    # 2. Filter status=REJECTED
    res_rejected = client.get("/applications?status=REJECTED")
    assert res_rejected.status_code == 200
    assert len(res_rejected.json()) == 1

    # 3. Filter product=CARD
    res_card = client.get("/applications?product=CARD")
    assert res_card.status_code == 200
    assert len(res_card.json()) == 1

    # 4. List all
    res_all = client.get("/applications")
    assert res_all.status_code == 200
    assert len(res_all.json()) == 3


def test_list_applications_invalid_query_parameter(client: TestClient):
    res = client.get("/applications?status=NON_EXISTENT_STATUS")
    assert res.status_code == 422


def test_reevaluate_application_success(client: TestClient):
    # Create application that is currently APPROVED under PHONE
    payload = {
        "amount": 1_200_000,
        "monthly_income": 2_000_000,
        "employment_months": 24,
        "external_score": 720,
        "product": "PHONE",
    }
    res = client.post("/applications", json=payload)
    app_id = res.json()["id"]
    assert res.json()["status"] == "APPROVED"

    # Now call reevaluate
    reeval_res = client.post(f"/applications/{app_id}/reevaluate")
    assert reeval_res.status_code == 200
    data = reeval_res.json()
    assert data["id"] == app_id
    assert data["status"] == "APPROVED"


def test_reevaluate_application_policy_change_simulation(client: TestClient):
    """Simulate a threshold change (e.g. MIN_SCORE changed from 700 to 750) and test reevaluate."""
    payload = {
        "amount": 1_200_000,
        "monthly_income": 2_000_000,
        "employment_months": 24,
        "external_score": 720,  # Passes original 700 threshold
        "product": "PHONE",
    }
    create_res = client.post("/applications", json=payload)
    app_id = create_res.json()["id"]
    assert create_res.json()["status"] == "APPROVED"

    # Simulate tighter policy rule in registry
    original_min_score = PhonePolicy.MIN_SCORE
    try:
        PhonePolicy.MIN_SCORE = 750  # Now 720 score is rejected

        reeval_res = client.post(f"/applications/{app_id}/reevaluate")
        assert reeval_res.status_code == 200
        data = reeval_res.json()
        assert data["id"] == app_id
        assert data["status"] == "REJECTED"
        assert any("Score externo (720)" in reason for reason in data["rejection_reasons"])
    finally:
        PhonePolicy.MIN_SCORE = original_min_score  # Reset


def test_reevaluate_application_not_found(client: TestClient):
    response = client.post("/applications/999999/reevaluate")
    assert response.status_code == 404
