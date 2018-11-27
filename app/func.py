import logging
from queue import PriorityQueue
from collections import namedtuple, Iterable

from app import distance as distance
from app.exception import HomeConfigValidationError, NoMatchError

log = logging.getLogger(__name__)


class Sentence:
    WeightedWord = namedtuple('WeightedWord', ['weight', 'word_sentence', 'word'])

    def __init__(self, sentence):
        self.sentence = [word.lower() for word in sentence.split()]

    def search(self, words, distance_function=None, max_difference=0.7):
        """
        Searches sentence for any word from words list.
        :param iterable[str] words: iterable of words to look for
        :return: list of best matching words, empty list if no word is matching at all
        """
        assert isinstance(words, Iterable), 'words must be type of Iterable[str]'

        # if no distance function was given, simply check for exact containment
        if not distance_function:
            return [word for word in words if word in self.sentence]
        else:
            best_results = PriorityQueue()

            for word in words:
                weighted_words = PriorityQueue()

                for word_sentence in self.sentence:
                    # for every word in a sentence, calculate how similar it is to word from input list
                    dist = distance_function(word, word_sentence)

                    # store results in a priority queue
                    weighted_words.put(self.WeightedWord(dist, word_sentence, word))

                for w in self._get_best(weighted_words, max_difference):
                    best_results.put(w)

            return [w.word for w in self._get_best(best_results)]

    def _get_best(self, in_queue, max_difference=None):
        previous_weight = None

        while not in_queue.empty():
            # pick up best, most similar word
            w_word = in_queue.get()

            # if previous weight is better than current, then break a loop - collecting only N best elements
            if previous_weight is not None and w_word.weight > previous_weight:
                break

            previous_weight = w_word.weight

            if max_difference:
                # ensure than word satisfies max difference condition
                # if it does, then remember that word
                # if it does not, then break - further elements will have worse weight
                # collect up to N best words with same best weight M
                if w_word.weight / len(w_word.word) <= max_difference:
                    yield w_word
                else:
                    break
            else:
                yield w_word


class Home:
    def __init__(self, home):
        self._rooms = self.get(home, 'rooms')
        self._functionality = self._prepare_functionality(home)
        self.home = self._prepare_home()

    @property
    def rooms(self):
        return list(self.home.keys())

    def devices(self, room):
        return list(self.home[room].keys())

    def keywords(self, room, device):
        return list(self.home[room][device].keys())

    def construct_command(self, room, device, keyword):
        return ''.join([
            self.home[room]['_id'],
            self.home[room][device]['_id'],
            self.home[room][device][keyword]
        ])

    def _prepare_functionality(self, home):
        funcs = {}

        for func_id, func in self.get(home, 'functionality').items():
            if func_id in funcs:
                raise HomeConfigValidationError(f'Duplicated functionality id: {func_id} - id must be unique!')

            cmds = {}

            for cmd in self.get(func, 'commands'):
                cmd_value = self.get(self.get(cmd, 'cmd'), 'value')

                cmds.update({
                    keyword: cmd_value for keyword in self.get(cmd, 'keywords')
                })

            funcs[func_id] = cmds

        return funcs

    def _prepare_home(self):
        rooms = {}

        for room in self._rooms:
            room_name, room_id = self.get(room, 'name'), self.get(room, 'id')

            if room_name in rooms:
                raise HomeConfigValidationError(f'Duplicated room name: {room_name} - name should be unique for entire'
                                                f'house!')

            devices = {}

            for device in self.get(room, 'devices'):
                device_name, device_id = self.get(device, 'name'), self.get(device, 'id')

                if device_name in devices:
                    raise HomeConfigValidationError(f'Duplicated device name: {device_name} - name should be unique'
                                                    f'for each room!')

                keywords = {}

                for func in self.get(device, 'functionality'):
                    if func not in self._functionality:
                        raise HomeConfigValidationError(f'Functionality "{func}" in room "{room_name}" for device '
                                                        f'"{device_name}" is not defined!')

                    keywords.update(self._functionality[func])

                # append new device
                devices[device_name] = {'_id': device_id, **keywords}

            # append new room
            rooms[room_name] = {'_id': room_id, **devices}

        return rooms

    def get(self, dictionary, key):
        try:
            return dictionary[key]
        except KeyError:
            raise HomeConfigValidationError(f'No required property: {key} in: {dictionary}')


def parse(sentence, home, metric='classic', max_difference=0.6):
    """
    Parses sentence and translates it into machine readable command.

    :param str sentence: sentence to parse
    :param dict home: description of a home
    :param float or int max_difference: number representing variance of a key
    :param str metric: name of a function used for difference calculation
    :return: machine readable command based on ``home`` config
    :rtype: str
    """
    # import distance function
    try:
        distance_function = getattr(distance, f'{metric}_levenshtein')
    except AttributeError:
        all_metrics = [func[:func.index('_')] for func in distance.__all__]
        raise ValueError(f'Unsupported metric {metric}. Supported metrics: {all_metrics}')

    h = Home(home)
    s = Sentence(sentence)
    args = {
        'max_difference': max_difference,
        'distance_function': distance_function
    }

    room_names = s.search(h.rooms, **args)
    if not room_names:
        raise NoMatchError(f'Could not match any room (available rooms: {h.rooms})')
    room_name = room_names[0]

    device_names = s.search(h.devices(room_name), **args)
    if not device_names:
        raise NoMatchError(f'Could not match any device (available devices: {h.devices(room_name)}) '
                           f'for a room: ({room_name})')
    device_name = device_names[0]

    keywords = s.search(h.keywords(room_name, device_name), **args)
    if not keywords:
        raise NoMatchError(f'Could not match any keyword (available keywords: {h.keywords(room_name, device_name)}) '
                           f'for a device ({device_name}) in a room: ({room_name})')
    keyword = keywords[0]

    return h.construct_command(room_name, device_name, keyword)
