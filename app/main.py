from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse

from app.database import Base, engine
from app.exceptions import DomainException
import app.models  # noqa: F401
from app.routers import applications_router

# Create tables on startup
Base.metadata.create_all(bind=engine)

app = FastAPI(title="Credit Evaluation Service")


@app.exception_handler(DomainException)
async def domain_exception_handler(request: Request, exc: DomainException):
    """
    Generic exception handler for all domain and business rule errors.
    Extracts status_code and message dynamically from the DomainException instance.
    """
    return JSONResponse(
        status_code=exc.status_code,
        content={"detail": exc.message},
    )


@app.get("/health")
def health():
    return {"status": "ok"}


# Register application routes
app.include_router(applications_router)
