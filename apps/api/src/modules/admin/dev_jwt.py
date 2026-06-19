import argparse
from datetime import UTC, datetime, timedelta

from src.core.config import Settings, get_settings


def create_dev_jwt(
    *,
    settings: Settings,
    organization_id: str,
    user_id: str,
    email: str,
    role: str,
    expires_minutes: int = 60,
) -> str:
    if settings.app_env != "local" or not settings.dev_jwt_enabled:
        raise RuntimeError("Local development JWT generation is disabled.")

    if not settings.dev_jwt_secret:
        raise RuntimeError("DEV_JWT_SECRET is required to generate a dev JWT.")

    try:
        import jwt
    except ImportError as exc:
        raise RuntimeError("PyJWT is required to generate a dev JWT.") from exc

    now = datetime.now(UTC)
    claims = {
        "iss": settings.dev_jwt_issuer,
        "aud": settings.dev_jwt_audience,
        "iat": now,
        "exp": now + timedelta(minutes=expires_minutes),
        "sub": user_id,
        "email": email,
        settings.cognito_organization_claim: organization_id,
        settings.cognito_role_claim: role,
        "token_use": "dev",
    }

    return jwt.encode(claims, settings.dev_jwt_secret, algorithm="HS256")


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Generate a local development JWT for API smoke testing."
    )
    parser.add_argument("--organization-id", required=True)
    parser.add_argument("--user-id", required=True)
    parser.add_argument("--email", required=True)
    parser.add_argument("--role", default="admin")
    parser.add_argument("--expires-minutes", type=int, default=60)

    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    token = create_dev_jwt(
        settings=get_settings(),
        organization_id=args.organization_id,
        user_id=args.user_id,
        email=args.email,
        role=args.role,
        expires_minutes=args.expires_minutes,
    )
    print(token)

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
