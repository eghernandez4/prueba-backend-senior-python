"""
Repository for credit applications persistence.
"""

from typing import List, Optional

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models import Application
from app.schemas import ApplicationStatus, ProductType


class ApplicationRepository:
    """Encapsulates database operations for Application entities."""

    def __init__(self, db: Session) -> None:
        self.db = db

    def create(self, application: Application) -> Application:
        """Persist a new application entity."""
        self.db.add(application)
        self.db.commit()
        self.db.refresh(application)
        return application

    def get_by_id(self, application_id: int) -> Optional[Application]:
        """Fetch an application by primary key."""
        stmt = select(Application).where(Application.id == application_id)
        return self.db.scalars(stmt).first()

    def list(
        self,
        status: Optional[ApplicationStatus | str] = None,
        product: Optional[ProductType | str] = None,
    ) -> List[Application]:
        """Query applications with optional status and product filters."""
        stmt = select(Application)
        if status is not None:
            status_val = status.value if isinstance(status, ApplicationStatus) else str(status)
            stmt = stmt.where(Application.status == status_val)
        if product is not None:
            product_val = product.value if isinstance(product, ProductType) else str(product)
            stmt = stmt.where(Application.product == product_val)

        stmt = stmt.order_by(Application.id.desc())
        return list(self.db.scalars(stmt).all())

    def save(self, application: Application) -> Application:
        """Save updates to an existing application entity."""
        self.db.add(application)
        self.db.commit()
        self.db.refresh(application)
        return application
