from functools import lru_cache
from typing import Literal

from pydantic import AliasChoices, Field, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
        case_sensitive=False,
        populate_by_name=True,
    )

    project_name: str = Field(default="legaltech", alias="PROJECT_NAME")
    environment: str | None = Field(default=None, alias="ENVIRONMENT")
    app_env: str = Field(default="local", alias="APP_ENV")
    app_name: str = Field(default="legaltech-api", alias="APP_NAME")
    app_version: str = Field(default="0.1.0", alias="APP_VERSION")
    enable_docs: bool = Field(default=True, alias="ENABLE_DOCS")
    log_level: str = Field(default="INFO", alias="LOG_LEVEL")
    rate_limit_enabled: bool = Field(default=True, alias="RATE_LIMIT_ENABLED")
    cors_allowed_origins: str = Field(
        default=(
            "http://localhost:3000,"
            "http://127.0.0.1:3000,"
            "http://192.168.0.102:3000"
        ),
        alias="CORS_ALLOWED_ORIGINS",
    )
    auth_provider: Literal["dev_jwt", "cognito"] = Field(
        default="dev_jwt",
        alias="AUTH_PROVIDER",
    )

    database_url: str = Field(
        default="postgresql+psycopg://legaltech:legaltech@localhost:5432/legaltech",
        alias="DATABASE_URL",
    )

    aws_region: str = Field(default="sa-east-1", alias="AWS_REGION")
    aws_account_id: str | None = Field(default=None, alias="AWS_ACCOUNT_ID")
    aws_profile: str | None = Field(default=None, alias="AWS_PROFILE")
    domain_name: str | None = Field(default=None, alias="DOMAIN_NAME")
    acm_certificate_arn: str | None = Field(
        default=None,
        alias="ACM_CERTIFICATE_ARN",
    )
    cloudfront_distribution_id: str | None = Field(
        default=None,
        alias="CLOUDFRONT_DISTRIBUTION_ID",
    )
    cognito_region: str | None = Field(default=None, alias="COGNITO_REGION")
    cognito_user_pool_id: str | None = Field(default=None, alias="COGNITO_USER_POOL_ID")
    cognito_client_id: str | None = Field(default=None, alias="COGNITO_CLIENT_ID")
    cognito_issuer_override: str | None = Field(default=None, alias="COGNITO_ISSUER")
    cognito_jwks_url_override: str | None = Field(
        default=None,
        alias="COGNITO_JWKS_URL",
    )
    cognito_organization_claim: str = Field(
        default="custom:organization_id",
        alias="COGNITO_ORGANIZATION_CLAIM",
    )
    cognito_role_claim: str = Field(
        default="custom:role",
        alias="COGNITO_ROLE_CLAIM",
    )
    cognito_token_use: Literal["id", "access"] = Field(
        default="id",
        alias="COGNITO_TOKEN_USE",
    )
    dev_jwt_enabled: bool = Field(default=False, alias="DEV_JWT_ENABLED")
    dev_jwt_secret: str | None = Field(default=None, alias="DEV_JWT_SECRET")
    dev_jwt_issuer: str = Field(
        default="legaltech-local-dev",
        alias="DEV_JWT_ISSUER",
    )
    dev_jwt_audience: str = Field(
        default="legaltech-local-api",
        alias="DEV_JWT_AUDIENCE",
    )
    local_upload_root: str = Field(
        default="storage/local_uploads",
        alias="LOCAL_UPLOAD_ROOT",
    )
    max_upload_size_bytes: int = Field(
        default=10 * 1024 * 1024,
        alias="MAX_UPLOAD_SIZE_BYTES",
        gt=0,
    )
    storage_backend: Literal["local", "s3"] = Field(
        default="local",
        alias="STORAGE_BACKEND",
    )
    s3_documents_bucket: str | None = Field(
        default=None,
        alias="S3_DOCUMENTS_BUCKET",
    )
    aws_endpoint_url: str | None = Field(default=None, alias="AWS_ENDPOINT_URL")
    presigned_url_expires_in_seconds: int = Field(
        default=900,
        validation_alias=AliasChoices(
            "PRESIGNED_URL_EXPIRES_SECONDS",
            "PRESIGNED_URL_EXPIRES_IN_SECONDS",
        ),
        gt=0,
        le=3600,
    )
    local_processing_max_text_chars: int = Field(
        default=50_000,
        alias="LOCAL_PROCESSING_MAX_TEXT_CHARS",
        gt=0,
    )
    document_processing_max_attempts: int = Field(
        default=3,
        alias="DOCUMENT_PROCESSING_MAX_ATTEMPTS",
        ge=1,
    )
    queue_backend: Literal["local", "sqs"] = Field(
        default="local",
        alias="QUEUE_BACKEND",
    )
    local_queue_path: str = Field(
        default="storage/local_queue/document_processing.jsonl",
        alias="LOCAL_QUEUE_PATH",
    )
    sqs_document_processing_queue_url: str | None = Field(
        default=None,
        alias="SQS_DOCUMENT_PROCESSING_QUEUE_URL",
    )
    sqs_triage_queue_url: str | None = Field(
        default=None,
        alias="SQS_TRIAGE_QUEUE_URL",
    )
    sqs_external_collection_queue_url: str | None = Field(
        default=None,
        alias="SQS_EXTERNAL_COLLECTION_QUEUE_URL",
    )
    sqs_contract_analysis_queue_url: str | None = Field(
        default=None,
        alias="SQS_CONTRACT_ANALYSIS_QUEUE_URL",
    )
    sqs_compliance_queue_url: str | None = Field(
        default=None,
        alias="SQS_COMPLIANCE_QUEUE_URL",
    )
    sqs_report_queue_url: str | None = Field(
        default=None,
        alias="SQS_REPORT_QUEUE_URL",
    )

    # --- Adapter layer (external APIs) ---
    escavador_backend: Literal["mock", "real"] = Field(
        default="mock", alias="ESCAVADOR_BACKEND",
    )
    escavador_api_key: str | None = Field(
        default=None, alias="ESCAVADOR_API_KEY",
    )
    serasa_backend: Literal["mock", "real"] = Field(
        default="mock", alias="SERASA_BACKEND",
    )
    serasa_api_key: str | None = Field(
        default=None, alias="SERASA_API_KEY",
    )
    cnj_backend: Literal["mock", "real"] = Field(
        default="mock", alias="CNJ_BACKEND",
    )
    cnj_api_key: str | None = Field(
        default=None, alias="CNJ_API_KEY",
    )
    ocr_backend: Literal["mock", "real"] = Field(
        default="mock", alias="OCR_BACKEND",
    )
    ai_analysis_backend: Literal["mock", "real"] = Field(
        default="mock", alias="AI_ANALYSIS_BACKEND",
    )
    ai_analysis_provider: Literal["openai", "bedrock"] = Field(
        default="openai", alias="AI_ANALYSIS_PROVIDER",
    )
    ai_analysis_api_key: str | None = Field(
        default=None, alias="AI_ANALYSIS_API_KEY",
    )

    # --- E-mail adapter ---
    email_backend: Literal["mock", "ses"] = Field(
        default="mock", alias="EMAIL_BACKEND",
    )
    email_sender: str | None = Field(default=None, alias="EMAIL_SENDER")
    frontend_base_url: str = Field(
        default="http://localhost:3000", alias="FRONTEND_BASE_URL",
    )

    secrets_external_apis_name: str | None = Field(
        default=None,
        alias="SECRETS_EXTERNAL_APIS_NAME",
    )
    openai_api_secret_name: str | None = Field(
        default=None,
        alias="OPENAI_API_SECRET_NAME",
    )

    @field_validator("database_url", mode="before")
    @classmethod
    def normalize_database_url(cls, value: str) -> str:
        if value.startswith("postgresql://"):
            return value.replace("postgresql://", "postgresql+psycopg://", 1)

        return value

    @field_validator("cors_allowed_origins")
    @classmethod
    def reject_wildcard_cors(cls, value: str) -> str:
        origins = [origin.strip() for origin in value.split(",") if origin.strip()]
        if "*" in origins:
            raise ValueError("CORS_ALLOWED_ORIGINS must not include wildcard '*'.")

        return value

    @property
    def cognito_issuer(self) -> str | None:
        if self.cognito_issuer_override:
            return self.cognito_issuer_override

        if not self.cognito_user_pool_id:
            return None

        region = self.cognito_region or self.aws_region
        return (
            f"https://cognito-idp.{region}.amazonaws.com/"
            f"{self.cognito_user_pool_id}"
        )

    @property
    def cognito_jwks_url(self) -> str | None:
        if self.cognito_jwks_url_override:
            return self.cognito_jwks_url_override

        if not self.cognito_issuer:
            return None

        return f"{self.cognito_issuer}/.well-known/jwks.json"

    @property
    def cors_origins(self) -> list[str]:
        return [
            origin.strip()
            for origin in self.cors_allowed_origins.split(",")
            if origin.strip()
        ]


@lru_cache
def get_settings() -> Settings:
    return Settings()
