"""Validate LegalTech environment files without contacting external services."""

from __future__ import annotations

import argparse
from pathlib import Path


VALID_ENVIRONMENTS = {"local", "dev", "staging", "prod"}
BACKEND_AUTH_PROVIDERS = {"dev_jwt", "cognito"}
STORAGE_BACKENDS = {"local", "s3"}
QUEUE_BACKENDS = {"local", "sqs"}


def parse_env_file(path: Path) -> dict[str, str]:
    values: dict[str, str] = {}
    for raw_line in path.read_text(encoding="utf-8").splitlines():
        line = raw_line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue

        key, value = line.split("=", 1)
        key = key.strip()
        value = value.strip().strip('"').strip("'")
        values[key] = value

    return values


def is_blank(values: dict[str, str], key: str) -> bool:
    return values.get(key, "").strip() == ""


def is_true(value: str | None) -> bool:
    return str(value or "").strip().lower() in {"1", "true", "yes", "on"}


def require(
    values: dict[str, str],
    keys: list[str],
    errors: list[str],
    *,
    context: str,
) -> None:
    for key in keys:
        if is_blank(values, key):
            errors.append(f"{context}: variavel obrigatoria ausente ou vazia: {key}")


def validate_backend(
    values: dict[str, str],
    environment: str,
    errors: list[str],
    warnings: list[str],
) -> None:
    require(
        values,
        [
            "APP_ENV",
            "APP_NAME",
            "LOG_LEVEL",
            "CORS_ALLOWED_ORIGINS",
            "DATABASE_URL",
            "AUTH_PROVIDER",
        ],
        errors,
        context="backend",
    )

    app_env = values.get("APP_ENV", "")
    if app_env and app_env != environment:
        warnings.append(
            f"backend: APP_ENV={app_env} difere do ambiente informado {environment}"
        )

    cors_origins = [
        origin.strip()
        for origin in values.get("CORS_ALLOWED_ORIGINS", "").split(",")
        if origin.strip()
    ]
    if "*" in cors_origins:
        errors.append("backend/cors: wildcard '*' nao e permitido")
    if environment == "local":
        allowed_local_origins = {
            "http://localhost:3000",
            "http://127.0.0.1:3000",
            "http://192.168.0.102:3000",
        }
        invalid_local_origins = sorted(
            origin for origin in cors_origins if origin not in allowed_local_origins
        )
        if invalid_local_origins:
            errors.append(
                "backend/cors: MVP local permite apenas origens explicitas: "
                + ", ".join(sorted(allowed_local_origins))
            )

    auth_provider = values.get("AUTH_PROVIDER", "")
    if auth_provider and auth_provider not in BACKEND_AUTH_PROVIDERS:
        errors.append(f"backend: AUTH_PROVIDER invalido: {auth_provider}")

    dev_jwt_enabled = is_true(values.get("DEV_JWT_ENABLED"))
    if environment != "local" and dev_jwt_enabled:
        errors.append("backend: DEV_JWT_ENABLED=true e permitido apenas em local")

    if environment != "local" and auth_provider == "dev_jwt":
        errors.append("backend: AUTH_PROVIDER=dev_jwt e permitido apenas em local")

    if auth_provider == "dev_jwt":
        require(
            values,
            ["DEV_JWT_ENABLED", "DEV_JWT_SECRET", "DEV_JWT_ISSUER", "DEV_JWT_AUDIENCE"],
            errors,
            context="backend/dev_jwt",
        )
        if environment == "local" and not dev_jwt_enabled:
            errors.append("backend: DEV_JWT_ENABLED deve ser true com dev_jwt local")

    if auth_provider == "cognito" or environment != "local":
        require(
            values,
            [
                "COGNITO_REGION",
                "COGNITO_USER_POOL_ID",
                "COGNITO_CLIENT_ID",
                "COGNITO_ORGANIZATION_CLAIM",
                "COGNITO_ROLE_CLAIM",
                "COGNITO_TOKEN_USE",
            ],
            errors,
            context="backend/cognito",
        )
        if is_blank(values, "COGNITO_ISSUER"):
            warnings.append("backend/cognito: COGNITO_ISSUER vazio, sera derivado se possivel")
        if is_blank(values, "COGNITO_JWKS_URL"):
            warnings.append("backend/cognito: COGNITO_JWKS_URL vazio, sera derivado se possivel")

    storage_backend = values.get("STORAGE_BACKEND", "local")
    if storage_backend not in STORAGE_BACKENDS:
        errors.append(f"backend: STORAGE_BACKEND invalido: {storage_backend}")

    if storage_backend == "s3" or environment in {"staging", "prod"}:
        require(
            values,
            ["AWS_REGION", "S3_DOCUMENTS_BUCKET"],
            errors,
            context="backend/storage",
        )
        if environment in {"staging", "prod"} and storage_backend != "s3":
            errors.append("backend/storage: staging/prod devem usar STORAGE_BACKEND=s3")

    if is_blank(values, "PRESIGNED_URL_EXPIRES_SECONDS") and is_blank(
        values, "PRESIGNED_URL_EXPIRES_IN_SECONDS"
    ):
        errors.append("backend/storage: configure PRESIGNED_URL_EXPIRES_SECONDS")

    queue_backend = values.get("QUEUE_BACKEND", "local")
    if queue_backend not in QUEUE_BACKENDS:
        errors.append(f"backend: QUEUE_BACKEND invalido: {queue_backend}")

    if queue_backend == "sqs" or environment in {"staging", "prod"}:
        require(
            values,
            ["SQS_DOCUMENT_PROCESSING_QUEUE_URL"],
            errors,
            context="backend/queues",
        )
        if environment in {"staging", "prod"} and queue_backend != "sqs":
            errors.append("backend/queues: staging/prod devem usar QUEUE_BACKEND=sqs")

    for key in ["SECRETS_EXTERNAL_APIS_NAME", "OPENAI_API_SECRET_NAME"]:
        if environment in {"staging", "prod"} and is_blank(values, key):
            warnings.append(f"backend/secrets: {key} vazio para ambiente {environment}")


