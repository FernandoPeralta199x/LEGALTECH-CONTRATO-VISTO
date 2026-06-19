from fastapi import FastAPI, HTTPException
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware

import logging

from src.adapters.escavador import create_escavador_adapter
from src.adapters.serasa import create_serasa_adapter
from src.adapters.cnj import create_cnj_adapter
from src.adapters.ocr import create_ocr_adapter
from src.adapters.ai_analysis import create_ai_analysis_adapter
from src.core.config import get_settings
from src.core.logging import configure_logging
from src.modules.auth.router import router as auth_router
from src.modules.audit.router import router as audit_router
from src.modules.case_parties.router import router as case_parties_router
from src.modules.cases.router import router as cases_router
from src.modules.clients.router import router as clients_router
from src.modules.common.exceptions import ResourceNotFoundError
from src.modules.common.responses import error_response
from src.modules.document_processing.router import router as document_processing_router
from src.modules.documents.router import router as documents_router
from src.modules.documents.router import case_router as case_documents_router
from src.modules.health.router import router as health_router
from src.modules.provider_results.router import router as provider_results_router
from src.modules.requests.router import router as requests_router
from src.modules.reports.router import router as reports_router
from src.modules.timeline.router import router as timeline_router
from src.modules.triage.router import router as triage_router


HTTP_ERROR_CODES = {
    401: "UNAUTHORIZED",
    403: "FORBIDDEN",
    404: "NOT_FOUND",
    400: "VALIDATION_ERROR",
    413: "VALIDATION_ERROR",
    422: "VALIDATION_ERROR",
}

SECURITY_HEADERS = {
    "X-Content-Type-Options": "nosniff",
    "Referrer-Policy": "no-referrer",
    "X-Frame-Options": "DENY",
    "Permissions-Policy": "geolocation=(), microphone=(), camera=()",
}


def create_app() -> FastAPI:
    settings = get_settings()
    configure_logging(settings.log_level)

    app = FastAPI(
        title=settings.app_name,
        version=settings.app_version,
        docs_url="/docs" if settings.enable_docs else None,
        redoc_url="/redoc" if settings.enable_docs else None,
        openapi_url="/openapi.json" if settings.enable_docs else None,
    )
    if settings.cors_origins:
        app.add_middleware(
            CORSMiddleware,
            allow_origins=settings.cors_origins,
            allow_methods=["GET", "POST", "PATCH", "OPTIONS"],
            allow_headers=["Authorization", "Content-Type"],
        )

    @app.middleware("http")
    async def add_security_headers(request, call_next):
        response = await call_next(request)
        for header, value in SECURITY_HEADERS.items():
            response.headers.setdefault(header, value)

        if request.url.path.startswith("/api/v1"):
            response.headers.setdefault("Cache-Control", "no-store")

        return response

    @app.exception_handler(ResourceNotFoundError)
    async def resource_not_found_handler(_, exc: ResourceNotFoundError) -> JSONResponse:
        return JSONResponse(
            status_code=404,
            content=error_response(code=exc.code, message=str(exc)),
        )

    @app.exception_handler(HTTPException)
    async def http_exception_handler(_, exc: HTTPException) -> JSONResponse:
        return JSONResponse(
            status_code=exc.status_code,
            content=error_response(
                code=HTTP_ERROR_CODES.get(exc.status_code, "INTERNAL_ERROR"),
                message=str(exc.detail),
            ),
            headers=exc.headers,
        )

    app.include_router(health_router)
    app.include_router(auth_router)
    app.include_router(clients_router)
    app.include_router(cases_router)
    app.include_router(case_parties_router)
    app.include_router(case_documents_router)
    app.include_router(timeline_router)
    app.include_router(triage_router)
    app.include_router(provider_results_router)
    app.include_router(reports_router)
    app.include_router(documents_router)
    app.include_router(requests_router)
    app.include_router(document_processing_router)
    app.include_router(audit_router)

    _register_adapters(app, settings)

    return app


def _register_adapters(app: FastAPI, settings) -> None:
    """Instantiate adapters based on settings and store them on app.state."""
    log = logging.getLogger("legaltech.adapters")

    app.state.escavador = create_escavador_adapter(
        backend=settings.escavador_backend,
        api_key=settings.escavador_api_key,
    )
    app.state.serasa = create_serasa_adapter(
        backend=settings.serasa_backend,
        api_key=settings.serasa_api_key,
    )
    app.state.cnj = create_cnj_adapter(
        backend=settings.cnj_backend,
        api_key=settings.cnj_api_key,
    )
    app.state.ocr = create_ocr_adapter(
        backend=settings.ocr_backend,
        aws_region=settings.aws_region,
    )
    app.state.ai_analysis = create_ai_analysis_adapter(
        backend=settings.ai_analysis_backend,
        provider=settings.ai_analysis_provider,
        api_key=settings.ai_analysis_api_key,
    )

    adapters_summary = {
        "escavador": settings.escavador_backend,
        "serasa": settings.serasa_backend,
        "cnj": settings.cnj_backend,
        "ocr": settings.ocr_backend,
        "ai_analysis": settings.ai_analysis_backend,
    }
    log.info("Adapters registrados: %s", adapters_summary)


app = create_app()
