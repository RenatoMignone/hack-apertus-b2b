"""Safe public errors: validation/provider exception payloads never leave the API."""
from fastapi import HTTPException
from fastapi.exceptions import RequestValidationError
from sqlalchemy.exc import NoResultFound, SQLAlchemyError
from starlette.responses import JSONResponse

from backend.contracts.services import ServiceError


def response(request, status, code, message, retryable=False, details=None):
    return JSONResponse(status_code=status, content={"schema_version": "1", "error": {"code": code,
        "message": message, "retryable": retryable, "details": details or []},
        "request_id": getattr(request.state, "request_id", "unavailable")})


def install_errors(app):
    @app.exception_handler(RequestValidationError)
    async def validation(request, error):
        fields = [{"field": ".".join(map(str, item["loc"])), "type": item["type"]} for item in error.errors()]
        return response(request, 422, "invalid_request", "Request validation failed", details=fields)

    @app.exception_handler(HTTPException)
    async def http(request, error):
        output = response(request, error.status_code, "authentication_required" if error.status_code == 401 else "invalid_request",
                          "Authentication required" if error.status_code == 401 else "Request could not be accepted")
        output.headers.update(error.headers or {})
        return output

    @app.exception_handler(ServiceError)
    async def service(request, error):
        status = {"service_unavailable": 503, "budget_exceeded": 409, "stale_revision": 409,
                  "evidence_rejected": 409, "invalid_model_output": 502}.get(error.code, 503)
        return response(request, status, error.code, error.public_message, error.retryable)

    @app.exception_handler(PermissionError)
    @app.exception_handler(NoResultFound)
    async def not_found(request, error):
        return response(request, 404, "not_found", "Resource is unavailable")

    @app.exception_handler(ValueError)
    async def conflict(request, error):
        return response(request, 409, "conflict", "The operation conflicts with the current case state")

    @app.exception_handler(SQLAlchemyError)
    async def database(request, error):
        return response(request, 503, "storage_unavailable", "Storage is unavailable", True)

    @app.exception_handler(Exception)
    async def unexpected(request, error):
        return response(request, 503, "service_unavailable", "A required service is unavailable", True)
