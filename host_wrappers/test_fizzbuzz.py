import unittest

from fizzbuzz import fizzbuzz


class FizzBuzzTests(unittest.TestCase):
    def test_first_entries(self):
        """Verify the sequence begins correctly."""
        expected = ["1", "2", "Fizz", "4", "Buzz", "Fizz", "7", "8", "Fizz", "Buzz"]
        self.assertEqual(fizzbuzz(limit=10), expected)

    def test_multiples_of_three_and_five(self):
        """Numbers divisible by 3 and 5 become FizzBuzz."""
        sequence = fizzbuzz(limit=30)
        self.assertEqual(sequence[14], "FizzBuzz")  # 15
        self.assertEqual(sequence[29], "FizzBuzz")  # 30

    def test_limit_length_and_terminal_value(self):
        """Sequence length matches limit and ends with the correct value."""
        result = fizzbuzz(limit=7)
        self.assertEqual(len(result), 7)
        self.assertEqual(result[-1], "7")


if __name__ == "__main__":
    unittest.main()
