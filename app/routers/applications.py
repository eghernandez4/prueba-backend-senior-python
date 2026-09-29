"""
Router for credit applications endpoints.
"""

from typing import List, Optional

from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.orm import Session

from app.database import get_db
from app.repositories.application_repository import ApplicationRepository
from app.schemas import (
    ApplicationCreate,
    ApplicationResponse,
    ApplicationStatus,
    ProductType,
)
from app.services.application_service import ApplicationService
from app.strategies.evaluator import ApplicationEvaluator, default_evaluator

router = APIRouter(prefix="/applications", tags=["Applications"])


def get_application_repository(db: Session = Depends(get_db)) -> ApplicationRepository:
    """Dependency provider for ApplicationRepository."""
    return ApplicationRepository(db)


def get_application_evaluator() -> ApplicationEvaluator:
    """Dependency provider for ApplicationEvaluator concern."""
    return default_evaluator


def get_application_service(
    repository: ApplicationRepository = Depends(get_application_repository),
    evaluator: ApplicationEvaluator = Depends(get_application_evaluator),
) -> ApplicationService:
    """Dependency provider for ApplicationService."""
    return ApplicationService(repository=repository, evaluator=evaluator)


@router.post(
    "",
    response_model=ApplicationResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Crear y evaluar una nueva solicitud de crédito",
)
def create_application(
    payload: ApplicationCreate,
    service: ApplicationService = Depends(get_application_service),
) -> ApplicationResponse:
    """
    Recibe la solicitud de crédito, la evalúa con la política correspondiente al producto
    y la persiste con su decisión ('APPROVED' o 'REJECTED') y razones de rechazo.
    """
    return service.create_application(payload)


@router.get(
    "/{id}",
    response_model=ApplicationResponse,
    summary="Obtener una solicitud de crédito por ID",
)
def get_application_by_id(
    id: int,
    service: ApplicationService = Depends(get_application_service),
) -> ApplicationResponse:
    """
    Retorna los datos y la decisión de una solicitud existente por su ID.
    """
    return service.get_application(id)


@router.get(
    "",
    response_model=List[ApplicationResponse],
    summary="Listar solicitudes de crédito con filtros opcionales",
)
def list_applications(
    status: Optional[ApplicationStatus] = Query(
        None, description="Filtrar por estado: APPROVED o REJECTED"
    ),
    product: Optional[ProductType] = Query(
        None, description="Filtrar por tipo de producto: PHONE, TWIST o CARD"
    ),
    service: ApplicationService = Depends(get_application_service),
) -> List[ApplicationResponse]:
    """
    Lista las solicitudes de crédito persistidas con filtros opcionales por estado y producto.
    """
    return service.list_applications(status=status, product=product)


@router.post(
    "/{id}/reevaluate",
    response_model=ApplicationResponse,
    summary="Reevaluar una solicitud existente con las políticas actuales",
)
def reevaluate_application(
    id: int,
    service: ApplicationService = Depends(get_application_service),
) -> ApplicationResponse:
    """
    Ejecuta una nueva evaluación sobre una solicitud existente utilizando las reglas
    de política vigentes y actualiza su decisión en la base de datos.
    """
    return service.reevaluate_application(id)
