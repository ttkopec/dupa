import unittest
from json import JSONDecodeError

from app.util import load_home

from tests.fixtures import INVALID_JSON, SIMPLE_HOME


class TestUtil(unittest.TestCase):
    def test_load_home(self):
        with self.assertRaises(FileNotFoundError, msg='should raise error for non existing file'):
            load_home('non existing file_path')

        with self.assertRaises(JSONDecodeError, msg='should raise error for invalid json'):
            load_home(INVALID_JSON)

        self.assertDictEqual(load_home(SIMPLE_HOME),
                             {'functionality': {'on_off': {'commands': [{'cmd': {'value': 'on'},
                                                                         'keywords': ['turn on']}]}},
                              'rooms': [{'id': 'A',
                                         'name': 'Bedroom',
                                         'devices': [{'id': '1', 'name': 'Lamp', 'functionality': ['on_off']}]}]},
                             'should load simple dict')
