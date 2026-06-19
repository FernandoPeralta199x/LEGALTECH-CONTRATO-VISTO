import unittest
from types import SimpleNamespace
from uuid import uuid4

from pydantic import ValidationError
from sqlalchemy.dialects import postgresql


def compile_sql(statement) -> str:
    return str(
        statement.compile(
            dialect=postgresql.dialect(),
            compile_kwargs={"literal_binds": False},
        )
    )


class FakeScalarResult:
    def __init__(self, values=None) -> None:
        self.values = values or []

    def all(self):
        return self.values

    def first(self):
        return self.values[0] if self.values else None


class FakeSession:
    def __init__(self, scalars_result=None) -> None:
        self.scalars_result = FakeScalarResult(scalars_result)
        self.statements = []
        self.added = []
        self.flushed = False
        self.refreshed = []

    def scalars(self, statement):
        self.statements.append(statement)
        return self.scalars_result

    def add(self, instance) -> None:
        self.added.append(instance)

    def flush(self) -> None:
        self.flushed = True

    def refresh(self, instance) -> None:
        self.refreshed.append(instance)


class SchemasTest(unittest.TestCase):
    def test_client_create_rejects_tenant_supplied_by_payload(self) -> None:
        from src.modules.clients.schemas import ClientCreate

        with self.assertRaises(ValidationError):
            ClientCreate.model_validate(
                {
                    "name": "Cliente Teste",
                    "organization_id": str(uuid4()),
                }
            )

    def test_client_create_validates_person_type_required_fields(self) -> None:
        from src.modules.clients.schemas import ClientCreate

        with self.assertRaises(ValidationError):
            ClientCreate.model_validate(
                {
                    "person_type": "individual",
                    "contract_role": "contractor",
                }
            )

        with self.assertRaises(ValidationError):
            ClientCreate.model_validate(
                {
                    "person_type": "company",
                    "contract_role": "contractor",
                }
            )

        with self.assertRaises(ValidationError):
            ClientCreate.model_validate(
                {
                    "person_type": "individual",
                    "full_name": "Cliente Teste",
                }
            )

    def test_case_create_rejects_tenant_and_creator_supplied_by_payload(self) -> None:
        from src.modules.cases.schemas import CaseCreate

        with self.assertRaises(ValidationError):
            CaseCreate.model_validate(
                {
                    "client_id": str(uuid4()),
                    "case_type": "contract_analysis",
                    "organization_id": str(uuid4()),
                    "created_by": str(uuid4()),
                }
            )


class ClientRepositoryTest(unittest.TestCase):
    def test_list_clients_always_filters_by_organization_and_not_deleted(self) -> None:
        from src.modules.clients.repository import ClientRepository

        session = FakeSession()
        organization_id = uuid4()

        ClientRepository(session).list_clients(
            organization_id=organization_id,
            search="empresa",
            page=2,
            page_size=10,
        )

        sql = compile_sql(session.statements[0])
        self.assertIn("clients.organization_id", sql)
        self.assertIn("clients.deleted_at IS NULL", sql)
        self.assertIn("ILIKE", sql)
        self.assertIn("LIMIT", sql)
        self.assertIn("OFFSET", sql)

    def test_get_client_always_filters_by_organization_and_not_deleted(self) -> None:
        from src.modules.clients.repository import ClientRepository

        session = FakeSession()

        ClientRepository(session).get_client(
            organization_id=uuid4(),
            client_id=uuid4(),
        )

        sql = compile_sql(session.statements[0])
        self.assertIn("clients.id", sql)
        self.assertIn("clients.organization_id", sql)
        self.assertIn("clients.deleted_at IS NULL", sql)


class CaseRepositoryTest(unittest.TestCase):
    def test_list_cases_always_filters_by_organization_not_deleted_and_filters(self) -> None:
        from src.modules.cases.repository import CaseRepository

        session = FakeSession()

        CaseRepository(session).list_cases(
            organization_id=uuid4(),
            status="draft",
            case_type="contract_analysis",
            client_id=uuid4(),
            page=1,
            page_size=25,
        )

        sql = compile_sql(session.statements[0])
        self.assertIn("cases.organization_id", sql)
        self.assertIn("cases.deleted_at IS NULL", sql)
        self.assertIn("cases.status", sql)
        self.assertIn("cases.case_type", sql)
        self.assertIn("cases.client_id", sql)


