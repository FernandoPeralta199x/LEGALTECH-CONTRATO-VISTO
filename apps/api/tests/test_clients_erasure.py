import unittest
from uuid import uuid4

from src.models.client import Client
from src.modules.clients.repository import ClientRepository
from src.modules.clients.service import ClientService
from src.modules.common.exceptions import ResourceNotFoundError


class _FakeSession:
    def flush(self) -> None:
        return None

    def refresh(self, _obj) -> None:
        return None


class AnonymizeClientRepositoryTest(unittest.TestCase):
    def test_anonymize_client_scrubs_all_pii_and_marks_deleted(self) -> None:
        organization_id = uuid4()
        client = Client(
            organization_id=organization_id,
            name="Maria da Silva",
            document="12345678900",
            email="maria@example.com",
            phone="+5511999998888",
            metadata_json={"cpf": "12345678900", "full_name": "Maria da Silva"},
        )
        client.id = uuid4()

        result = ClientRepository(_FakeSession()).anonymize_client(client)

        self.assertEqual("[anonimizado]", result.name)
        self.assertIsNone(result.document)
        self.assertIsNone(result.email)
        self.assertIsNone(result.phone)
        self.assertEqual({}, result.metadata_json)
        self.assertIsNotNone(result.deleted_at)
        self.assertEqual(organization_id, result.organization_id)
        self.assertIsNotNone(result.id)


class _FakeRepository:
    def __init__(self, client) -> None:
        self._client = client
        self.anonymized = None

    def get_client(self, *, organization_id, client_id):
        return self._client

    def anonymize_client(self, client):
        self.anonymized = client
        return client


class _MissingRepository:
    def get_client(self, *, organization_id, client_id):
        return None


class EraseClientServiceTest(unittest.TestCase):
    def test_erase_client_delegates_to_repository_anonymize(self) -> None:
        client = Client(
            organization_id=uuid4(),
            name="Joao",
            document="98765432100",
            email="joao@example.com",
            phone="+5511888887777",
            metadata_json={},
        )
        client.id = uuid4()
        repository = _FakeRepository(client)
        service = ClientService(repository=repository)

        result = service.erase_client(organization_id=uuid4(), client_id=client.id)

        self.assertIs(client, result)
        self.assertIs(client, repository.anonymized)

    def test_erase_client_raises_not_found_for_missing_client(self) -> None:
        service = ClientService(repository=_MissingRepository())

        with self.assertRaises(ResourceNotFoundError):
            service.erase_client(organization_id=uuid4(), client_id=uuid4())


if __name__ == "__main__":
    unittest.main()
