import os
import unittest

from src.core.config import Settings, enforce_production_safety, get_settings


def _settings(**over):
    base = dict(
        APP_ENV="staging",
        AUTH_PROVIDER="cognito",
        DEV_JWT_ENABLED=False,
        DEV_JWT_SECRET="fictitious-local-dev-secret-32-bytes-minimum",
        ENABLE_DOCS=False,
        AI_ANALYSIS_BACKEND="real",
        OCR_BACKEND="real",
        ESCAVADOR_BACKEND="real",
        SERASA_BACKEND="real",
        CNJ_BACKEND="real",
        EMAIL_BACKEND="ses",
    )
    base.update(over)
    return Settings(**base)


class ProductionSafetyGateTest(unittest.TestCase):
    def test_staging_all_real_passes(self) -> None:
        enforce_production_safety(_settings())  # nao levanta

    def test_local_never_enforced(self) -> None:
        enforce_production_safety(
            _settings(
                APP_ENV="local", AI_ANALYSIS_BACKEND="mock",
                AUTH_PROVIDER="dev_jwt", DEV_JWT_ENABLED=True, EMAIL_BACKEND="mock",
            )
        )

    def test_mock_legal_backend_blocks(self) -> None:
        with self.assertRaises(RuntimeError) as ctx:
            enforce_production_safety(_settings(AI_ANALYSIS_BACKEND="mock"))
        self.assertIn("AI_ANALYSIS_BACKEND", str(ctx.exception))

    def test_dev_jwt_blocks(self) -> None:
        with self.assertRaises(RuntimeError):
            enforce_production_safety(_settings(DEV_JWT_ENABLED=True))

    def test_dev_auth_provider_blocks_in_prod(self) -> None:
        with self.assertRaises(RuntimeError):
            enforce_production_safety(_settings(APP_ENV="prod", AUTH_PROVIDER="dev_jwt"))

    def test_builder_fail_closed_without_db_outside_local(self) -> None:
        from src.modules.contracts.operational import build_operational_repositories

        old = os.environ.get("APP_ENV")
        os.environ["APP_ENV"] = "staging"
        get_settings.cache_clear()
        try:
            with self.assertRaises(RuntimeError):
                build_operational_repositories()  # db=None em staging
        finally:
            if old is None:
                os.environ.pop("APP_ENV", None)
            else:
                os.environ["APP_ENV"] = old
            get_settings.cache_clear()
