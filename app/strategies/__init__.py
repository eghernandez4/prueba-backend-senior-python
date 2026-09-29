"""
Strategies package for credit application evaluation.
"""

from app.strategies.base import ApplicationEvaluationInput, BaseEvaluationPolicy
from app.strategies.evaluator import (
    ApplicationEvaluator,
    PolicyRegistry,
    UnsupportedProductError,
    default_evaluator,
)
from app.strategies.policies import CardPolicy, PhonePolicy, TwistPolicy

__all__ = [
    "ApplicationEvaluationInput",
    "BaseEvaluationPolicy",
    "PhonePolicy",
    "TwistPolicy",
    "CardPolicy",
    "PolicyRegistry",
    "ApplicationEvaluator",
    "UnsupportedProductError",
    "default_evaluator",
]
