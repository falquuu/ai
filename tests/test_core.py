import unittest

from perfect_numbers.core import (
    MAX_END, MAX_SPAN, RangeError, analyze, divisor_sum, find_perfect_numbers,
    is_perfect, validate_range,
)


class TestCore(unittest.TestCase):
    def test_known_perfect_numbers(self):
        self.assertEqual(find_perfect_numbers(1, 10000), [6, 28, 496, 8128])

    def test_fifth_perfect_number(self):
        self.assertEqual(find_perfect_numbers(33550000, 33551000), [33550336])

    def test_single_number_range(self):
        self.assertEqual(find_perfect_numbers(28, 28), [28])
        self.assertEqual(find_perfect_numbers(27, 27), [])

    def test_one_is_not_perfect(self):
        self.assertEqual(find_perfect_numbers(1, 5), [])
        self.assertFalse(is_perfect(1))

    def test_no_perfect_in_range(self):
        self.assertEqual(find_perfect_numbers(29, 495), [])

    def test_boundaries_inclusive(self):
        self.assertEqual(find_perfect_numbers(6, 28), [6, 28])

    def test_range_not_starting_from_one_matches_bruteforce(self):
        for a, b in [(2, 50), (7, 7), (500, 9000), (1000, 1999)]:
            self.assertEqual(find_perfect_numbers(a, b),
                             [n for n in range(a, b + 1) if is_perfect(n)])

    def test_divisor_sum(self):
        self.assertEqual(divisor_sum(1), 0)
        self.assertEqual(divisor_sum(12), 16)  # 1+2+3+4+6
        self.assertEqual(divisor_sum(36), 55)  # квадрат: 1+2+3+4+6+9+12+18

    def test_analyze_structure(self):
        self.assertEqual(analyze(1, 100),
                         {"start": 1, "end": 100, "count": 2, "numbers": [6, 28]})

    def test_invalid_ranges(self):
        for start, end in [(0, 10), (-5, 10), (10, 1), (1, MAX_END + 1),
                           (1, MAX_SPAN + 1)]:
            with self.subTest(start=start, end=end):
                with self.assertRaises(RangeError):
                    validate_range(start, end)

    def test_non_integer_bounds(self):
        for start, end in [(1.5, 10), (1, "10"), (True, 10)]:
            with self.assertRaises(RangeError):
                validate_range(start, end)

    def test_max_span_allowed(self):
        self.assertEqual(validate_range(1, MAX_SPAN), (1, MAX_SPAN))


if __name__ == "__main__":
    unittest.main()
