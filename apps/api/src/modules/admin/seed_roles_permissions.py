import argparse

from src.db.session import SessionLocal
from src.modules.audit.service import AuditLogService
from src.modules.common.identifiers import parse_uuid
from src.modules.roles.service import RolePermissionService


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Seed internal base RBAC permissions for one organization."
    )
    parser.add_argument(
        "--organization-id",
        required=True,
        help="Organization UUID that will receive the base permissions.",
    )
    parser.add_argument(
        "--actor-user-id",
        required=False,
        help="Optional internal user UUID responsible for the audit event.",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Run the seed and rollback instead of committing changes.",
    )

    return parser


def run(args: argparse.Namespace) -> int:
    organization_id = parse_uuid(args.organization_id)
    actor_user_id = parse_uuid(args.actor_user_id) if args.actor_user_id else None

    db = SessionLocal()
    try:
        result = RolePermissionService(db=db).seed_base_permissions(
            organization_id=organization_id,
            actor_user_id=actor_user_id,
            audit_service=AuditLogService(db),
        )
        if args.dry_run:
            db.rollback()
        else:
            db.commit()

        mode = "dry-run" if args.dry_run else "committed"
        print(
            "roles_permissions seed "
            f"{mode}: organization_id={organization_id} "
            f"created={result.created_count} existing={result.existing_count}"
        )
        for role_result in result.roles:
            print(
                f"- {role_result.role}: "
                f"created={role_result.created_count} "
                f"existing={role_result.existing_count}"
            )

        return 0
    except Exception:
        db.rollback()
        raise
    finally:
        db.close()


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    return run(args)


if __name__ == "__main__":
    raise SystemExit(main())
