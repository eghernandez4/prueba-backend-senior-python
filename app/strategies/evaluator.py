"""
Registry and Evaluator concern for credit application evaluation.
"""

from typing import Dict

from app.exceptions import UnsupportedProductError
from app.schemas import EvaluationResult, ProductType
from app.strategies.base import ApplicationEvaluationInput, BaseEvaluationPolicy
from app.strategies.policies import CardPolicy, PhonePolicy, TwistPolicy


class PolicyRegistry:
    """Registry that maps products to their corresponding evaluation policy."""

    def __init__(self) -> None:
        self._policies: Dict[ProductType, BaseEvaluationPolicy] = {}

    def register(self, product: ProductType, policy: BaseEvaluationPolicy) -> None:
        """Register a policy strategy for a product type."""
        self._policies[product] = policy

    def get(self, product: ProductType | str) -> BaseEvaluationPolicy:
        """
        Retrieve the policy strategy for a given product type.

        Raises:
            UnsupportedProductError: If no strategy is registered for the product.
        """
        try:
            enum_product = ProductType(product)
        except ValueError:
            raise UnsupportedProductError(str(product))

        policy = self._policies.get(enum_product)
        if policy is None:
            raise UnsupportedProductError(str(product))
        return policy


class ApplicationEvaluator:
    """
    Dedicated evaluation concern for credit applications.

    Decouples business evaluation logic from HTTP controllers and persistence layers.
    Uses the Strategy pattern via PolicyRegistry, satisfying the Open/Closed Principle
    and eliminating conditional branching in endpoints or services.
    """

    def __init__(self, registry: PolicyRegistry | None = None) -> None:
        if registry is None:
            registry = PolicyRegistry()
            registry.register(ProductType.PHONE, PhonePolicy())
            registry.register(ProductType.TWIST, TwistPolicy())
            registry.register(ProductType.CARD, CardPolicy())
        self.registry = registry

    def evaluate(self, application: ApplicationEvaluationInput) -> EvaluationResult:
        """
        Evaluate an application against the registered policy for its product type.
        """
        policy = self.registry.get(application.product)
        return policy.evaluate(application)


# Default shared evaluator instance
default_evaluator = ApplicationEvaluator()
