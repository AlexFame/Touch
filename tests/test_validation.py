import unittest

from app.validation import normalize_contact, normalize_name, valid_contact, valid_name


class ValidationTests(unittest.TestCase):
    def test_name_accepts_human_names_and_normalizes_spaces(self):
        self.assertEqual(normalize_name("  Андрій   Павлов  "), "Андрій Павлов")
        self.assertTrue(valid_name("Alexey"))
        self.assertTrue(valid_name("Олексій Павлов"))
        self.assertTrue(valid_name("Anne-Marie"))

    def test_name_rejects_links_digits_and_garbage(self):
        self.assertFalse(valid_name("Alexey123"))
        self.assertFalse(valid_name("https://spam.example"))
        self.assertFalse(valid_name("t.me/spam"))
        self.assertFalse(valid_name("🐾🐾🐾"))

    def test_contact_accepts_empty_username_and_phone(self):
        self.assertTrue(valid_contact(""))
        self.assertTrue(valid_contact(None))
        self.assertTrue(valid_contact("@iam_fvme"))
        self.assertTrue(valid_contact("+49 162 2589015"))
        self.assertTrue(valid_contact("iam_fvme"))
        self.assertEqual(normalize_contact("iam_fvme"), "@iam_fvme")

    def test_contact_rejects_links_short_usernames_and_bad_phone(self):
        self.assertFalse(valid_contact("https://example.com"))
        self.assertFalse(valid_contact("t.me/someone"))
        self.assertFalse(valid_contact("@abc"))
        self.assertFalse(valid_contact("+49 abc"))
