import unittest

from src.modules.common.pii import mask_email


class MaskEmailTest(unittest.TestCase):
    def test_masks_local_part_keeping_first_char_and_domain(self) -> None:
        self.assertEqual("f*******@example.com", mask_email("fernando@example.com"))

    def test_single_char_local_is_fully_masked(self) -> None:
        self.assertEqual("*@b.com", mask_email("a@b.com"))

    def test_none_or_invalid_is_redacted(self) -> None:
        self.assertEqual("<redacted>", mask_email(None))
        self.assertEqual("<redacted>", mask_email("notanemail"))
        self.assertEqual("<redacted>", mask_email(""))


if __name__ == "__main__":
    unittest.main()
