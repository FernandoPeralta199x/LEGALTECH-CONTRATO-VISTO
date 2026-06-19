import unittest
from pathlib import Path

from sqlalchemy import inspect

from src.db.base import Base


class ModelMetadataTest(unittest.TestCase):
    def test_initial_tables_are_registered(self) -> None:
        import src.models  # noqa: F401

        expected_tables = {
            "organizations",
            "users",
            "roles_permissions",
            "clients",
            "case_parties",
            "cases",
            "documents",
            "external_queries_cache",
            "audit_log",
            "agent_executions",
            "document_chunks",
            "document_embeddings",
            "human_reviews",
            "reports",
        }

        self.assertEqual(expected_tables, set(Base.metadata.tables))

    def test_sensitive_tables_have_organization_id(self) -> None:
        import src.models  # noqa: F401

        sensitive_tables = {
            "users",
            "roles_permissions",
            "clients",
            "case_parties",
            "cases",
            "documents",
            "external_queries_cache",
            "audit_log",
            "agent_executions",
            "document_chunks",
            "document_embeddings",
            "human_reviews",
            "reports",
        }

        for table_name in sensitive_tables:
            with self.subTest(table=table_name):
                table = Base.metadata.tables[table_name]
                self.assertIn("organization_id", table.c)
                self.assertFalse(table.c.organization_id.nullable)

    def test_mutable_tables_have_timestamps(self) -> None:
        import src.models  # noqa: F401

        for table_name, table in Base.metadata.tables.items():
            with self.subTest(table=table_name):
                self.assertIn("created_at", table.c)
                self.assertFalse(table.c.created_at.nullable)

                if table_name not in {
                    "roles_permissions",
                    "document_chunks",
                    "document_embeddings",
                    "audit_log",
                }:
                    self.assertIn("updated_at", table.c)
                    self.assertFalse(table.c.updated_at.nullable)

    def test_uuid_primary_keys_are_configured(self) -> None:
        import src.models  # noqa: F401

        for table_name, table in Base.metadata.tables.items():
            with self.subTest(table=table_name):
                primary_key = inspect(table).primary_key
                self.assertEqual(1, len(primary_key.columns))
                self.assertEqual("id", next(iter(primary_key.columns)).name)

    def test_expected_indexes_exist(self) -> None:
        import src.models  # noqa: F401

        expected_indexes = {
            "idx_users_org_email",
            "idx_users_org_role",
            "idx_roles_permissions_unique",
            "idx_clients_org_name",
            "idx_clients_org_document",
            "idx_case_parties_org_case",
            "idx_case_parties_org_document",
            "idx_cases_org_status",
            "idx_cases_org_client",
            "idx_cases_org_type",
            "idx_documents_org_case",
            "idx_documents_org_status",
            "idx_documents_org_conversion_status",
            "idx_external_queries_cache_unique",
            "idx_audit_log_org_created",
            "idx_agent_executions_job_id",
            "idx_agent_executions_org_case",
            "idx_agent_executions_org_status",
            "idx_document_chunks_org_case",
            "idx_document_chunks_document",
            "idx_document_embeddings_org_case",
            "idx_document_embeddings_vector",
            "idx_human_reviews_org_status",
            "idx_reports_org_case",
            "idx_reports_org_status",
        }
        actual_indexes = {
            index.name
            for table in Base.metadata.tables.values()
            for index in table.indexes
        }

        self.assertTrue(expected_indexes.issubset(actual_indexes))

    def test_basic_foreign_keys_exist(self) -> None:
        import src.models  # noqa: F401

        expected_foreign_keys = {
            "users": {"organizations"},
            "roles_permissions": {"organizations"},
            "clients": {"organizations", "users"},
            "case_parties": {"organizations", "cases"},
            "cases": {"organizations", "clients", "users"},
            "documents": {"organizations", "cases", "users"},
            "external_queries_cache": {"organizations", "cases", "users"},
            "audit_log": {"organizations", "users"},
            "agent_executions": {"organizations", "cases", "documents"},
            "document_chunks": {"organizations", "documents", "cases"},
            "document_embeddings": {
                "organizations",
                "documents",
                "cases",
                "document_chunks",
            },
            "human_reviews": {"organizations", "cases", "reports", "users"},
            "reports": {"organizations", "cases", "users"},
        }

        for table_name, referenced_tables in expected_foreign_keys.items():
            with self.subTest(table=table_name):
                table = Base.metadata.tables[table_name]
                actual_references = {
                    foreign_key.column.table.name
                    for foreign_key in table.foreign_keys
                }
                self.assertTrue(referenced_tables.issubset(actual_references))


class AlembicConfigTest(unittest.TestCase):
    def test_alembic_files_exist(self) -> None:
        api_root = Path(__file__).resolve().parents[1]

        self.assertTrue((api_root / "alembic.ini").is_file())
        self.assertTrue((api_root / "alembic" / "env.py").is_file())
        self.assertTrue((api_root / "alembic" / "script.py.mako").is_file())
        self.assertTrue((api_root / "alembic" / "versions").is_dir())
        self.assertTrue(
            (api_root / "alembic" / "versions" / "0002_remaining_mvp_models.py").is_file()
        )
        self.assertTrue(
            (
                api_root
                / "alembic"
                / "versions"
                / "0003_doc_md_norm.py"
            ).is_file()
        )

    def test_document_normalization_columns_exist(self) -> None:
        import src.models  # noqa: F401

        documents = Base.metadata.tables["documents"]
        for column_name in {
            "conversion_status",
            "normalized_markdown_storage_key",
            "normalized_markdown_sha256",
            "normalized_markdown_size_bytes",
            "conversion_error_summary",
            "converted_at",
        }:
            with self.subTest(column=column_name):
                self.assertIn(column_name, documents.c)


if __name__ == "__main__":
    unittest.main()
