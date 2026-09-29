"""
Base abstract definition for credit evaluation strategies.
"""

from abc import ABC, abstractmethod
from typing import Protocol, runtime_checkable

from app.schemas import EvaluationResult, ProductType


@runtime_checkable
class ApplicationEvaluationInput(Protocol):
    """Protocol specifying the fields required to evaluate an application."""

    amount: int
    monthly_income: int
    employment_months: int
    external_score: int
    product: ProductType | str


class BaseEvaluationPolicy(ABC):
    """Abstract base class for credit policy evaluation strategies."""

    FIXED_TERM_MONTHS: int = 12

    def calculate_installment(self, amount: int) -> float:
        """Calculate monthly installment for fixed 12-month term."""
        return amount / float(self.FIXED_TERM_MONTHS)

    @abstractmethod
    def evaluate(self, application: ApplicationEvaluationInput) -> EvaluationResult:
        """
        Evaluate application against the policy rules.

        Returns:
            EvaluationResult with status APPROVED or REJECTED and rejection reasons.
        """
        raise NotImplementedError
