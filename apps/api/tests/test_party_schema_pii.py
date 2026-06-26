import unittest
from datetime import UTC, datetime
from uuid import uuid4

from src.modules.contracts.schemas import PartySchema


class PartySchemaPiiTest(unittest.TestCase):
    def test_masks_pii_and_excludes_raw(self):
        p = PartySchema(
            id=uuid4(), case_id=uuid4(), organization_id=uuid4(),
            name="Parte", role="contratante",
            document="12345678901", email="parte@example.test", phone="+5511999998888",
            created_at=datetime.now(UTC), updated_at=datetime.now(UTC),
        )
        self.assertEqual("123****01", p.document_masked)
        self.assertNotEqual("12345678901", p.document_masked)
        self.assertIn("@example.test", p.email_masked)
        self.assertTrue(p.phone_masked.startswith("("))
        dumped = p.model_dump(mode="json")
        self.assertNotIn("document", dumped)
        self.assertNotIn("email", dumped)
        self.assertNotIn("phone", dumped)


if __name__ == "__main__":
    unittest.main()
