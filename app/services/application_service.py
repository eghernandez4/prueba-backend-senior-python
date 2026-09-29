"""
Application service for business orchestration.
"""

from typing import List, Optional

from app.exceptions import ApplicationNotFoundError
from app.models import Application
from app.repositories.application_repository import ApplicationRepository
from app.schemas import ApplicationCreate, ApplicationStatus, ProductType
from app.strategies.evaluator import ApplicationEvaluator


class ApplicationService:
    """Orchestrates application evaluation and persistence."""

    def __init__(
        self,
        repository: ApplicationRepository,
        evaluator: ApplicationEvaluator,
    ) -> None:
        self.repository = repository
        self.evaluator = evaluator

    def create_application(self, data: ApplicationCreate) -> Application:
        """
        Evaluate application against the registered policy and persist it.
        """
        eval_result = self.evaluator.evaluate(data)

        application = Application(
            amount=data.amount,
            monthly_income=data.monthly_income,
            employment_months=data.employment_months,
            external_score=data.external_score,
            product=data.product.value,
            status=eval_result.status.value,
            rejection_reasons=eval_result.rejection_reasons,
        )

        return self.repository.create(application)

    def get_application(self, application_id: int) -> Application:
        """
        Retrieve an application by its ID.

        Raises:
            ApplicationNotFoundError: If the application does not exist.
        """
        application = self.repository.get_by_id(application_id)
        if application is None:
            raise ApplicationNotFoundError(application_id)
        return application

    def list_applications(
        self,
        status: Optional[ApplicationStatus] = None,
        product: Optional[ProductType] = None,
    ) -> List[Application]:
        """
        List applications matching optional status and product filters.
        """
        return self.repository.list(status=status, product=product)

    def reevaluate_application(self, application_id: int) -> Application:
        """
        Re-evaluate an existing application against current policy rules.

        Raises:
            ApplicationNotFoundError: If the application does not exist.
        """
        application = self.get_application(application_id)

        eval_result = self.evaluator.evaluate(application)
        application.status = eval_result.status.value
        application.rejection_reasons = eval_result.rejection_reasons

        return self.repository.save(application)
