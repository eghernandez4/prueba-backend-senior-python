"""
Unit tests for evaluation policies and evaluator concern.
"""

from dataclasses import dataclass
import pytest

from app.schemas import ApplicationStatus, ProductType
from app.strategies import (
    ApplicationEvaluator,
    CardPolicy,
    PhonePolicy,
    PolicyRegistry,
    TwistPolicy,
    UnsupportedProductError,
)


@dataclass
class DummyApplicationInput:
    """Mock application input for testing policies."""

    amount: int
    monthly_income: int
    employment_months: int
    external_score: int
    product: ProductType | str


class TestPhonePolicy:
    """Tests for PHONE conservative policy."""

    def setup_method(self):
        self.policy = PhonePolicy()

    def test_phone_approved(self):
        """Meets score >= 700, employment >= 12, installment <= 25% income."""
        app_input = DummyApplicationInput(
            amount=1_200_000,  # installment = 100,000
            monthly_income=1_000_000,  # 25% = 250,000
            employment_months=12,
            external_score=700,
            product=ProductType.PHONE,
        )
        result = self.policy.evaluate(app_input)
        assert result.status == ApplicationStatus.APPROVED
        assert result.rejection_reasons == []

    def test_phone_rejected_score_below_700(self):
        app_input = DummyApplicationInput(
            amount=1_200_000,
            monthly_income=1_000_000,
            employment_months=12,
            external_score=699,
            product=ProductType.PHONE,
        )
        result = self.policy.evaluate(app_input)
        assert result.status == ApplicationStatus.REJECTED
        assert len(result.rejection_reasons) == 1
        assert "Score externo (699)" in result.rejection_reasons[0]

    def test_phone_rejected_employment_below_12(self):
        app_input = DummyApplicationInput(
            amount=1_200_000,
            monthly_income=1_000_000,
            employment_months=11,
            external_score=750,
            product=ProductType.PHONE,
        )
        result = self.policy.evaluate(app_input)
        assert result.status == ApplicationStatus.REJECTED
        assert len(result.rejection_reasons) == 1
        assert "Antigüedad laboral (11 meses)" in result.rejection_reasons[0]

    def test_phone_rejected_installment_exceeds_25_percent(self):
        app_input = DummyApplicationInput(
            amount=3_600_000,  # installment = 300,000
            monthly_income=1_000_000,  # 25% = 250,000
            employment_months=24,
            external_score=800,
            product=ProductType.PHONE,
        )
        result = self.policy.evaluate(app_input)
        assert result.status == ApplicationStatus.REJECTED
        assert len(result.rejection_reasons) == 1
        assert "supera el 25%" in result.rejection_reasons[0]

    def test_phone_rejected_multiple_reasons(self):
        app_input = DummyApplicationInput(
            amount=3_600_000,  # installment = 300,000 > 250,000
            monthly_income=1_000_000,
            employment_months=6,  # < 12
            external_score=500,  # < 700
            product=ProductType.PHONE,
        )
        result = self.policy.evaluate(app_input)
        assert result.status == ApplicationStatus.REJECTED
        assert len(result.rejection_reasons) == 3


