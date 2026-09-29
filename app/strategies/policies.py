"""
Concrete evaluation policy strategies for each product type.
"""

from typing import List

from app.schemas import ApplicationStatus, EvaluationResult
from app.strategies.base import ApplicationEvaluationInput, BaseEvaluationPolicy


class PhonePolicy(BaseEvaluationPolicy):
    """
    Conservative policy for PHONE product:
    - score >= 700
    - employment_months >= 12
    - cuota <= 25% monthly_income
    """

    MIN_SCORE: int = 700
    MIN_EMPLOYMENT_MONTHS: int = 12
    MAX_DEBT_RATIO: float = 0.25

    def evaluate(self, application: ApplicationEvaluationInput) -> EvaluationResult:
        rejection_reasons: List[str] = []

        if application.external_score < self.MIN_SCORE:
            rejection_reasons.append(
                f"Score externo ({application.external_score}) menor al mínimo requerido ({self.MIN_SCORE})"
            )

        if application.employment_months < self.MIN_EMPLOYMENT_MONTHS:
            rejection_reasons.append(
                f"Antigüedad laboral ({application.employment_months} meses) menor al mínimo requerido ({self.MIN_EMPLOYMENT_MONTHS} meses)"
            )

        installment = self.calculate_installment(application.amount)
        max_allowed_installment = application.monthly_income * self.MAX_DEBT_RATIO
        if installment > max_allowed_installment:
            rejection_reasons.append(
                f"La cuota mensual ({installment:,.2f} COP) supera el 25% del ingreso mensual ({max_allowed_installment:,.2f} COP)"
            )

        if rejection_reasons:
            return EvaluationResult(
                status=ApplicationStatus.REJECTED,
                rejection_reasons=rejection_reasons,
            )

        return EvaluationResult(status=ApplicationStatus.APPROVED, rejection_reasons=[])


class TwistPolicy(BaseEvaluationPolicy):
    """
    Standard policy for TWIST product:
    - score >= 600
    - cuota <= 35% monthly_income
    """

    MIN_SCORE: int = 600
    MAX_DEBT_RATIO: float = 0.35

    def evaluate(self, application: ApplicationEvaluationInput) -> EvaluationResult:
        rejection_reasons: List[str] = []

        if application.external_score < self.MIN_SCORE:
            rejection_reasons.append(
                f"Score externo ({application.external_score}) menor al mínimo requerido ({self.MIN_SCORE})"
            )

        installment = self.calculate_installment(application.amount)
        max_allowed_installment = application.monthly_income * self.MAX_DEBT_RATIO
        if installment > max_allowed_installment:
            rejection_reasons.append(
                f"La cuota mensual ({installment:,.2f} COP) supera el 35% del ingreso mensual ({max_allowed_installment:,.2f} COP)"
            )

        if rejection_reasons:
            return EvaluationResult(
                status=ApplicationStatus.REJECTED,
                rejection_reasons=rejection_reasons,
            )

        return EvaluationResult(status=ApplicationStatus.APPROVED, rejection_reasons=[])


class CardPolicy(BaseEvaluationPolicy):
    """
    Aggressive policy for CARD product:
    - score >= 550 OR (score >= 500 AND monthly_income >= 3,000,000)
    """

    MIN_DIRECT_SCORE: int = 550
    MIN_CONDITIONAL_SCORE: int = 500
    MIN_CONDITIONAL_INCOME: int = 3_000_000

    def evaluate(self, application: ApplicationEvaluationInput) -> EvaluationResult:
        is_approved = application.external_score >= self.MIN_DIRECT_SCORE or (
            application.external_score >= self.MIN_CONDITIONAL_SCORE
            and application.monthly_income >= self.MIN_CONDITIONAL_INCOME
        )

        if is_approved:
            return EvaluationResult(status=ApplicationStatus.APPROVED, rejection_reasons=[])

        rejection_reasons: List[str] = []
        if application.external_score < self.MIN_CONDITIONAL_SCORE:
            rejection_reasons.append(
                f"Score externo ({application.external_score}) menor al mínimo permitido ({self.MIN_CONDITIONAL_SCORE})"
            )
        else:
            rejection_reasons.append(
                f"Para score entre {self.MIN_CONDITIONAL_SCORE} y {self.MIN_DIRECT_SCORE - 1}, "
                f"el ingreso mensual ({application.monthly_income:,.2f} COP) debe ser al menos {self.MIN_CONDITIONAL_INCOME:,.2f} COP"
            )

        return EvaluationResult(
            status=ApplicationStatus.REJECTED,
            rejection_reasons=rejection_reasons,
        )
