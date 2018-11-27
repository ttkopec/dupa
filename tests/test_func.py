import unittest
from functools import partial

from app.func import Home, Sentence, parse
from app.util import load_home
from app.distance import classic_levenshtein
from app.exception import HomeConfigValidationError, NoMatchError

from tests.fixtures import HOME, SIMPLE_HOME


class TestHomeConfigValidationErrors(unittest.TestCase):
    def setUp(self):
        self.home_dict = load_home(SIMPLE_HOME)

    def test_duplicated_room(self):
        self.home_dict['rooms'].append({"name": "Bedroom", "id": "bedroom"})

        with self.assertRaises(HomeConfigValidationError, msg='should raise error on duplicate room name') as e:
            Home(self.home_dict)

        msg = str(e.exception)
        self.assertTrue(msg.startswith('Duplicated room name'),
                        'exception should start with "Duplicated room name": {}.'.format(msg))

    def test_duplicated_functionality(self):
        pass

    def test_duplicated_device(self):
        pass

    def test_functionality_no_defined(self):
        pass

    def test_required_properties(self):
        pass


class TestSentence(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.s = Sentence('ala has cat')

    def test_search_without_distance(self):
        self.assertEqual(self.s.search(['ala']), ['ala'], msg='should return exact match')
        self.assertEqual(self.s.search(['whatever']), [], msg='should return no match')
        self.assertEqual(self.s.search([None]), [], msg='should return no match')

        with self.assertRaises(AssertionError, msg='should fail when non iterable argument is passed'):
            self.s.search(None)

    def test_search_with_distance(self):
        self.assertEqual(self.s.search(['ala123', 'ala', 'ala1', 'ala12'], classic_levenshtein), ['ala'])
        self.assertEqual(self.s.search(['whatever'], classic_levenshtein), [])

        self.assertEqual(self.s.search(['ala1'], classic_levenshtein), ['ala1'])
        self.assertEqual(self.s.search(['ala1', '1ala'], classic_levenshtein), ['1ala', 'ala1'],
                         msg='should return two equal matches')


class TestParse(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.home_dict = load_home(HOME)
        super().setUpClass()

    def test_happy_case(self):
        self.assertEqual(parse('Zapal oświetlenie górne w sypialni', self.home_dict, metric='wf'), 'B1on')
        self.assertEqual(parse('Załączyć lampe w sypialni', self.home_dict, metric='wf'), 'B4on')
        self.assertEqual(parse('Wyłączyc kuchanke w kuchni', self.home_dict, metric='wf'), 'C99off')

        # TODO add more cases

    def test_no_match_errors(self):
        self._assert_raises(partial(parse, 'Włącz lampe w lesie', self.home_dict, 'wf'), 'should not match room',
                            'Could not match any room')
        self._assert_raises(partial(parse, 'Włącz drewno w sypialni', self.home_dict, 'wf'), 'should not match device',
                            'Could not match any device')
        self._assert_raises(partial(parse, 'Odpalaj_szybciutko lampe w sypialni', self.home_dict, 'wf'),
                            'should not match keyword',
                            'Could not match any keyword')

    def _assert_raises(self, func, msg, expected_exc_msg=None):
        with self.assertRaises(NoMatchError, msg=msg) as e:
            func()

        if expected_exc_msg:
            self.assertTrue(str(e.exception).startswith(expected_exc_msg), f'exception should start with: {expected_exc_msg}')
