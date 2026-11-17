"""Error contract from LLD v1.4 §6.1."""
from __future__ import annotations

from typing import Any


class ApiError(Exception):
    def __init__(self, status: int, code: str, message: str, **details: Any):
        super().__init__(message)
        self.status = status
        self.code = code
        self.message = message
        self.details = details

    def body(self) -> dict:
        return {"error": {"code": self.code, "message": self.message, **self.details}}


def invalid_request(message: str, **d) -> ApiError:
    return ApiError(400, "invalid_request", message, **d)


def authentication_required() -> ApiError:
    return ApiError(401, "authentication_required", "Sign in to continue.")


def permission_denied(permission: str, required_plan: str | None = None, reason: str = "plan_entitlement_missing") -> ApiError:
    d = {"permission": permission, "reason": reason}
    if required_plan:
        d["required_plan"] = required_plan
    return ApiError(403, "permission_denied", "Your access does not include this action.", **d)


def not_visible() -> ApiError:
    return ApiError(404, "resource_not_visible", "Not found.")


def idempotency_conflict(message="This Idempotency-Key was already used with a different request.") -> ApiError:
    return ApiError(409, "idempotency_conflict", message)


def usage_limit_reached(permission: str, limit: int, period_end: str, upgrade_plan: str) -> ApiError:
    return ApiError(429, "usage_limit_reached", "Your plan limit for this action has been reached.",
                    permission=permission, limit=limit, period_end=period_end, upgrade_plan=upgrade_plan)
