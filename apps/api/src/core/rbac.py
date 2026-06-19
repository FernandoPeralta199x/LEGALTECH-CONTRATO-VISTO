from collections.abc import Callable
from typing import Annotated

from fastapi import Depends, HTTPException, Request, status

from src.core.tenant import TenantContext, get_tenant_context
from src.modules.audit import actions
from src.modules.audit.service import AuditLogService, get_audit_log_service
from src.modules.roles.service import RolePermissionService, get_role_permission_service


def get_permission_service(
    service: Annotated[RolePermissionService, Depends(get_role_permission_service)],
) -> RolePermissionService:
    return service


def require_permission(permission: str) -> Callable:
    async def dependency(
        request: Request,
        tenant: Annotated[TenantContext, Depends(get_tenant_context)],
        permission_service: Annotated[
            RolePermissionService,
            Depends(get_permission_service),
        ],
        audit_log: Annotated[AuditLogService, Depends(get_audit_log_service)],
    ) -> TenantContext:
        has_permission = permission_service.has_permission(
            organization_id=tenant.organization_id,
            role=tenant.role,
            permission=permission,
        )
        if not has_permission:
            try:
                audit_log.record_event(
                    organization_id=tenant.organization_id,
                    user_id=tenant.user_id,
                    action=actions.RBAC_DENIED,
                    entity_type="authorization",
                    metadata={
                        "permission": permission,
                        "role": tenant.role,
                        "path": request.url.path,
                        "method": request.method,
                    },
                    ip_address=request.client.host if request.client else None,
                    user_agent=request.headers.get("user-agent"),
                )
                audit_log.commit_pending()
            except Exception:
                pass
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Permission required: {permission}.",
            )

        return tenant

    return dependency
