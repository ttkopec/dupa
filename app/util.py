import json


def load_home(file_path):
    """
    Reads home json config file.

    :param str file_path: file path to json config file
    :return: dictionary representing home
    :rtype: dict
    """
    with open(file_path, 'r') as fp:
        return json.load(fp)