def validate_frontend(
    values: dict[str, str],
    environment: str,
    errors: list[str],
    warnings: list[str],
) -> None:
    require(
        values,
        [
            "NEXT_PUBLIC_API_BASE_URL",
            "NEXT_PUBLIC_ENABLE_API_MOCK_FALLBACK",
            "NEXT_PUBLIC_APP_ENV",
            "NEXT_PUBLIC_APP_NAME",
        ],
        errors,
        context="frontend",
    )

    app_env = values.get("NEXT_PUBLIC_APP_ENV", "")
    if app_env and app_env != environment:
        warnings.append(
            "frontend: NEXT_PUBLIC_APP_ENV="
            f"{app_env} difere do ambiente informado {environment}"
        )

    mock_fallback = is_true(values.get("NEXT_PUBLIC_ENABLE_API_MOCK_FALLBACK"))
    if environment in {"staging", "prod"} and mock_fallback:
        errors.append(
            "frontend: NEXT_PUBLIC_ENABLE_API_MOCK_FALLBACK deve ser false em staging/prod"
        )
    elif environment == "dev" and mock_fallback:
        warnings.append("frontend: mock fallback em dev deve ser temporario e documentado")


def validate_aws(
    values: dict[str, str],
    environment: str,
    errors: list[str],
    warnings: list[str],
) -> None:
    require(
        values,
        ["AWS_ACCOUNT_ID", "AWS_REGION", "AWS_PROFILE", "PROJECT_NAME", "ENVIRONMENT"],
        errors,
        context="aws",
    )

    file_environment = values.get("ENVIRONMENT", "")
    if file_environment and file_environment != environment:
        warnings.append(
            f"aws: ENVIRONMENT={file_environment} difere do ambiente informado {environment}"
        )

    if environment in {"staging", "prod"}:
        require(
            values,
            ["DOMAIN_NAME", "ACM_CERTIFICATE_ARN", "CLOUDFRONT_DISTRIBUTION_ID"],
            errors,
            context="aws/frontend",
        )

    validate_backend(values, environment, errors, warnings)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--env-file", required=True, type=Path)
    parser.add_argument(
        "--environment",
        required=True,
        choices=sorted(VALID_ENVIRONMENTS),
    )
    parser.add_argument(
        "--target",
        required=True,
        choices=["backend", "frontend", "aws"],
    )
    args = parser.parse_args()

    if not args.env_file.exists():
        print(f"ERRO: arquivo nao encontrado: {args.env_file}")
        return 1

    values = parse_env_file(args.env_file)
    errors: list[str] = []
    warnings: list[str] = []

    if args.target == "backend":
        validate_backend(values, args.environment, errors, warnings)
    elif args.target == "frontend":
        validate_frontend(values, args.environment, errors, warnings)
    else:
        validate_aws(values, args.environment, errors, warnings)

    for warning in warnings:
        print(f"AVISO: {warning}")

    if errors:
        for error in errors:
            print(f"ERRO: {error}")
        return 1

    print(
        "OK: variaveis validas para "
        f"target={args.target} environment={args.environment}"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
