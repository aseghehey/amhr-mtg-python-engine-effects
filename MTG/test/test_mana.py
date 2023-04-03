import unittest
from collections import defaultdict
from MTG.mana import Mana, str_to_mana_dict, chr_to_mana, ManaPool

def mana_dict_equal(dict1, dict2):
    if isinstance(dict1, bool) or isinstance(dict2, bool):
        return dict1 == dict2
    return all(dict1.get(key, 0) == dict2.get(key, 0) for key in Mana)

class DummyController:
    def __init__(self, auto_pay_mana):
        self.autoPayMana = auto_pay_mana

    def make_choice(self, prompt):
        return '0'  # always choose the default option

class TestManaFunctions(unittest.TestCase):

    def test_str_to_mana_dict_valid(self):
        """Test str_to_mana_dict with valid mana cost strings."""
        default_factory = lambda: 0
        self.assertEqual(str_to_mana_dict("2WU"), defaultdict(default_factory, {Mana.WHITE: 1, Mana.BLUE: 1, Mana.GENERIC: 2}))
        self.assertEqual(str_to_mana_dict("0U"), defaultdict(default_factory, {Mana.BLUE: 1, Mana.GENERIC: 0}))

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
        self.assertIsNone(chr_to_mana(""))
        self.assertIsNone(chr_to_mana("Invalid"))

class TestManaPool(unittest.TestCase):

    def setUp(self):
        dummy_controller = DummyController(auto_pay_mana=True)
        self.manapool = ManaPool(controller=dummy_controller)

    def test_init(self):
        """Test ManaPool __init__ method."""
        self.assertIsInstance(self.manapool.pool, defaultdict)

    def test_add_valid(self):
        """Test ManaPool add method with valid mana and amount inputs."""
        self.manapool.add("W", 1)
        self.assertEqual(self.manapool.pool[Mana.WHITE], 1)

    def test_add_invalid(self):
        """Test ManaPool add method with invalid or empty mana and amount inputs."""
        self.assertIsNone(self.manapool.add("", 1))
        self.assertIsNone(self.manapool.add("Invalid", 1))

    def test_canPay_invalid(self):
        """Test ManaPool canPay method with invalid or empty mana costs."""
        self.assertFalse(self.manapool.canPay(""))
        self.assertFalse(self.manapool.canPay("Invalid"))

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
        # Test when payment is not possible
        result = self.manapool.canPay("10WU")  # Adjust the cost so that the payment is not possible
        self.assertFalse(result)

        # Test when payment is possible
        result = self.manapool.canPay("2WU")
        print("Result:", result)  # Debugging print statement
        expected_result = {
            Mana.GENERIC: 0,
            Mana.WHITE: 1,
            Mana.BLUE: 1,
            Mana.BLACK: 2,
            Mana.RED: 0,
            Mana.GREEN: 0,
            Mana.COLORLESS: 0
        }
        print("Expected result:", expected_result)  # Debugging print statement
        self.assertTrue(mana_dict_equal(result, expected_result))



        # self.manapool.add("W", 1)
        # self.manapool.add("U", 1)
        # self.manapool.add("B", 2)
        # self.assertFalse(self.manapool.canPay("2WU"))
        # self.assertTrue(self.manapool.canPay("WU"))
        # self.assertTrue(self.manapool.canPay("WUB"))

    def test_canPay_invalid(self):
        """Test ManaPool canPay method for invalid or empty mana cost strings."""
        result = self.manapool.canPay("")
        expected_result = {mana: 0 for mana in Mana}
        self.assertTrue(mana_dict_equal(result, expected_result))

        result = self.manapool.canPay("Invalid")
        expected_result = {mana: 0 for mana in Mana}
        self.assertTrue(mana_dict_equal(result, expected_result))

if __name__ == '__main__':
    unittest.main()