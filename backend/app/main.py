"""
Application entrypoint.

Run with:  uvicorn app.main:app --reload --port 8000   (from backend/)
"""
from contextlib import asynccontextmanager

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from app.core.config import get_settings
from app.core.exceptions import CareerAssistantError
from app.core.logging_config import configure_logging, get_logger
from app.routers import health, resume

settings = get_settings()
configure_logging(debug=settings.debug)
logger = get_logger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("%s starting up in '%s' mode", settings.app_name, settings.environment)
    yield
    logger.info("%s shutting down", settings.app_name)


app = FastAPI(
    title=settings.app_name,
    version="2.0.0",
    description=(
        "A retrieval-augmented Q&A API that lets users upload a resume and ask "
        "career questions grounded in that document, powered by AWS Bedrock + FAISS."
    ),
    lifespan=lifespan,
)

# CORS: locked down to `ALLOWED_ORIGINS` from settings instead of "*".
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.allowed_origins,
    allow_credentials=True,
    allow_methods=["GET", "POST"],
    allow_headers=["*"],
)

app.include_router(health.router)
app.include_router(resume.router)


@app.exception_handler(CareerAssistantError)
async def domain_error_handler(request: Request, exc: CareerAssistantError) -> JSONResponse:
    """Catch-all for any domain error that a router didn't already translate
    into an HTTPException — ensures the client always gets clean JSON, never
    a raw traceback."""
    logger.warning("Unhandled domain error on %s: %s", request.url.path, exc)
    return JSONResponse(status_code=400, content={"detail": str(exc)})


@app.get("/", tags=["health"])
def root():
    return {"message": f"{settings.app_name} is running. See /docs for the API reference."}