class TestTwistPolicy:
    """Tests for TWIST standard policy."""

    def setup_method(self):
        self.policy = TwistPolicy()

    def test_twist_approved(self):
        """Meets score >= 600, installment <= 35% income."""
        app_input = DummyApplicationInput(
            amount=2_400_000,  # installment = 200,000
            monthly_income=1_000_000,  # 35% = 350,000
            employment_months=6,
            external_score=600,
            product=ProductType.TWIST,
        )
        result = self.policy.evaluate(app_input)
        assert result.status == ApplicationStatus.APPROVED
        assert result.rejection_reasons == []

    def test_twist_rejected_score_below_600(self):
        app_input = DummyApplicationInput(
            amount=2_400_000,
            monthly_income=1_000_000,
            employment_months=6,
            external_score=599,
            product=ProductType.TWIST,
        )
        result = self.policy.evaluate(app_input)
        assert result.status == ApplicationStatus.REJECTED
        assert len(result.rejection_reasons) == 1
        assert "Score externo (599)" in result.rejection_reasons[0]

    def test_twist_rejected_installment_exceeds_35_percent(self):
        app_input = DummyApplicationInput(
            amount=4_800_000,  # installment = 400,000 > 350,000
            monthly_income=1_000_000,
            employment_months=6,
            external_score=650,
            product=ProductType.TWIST,
        )
        result = self.policy.evaluate(app_input)
        assert result.status == ApplicationStatus.REJECTED
        assert len(result.rejection_reasons) == 1
        assert "supera el 35%" in result.rejection_reasons[0]

    def test_twist_rejected_both_reasons(self):
        app_input = DummyApplicationInput(
            amount=4_800_000,
            monthly_income=1_000_000,
            employment_months=1,
            external_score=450,
            product=ProductType.TWIST,
        )
        result = self.policy.evaluate(app_input)
        assert result.status == ApplicationStatus.REJECTED
        assert len(result.rejection_reasons) == 2


class TestCardPolicy:
    """Tests for CARD aggressive policy."""

    def setup_method(self):
        self.policy = CardPolicy()

    def test_card_approved_score_at_least_550(self):
        app_input = DummyApplicationInput(
            amount=5_000_000,
            monthly_income=1_500_000,  # Below 3M, but score >= 550
            employment_months=1,
            external_score=550,
            product=ProductType.CARD,
        )
        result = self.policy.evaluate(app_input)
        assert result.status == ApplicationStatus.APPROVED
        assert result.rejection_reasons == []

    def test_card_approved_conditional_score_and_high_income(self):
        app_input = DummyApplicationInput(
            amount=5_000_000,
            monthly_income=3_000_000,  # Score between 500 and 549, income >= 3M
            employment_months=1,
            external_score=500,
            product=ProductType.CARD,
        )
        result = self.policy.evaluate(app_input)
        assert result.status == ApplicationStatus.APPROVED
        assert result.rejection_reasons == []

    def test_card_rejected_score_below_500(self):
        app_input = DummyApplicationInput(
            amount=5_000_000,
            monthly_income=10_000_000,  # Even with high income, score < 500 rejects
            employment_months=12,
            external_score=499,
            product=ProductType.CARD,
        )
        result = self.policy.evaluate(app_input)
        assert result.status == ApplicationStatus.REJECTED
        assert len(result.rejection_reasons) == 1
        assert "menor al mínimo permitido (500)" in result.rejection_reasons[0]

    def test_card_rejected_score_500_to_549_with_insufficient_income(self):
        app_input = DummyApplicationInput(
            amount=5_000_000,
            monthly_income=2_999_999,  # Just below 3,000,000 COP
            employment_months=12,
            external_score=520,
            product=ProductType.CARD,
        )
        result = self.policy.evaluate(app_input)
        assert result.status == ApplicationStatus.REJECTED
        assert len(result.rejection_reasons) == 1
        assert "debe ser al menos 3,000,000.00 COP" in result.rejection_reasons[0]


class TestApplicationEvaluator:
    """Tests for ApplicationEvaluator concern and registry."""

    def test_evaluator_routes_to_correct_strategy(self):
        evaluator = ApplicationEvaluator()
        phone_input = DummyApplicationInput(
            amount=1_200_000,
            monthly_income=1_000_000,
            employment_months=12,
            external_score=750,
            product=ProductType.PHONE,
        )
        res = evaluator.evaluate(phone_input)
        assert res.status == ApplicationStatus.APPROVED

    def test_unsupported_product_raises_error(self):
        evaluator = ApplicationEvaluator()
        bad_input = DummyApplicationInput(
            amount=1_000_000,
            monthly_income=1_000_000,
            employment_months=12,
            external_score=700,
            product="UNKNOWN_PRODUCT",
        )
        with pytest.raises(UnsupportedProductError):
            evaluator.evaluate(bad_input)
