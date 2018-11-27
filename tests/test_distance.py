import unittest

from app import distance


class TestDistance(unittest.TestCase):
    def test_classic_levensthein(self):
        self.assertEqual(distance.classic_levenshtein('', ''), 0)
        self.assertEqual(distance.classic_levenshtein('psa', 'pies'), 3)
        self.assertEqual(distance.classic_levenshtein('granit', 'granat'), 1)
