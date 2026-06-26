"""Constantes centrais de dominio.

SYSTEM_ORGANIZATION_ID: tenant sentinela usado para auditar eventos de auth
PRE-organizacao (register, verify-email, login de e-mail inexistente), pois
audit_log.organization_id e ForeignKey NOT NULL para organizations (ADR-0003, M-08).
"""
from uuid import UUID

SYSTEM_ORGANIZATION_ID = UUID("00000000-0000-4000-8000-000000000000")
SYSTEM_ORGANIZATION_NAME = "SYSTEM"
