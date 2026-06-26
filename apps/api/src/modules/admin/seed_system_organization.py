"""Seed idempotente da organizacao-sistema (ADR-0003, M-08).

A org-sistema e o tenant sentinela usado para auditar eventos de auth
PRE-organizacao (register, verify-email, login de e-mail inexistente),
porque audit_log.organization_id e ForeignKey NOT NULL para organizations.

Uso (igual ao seed de roles):
    python -m src.modules.admin.seed_system_organization
"""
from src.core.constants import SYSTEM_ORGANIZATION_ID, SYSTEM_ORGANIZATION_NAME
from src.db.session import SessionLocal
from src.models.organization import Organization


def seed_system_organization(db) -> bool:
    existing = db.get(Organization, SYSTEM_ORGANIZATION_ID)
    if existing is not None:
        return False
    db.add(
        Organization(
            id=SYSTEM_ORGANIZATION_ID,
            name=SYSTEM_ORGANIZATION_NAME,
            status="active",
        )
    )
    db.commit()
    return True


def main() -> None:
    db = SessionLocal()
    try:
        created = seed_system_organization(db)
        state = "created" if created else "already exists"
        print(f"system organization seed: {state} ({SYSTEM_ORGANIZATION_ID})")
    finally:
        db.close()


if __name__ == "__main__":
    main()
