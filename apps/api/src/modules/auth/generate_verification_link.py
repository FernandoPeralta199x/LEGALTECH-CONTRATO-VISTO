import argparse
import hashlib

from src.db.session import SessionLocal
from src.models.user import User


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Generate a verification link for a pending user (local dev only)."
    )
    parser.add_argument("--email", required=True, help="User e-mail.")
    parser.add_argument(
        "--base-url",
        default="http://localhost:3000",
        help="Frontend base URL.",
    )
    return parser


def generate_link(*, email: str, base_url: str) -> str:
    db = SessionLocal()
    try:
        user = db.query(User).filter(User.email == email.lower().strip()).first()
        if not user:
            raise RuntimeError(f"User not found: {email}")
        if user.status != "pending_verification":
            raise RuntimeError(f"User is not pending verification: {user.status}")
        if not user.verification_token_hash:
            raise RuntimeError("User has no verification token.")

        # We cannot reverse the hash; this utility prints a fresh dev token and
        # updates the stored hash. Use only in local development.
        import secrets

        token = secrets.token_urlsafe(32)
        user.verification_token_hash = hashlib.sha256(token.encode("utf-8")).hexdigest()
        db.commit()

        return f"{base_url}/verify-email?email={email}&token={token}"
    finally:
        db.close()


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    link = generate_link(email=args.email, base_url=args.base_url)
    print(link)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