class ClientServiceTest(unittest.TestCase):
    def test_create_client_uses_tenant_and_user_from_service_arguments(self) -> None:
        from src.modules.clients.schemas import ClientCreate
        from src.modules.clients.service import ClientService

        class Repository:
            def __init__(self) -> None:
                self.created = None

            def create_client(self, client):
                self.created = client
                return client

        organization_id = uuid4()
        user_id = uuid4()
        repository = Repository()
        service = ClientService(repository=repository)

        service.create_client(
            organization_id=organization_id,
            user_id=user_id,
            payload=ClientCreate(
                contract_role="contractor",
                cpf="000.000.000-00",
                full_name="Cliente Teste",
                metadata={"origin": "unit-test"},
                name="Cliente Teste",
                person_type="individual",
            ),
        )

        self.assertEqual(organization_id, repository.created.organization_id)
        self.assertEqual(user_id, repository.created.created_by)
        self.assertEqual("Cliente Teste", repository.created.name)
        self.assertEqual("000.000.000-00", repository.created.document)
        self.assertEqual("unit-test", repository.created.metadata_json["origin"])
        self.assertEqual("individual", repository.created.metadata_json["person_type"])
        self.assertEqual("contractor", repository.created.metadata_json["contract_role"])

    def test_update_client_clears_incompatible_person_type_metadata(self) -> None:
        from src.modules.clients.schemas import ClientUpdate
        from src.modules.clients.service import ClientService

        class Repository:
            def __init__(self) -> None:
                self.client = SimpleNamespace(
                    id=uuid4(),
                    metadata_json={
                        "contract_role": "contractor",
                        "cpf": "123.456.789-01",
                        "document_type": "cpf",
                        "display_name": "Cliente PF",
                        "full_name": "Cliente PF",
                        "person_type": "individual",
                        "rg": "12.345.678-9",
                    },
                )
                self.updated_values = None

            def get_client(self, *, organization_id, client_id):
                return self.client

            def update_client(self, client, values):
                self.updated_values = values
                for field, value in values.items():
                    setattr(client, field, value)
                return client

        repository = Repository()
        service = ClientService(repository=repository)

        service.update_client(
            organization_id=uuid4(),
            client_id=repository.client.id,
            payload=ClientUpdate(
                cnpj="12.345.678/0001-99",
                contract_role="contracted",
                document="12.345.678/0001-99",
                document_type="cnpj",
                legal_name="Empresa Atualizada Ltda",
                name="Empresa Atualizada Ltda",
                person_type="company",
            ),
        )

        metadata = repository.updated_values["metadata_json"]
        self.assertEqual("company", metadata["person_type"])
        self.assertEqual("cnpj", metadata["document_type"])
        self.assertEqual("12.345.678/0001-99", metadata["cnpj"])
        self.assertEqual("Empresa Atualizada Ltda", metadata["display_name"])
        self.assertNotIn("cpf", metadata)
        self.assertNotIn("rg", metadata)
        self.assertNotIn("full_name", metadata)

    def test_update_client_name_refreshes_metadata_display_name(self) -> None:
        from src.modules.clients.schemas import ClientUpdate
        from src.modules.clients.service import ClientService

        class Repository:
            def __init__(self) -> None:
                self.client = SimpleNamespace(
                    id=uuid4(),
                    metadata_json={
                        "contract_role": "contractor",
                        "display_name": "Cliente Original",
                        "person_type": "individual",
                    },
                )
                self.updated_values = None

            def get_client(self, *, organization_id, client_id):
                return self.client

            def update_client(self, client, values):
                self.updated_values = values
                for field, value in values.items():
                    setattr(client, field, value)
                return client

        repository = Repository()
        service = ClientService(repository=repository)

        service.update_client(
            organization_id=uuid4(),
            client_id=repository.client.id,
            payload=ClientUpdate(name="Cliente Atualizado"),
        )

        self.assertEqual("Cliente Atualizado", repository.updated_values["name"])
        self.assertEqual(
            "Cliente Atualizado",
            repository.updated_values["metadata_json"]["display_name"],
        )


class CaseServiceTest(unittest.TestCase):
    def test_create_case_requires_client_from_same_organization(self) -> None:
        from src.modules.cases.schemas import CaseCreate
        from src.modules.cases.service import CaseService
        from src.modules.common.exceptions import ResourceNotFoundError

        class CaseRepository:
            def create_case(self, case):
                return case

        class ClientRepository:
            def get_client(self, *, organization_id, client_id):
                return None

        service = CaseService(
            repository=CaseRepository(),
            client_repository=ClientRepository(),
        )

        with self.assertRaises(ResourceNotFoundError):
            service.create_case(
                organization_id=uuid4(),
                user_id=uuid4(),
                payload=CaseCreate(
                    client_id=uuid4(),
                    case_type="contract_analysis",
                ),
            )

    def test_create_case_uses_tenant_and_user_from_service_arguments(self) -> None:
        from src.modules.cases.schemas import CaseCreate
        from src.modules.cases.service import CaseService

        class CaseRepository:
            def __init__(self) -> None:
                self.created = None

            def create_case(self, case):
                self.created = case
                return case

        class ClientRepository:
            def get_client(self, *, organization_id, client_id):
                return object()

        organization_id = uuid4()
        user_id = uuid4()
        case_repository = CaseRepository()
        service = CaseService(
            repository=case_repository,
            client_repository=ClientRepository(),
        )

        service.create_case(
            organization_id=organization_id,
            user_id=user_id,
            payload=CaseCreate(
                client_id=uuid4(),
                case_type="contract_analysis",
                priority="normal",
                metadata={"product": "analise_contratual"},
            ),
        )

        self.assertEqual(organization_id, case_repository.created.organization_id)
        self.assertEqual(user_id, case_repository.created.created_by)
        self.assertEqual(
            {"product": "analise_contratual"},
            case_repository.created.metadata_json,
        )


if __name__ == "__main__":
    unittest.main()
