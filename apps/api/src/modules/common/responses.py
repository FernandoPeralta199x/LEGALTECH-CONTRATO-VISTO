from datetime import UTC, datetime
from typing import Any
from uuid import uuid4


def _timestamp() -> str:
    return datetime.now(UTC).isoformat().replace("+00:00", "Z")


def _request_id(request_id: str | None = None) -> str:
    return request_id or str(uuid4())


def success_response(
    data: Any,
    message: str | None = None,
    *,
    request_id: str | None = None,
    source_mode: str = "real",
) -> dict[str, Any]:
    response: dict[str, Any] = {
        "success": True,
        "data": data,
        "error": None,
        "request_id": _request_id(request_id),
        "source_mode": source_mode,
        "timestamp": _timestamp(),
    }
    if message is not None:
        response["message"] = message

    return response


def error_response(
    *,
    code: str,
    message: str,
    details: dict[str, Any] | None = None,
    request_id: str | None = None,
    source_mode: str = "real",
) -> dict[str, Any]:
    return {
        "success": False,
        "data": None,
        "error": {
            "code": code,
            "message": message,
            "details": details or {},
        },
        "request_id": _request_id(request_id),
        "source_mode": source_mode,
        "timestamp": _timestamp(),
    }
