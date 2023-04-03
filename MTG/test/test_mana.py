import unittest
from collections import defaultdict
from MTG import Mana, str_to_mana_dict, chr_to_mana, ManaPool

class TestManaFunctions(unittest.TestCase):

    def test_str_to_mana_dict_valid(self):
        """Test str_to_mana_dict with valid mana cost strings."""
        self.assertEqual(str_to_mana_dict("2WU"), {Mana.WHITE: 1, Mana.BLUE: 1, Mana.GENERIC: 2})
        self.assertEqual(str_to_mana_dict("XU"), {Mana.BLUE: 1, Mana.GENERIC: 0})

    def test_str_to_mana_dict_invalid(self):
        """Test str_to_mana_dict with invalid or empty mana cost strings."""
        self.assertEqual(str_to_mana_dict(""), defaultdict(lambda: 0))
        self.assertEqual(str_to_mana_dict("Invalid"), defaultdict(lambda: 0))

    def test_str_to_mana_dict_hybrid(self):
        """Test str_to_mana_dict with hybrid mana costs."""
        self.assertEqual(str_to_mana_dict("(W/U)"), {Mana.WHITE: 1, Mana.BLUE: 1})

    def test_chr_to_mana_valid(self):
        """Test chr_to_mana with valid mana characters."""
        self.assertEqual(chr_to_mana("W"), Mana.WHITE)
        self.assertEqual(chr_to_mana("U"), Mana.BLUE)
        self.assertEqual(chr_to_mana("B"), Mana.BLACK)
        self.assertEqual(chr_to_mana("R"), Mana.RED)
        self.assertEqual(chr_to_mana("G"), Mana.GREEN)
        self.assertEqual(chr_to_mana("C"), Mana.COLORLESS)
        self.assertEqual(chr_to_mana("1"), Mana.GENERIC)

    def test_chr_to_mana_invalid(self):
        """Test chr_to_mana with invalid or empty mana characters."""
        with self.assertRaises(AssertionError):
            chr_to_mana("")
        with self.assertRaises(AssertionError):
            chr_to_mana("Invalid")

class TestManaPool(unittest.TestCase):

    def setUp(self):
        self.manapool = ManaPool()

    def test_init(self):
        """Test ManaPool __init__ method."""
        self.assertIsInstance(self.manapool.pool, defaultdict)
        self.assertIsNone(self.manapool.controller)

    def test_add_valid(self):
        """Test ManaPool add method with valid mana and amount inputs."""
        self.manapool.add("W", 1)
        self.assertEqual(self.manapool.pool[Mana.WHITE], 1)

    def test_add_invalid(self):
        """Test ManaPool add method with invalid or empty mana and amount inputs."""
        with self.assertRaises(AssertionError):
            self.manapool.add("", 1)
        with self.assertRaises(AssertionError):
            self.manapool.add("Invalid", 1)

    def test_pay_valid(self):
        """Test ManaPool pay method with valid mana costs."""
        self.manapool.add("W", 1)
        self.manapool.pay({Mana.WHITE: 1})
        self.assertEqual(self.manapool.pool[Mana.WHITE], 0)

    def test_pay_invalid(self):
        """Test ManaPool pay method with invalid or empty mana costs."""
        with self.assertRaises(AssertionError):
            self.manapool.pay({Mana.WHITE: 1})

    def test_is_empty(self):
        """Test ManaPool is_empty method for empty and non-empty mana pools."""
        self.assertTrue(self.manapool.is_empty())
        self.manapool.add("W", 1)
        self.assertFalse(self.manapool.is_empty())

    def test_clear(self):
        """Test ManaPool clear method for emptying the mana pool."""
        self.manapool.add("W", 1)
        self.manapool.clear()
        self.assertTrue(self.manapool.is_empty())

    def test_determine_costs_valid(self):
        """Test ManaPool determine_costs method with various mana cost strings, including hybrid and generic mana costs."""
        self.assertEqual(self.manapool.determine_costs("2WU"), {Mana.WHITE: 1, Mana.BLUE: 1, Mana.GENERIC: 2})
        self.assertEqual(self.manapool.determine_costs("(W/U)"), {Mana.WHITE: 1, Mana.BLUE: 1})

    def test_canPay_valid(self):
        """Test ManaPool canPay method for various mana cost strings and pool configurations."""
        self.manapool.add("W", 1)
        self.manapool.add("U", 1)
        self.manapool.add("B", 2)
        self.assertFalse(self.manapool.canPay("2WU"))
        self.assertTrue(self.manapool.canPay("WU"))
        self.assertTrue(self.manapool.canPay("WUB"))

    def test_canPay_invalid(self):
        """Test ManaPool canPay method for invalid or empty mana cost strings."""
        self.assertTrue(self.manapool.canPay(""))
        self.assertFalse(self.manapool.canPay("Invalid"))

if __name__ == '__main__':
    unittest.main()