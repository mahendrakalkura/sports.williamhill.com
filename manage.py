from datetime import datetime
from json import loads
from pprint import pprint
from re import compile
from sys import argv
from traceback import print_exc

from pytz import timezone, utc
from requests import request
from websocket import WebSocketApp

PATTERN = compile(r'document\.aip_list\.create_prebuilt_event\((.*?)\);')


def trace(function):
    def wrap(*args, **kwargs):
        try:
            return function(*args, **kwargs)
        except Exception:
            print_exc()
            raise
    return wrap


class WebSockets():

    URL = 'wss://scoreboards-ssl.williamhill.com/diffusion?v=4&ty=WB'

    DELIMITERS_MESSAGE = '\x00'
    DELIMITERS_RECORD = '\x01'
    DELIMITERS_FIELD = '\x02'

    TYPES_CLIENT_ID = '4'
    TYPES_TOPIC_LOAD_MESSAGE = '\x14'
    TYPES_DELTA_MESSAGE = '\x15'
    TYPES_SUBSCRIBE = '\x16'
    TYPES_PING_CLIENT = '\x19'

    TOPICS = [
        'sportsbook/football/{id:d}/animation',
        'sportsbook/football/{id:d}/i18n/en-gb/commentary',
        'sportsbook/football/{id:d}/stats/away',
        'sportsbook/football/{id:d}/stats/away/cards/red',
        'sportsbook/football/{id:d}/stats/away/cards/yellow',
        'sportsbook/football/{id:d}/stats/away/corners',
        'sportsbook/football/{id:d}/stats/away/freeKicks',
        'sportsbook/football/{id:d}/stats/away/goals',
        'sportsbook/football/{id:d}/stats/away/lineup',
        'sportsbook/football/{id:d}/stats/away/penalties',
        'sportsbook/football/{id:d}/stats/away/shots/offTarget',
        'sportsbook/football/{id:d}/stats/away/shots/onTarget',
        'sportsbook/football/{id:d}/stats/away/shots/onWoodwork',
        'sportsbook/football/{id:d}/stats/away/substitutions',
        'sportsbook/football/{id:d}/stats/away/throwIns',
        'sportsbook/football/{id:d}/stats/home',
        'sportsbook/football/{id:d}/stats/home/cards/red',
        'sportsbook/football/{id:d}/stats/home/cards/yellow',
        'sportsbook/football/{id:d}/stats/home/corners',
        'sportsbook/football/{id:d}/stats/home/freeKicks',
        'sportsbook/football/{id:d}/stats/home/goals',
        'sportsbook/football/{id:d}/stats/home/lineup',
        'sportsbook/football/{id:d}/stats/home/penalties',
        'sportsbook/football/{id:d}/stats/home/shots/offTarget',
        'sportsbook/football/{id:d}/stats/home/shots/onTarget',
        'sportsbook/football/{id:d}/stats/home/shots/onWoodwork',
        'sportsbook/football/{id:d}/stats/home/substitutions',
        'sportsbook/football/{id:d}/stats/home/throwIns',
        'sportsbook/football/{id:d}/stats/homeTeamPossesion',
        'sportsbook/football/{id:d}/stats/mode',
        'sportsbook/football/{id:d}/stats/period',
        'sportsbook/football/{id:d}/stats/score',
        'sportsbook/football/{id:d}/stats/time',
    ]

    @trace
    def __init__(self, match):
        self.match = match
        self.dictionary = {
            'client_id': None,
            'topics': {},
        }

    @trace
    def connect(self):
        self.connection = WebSocketApp(
            self.URL,
            on_open=self.on_open,
            on_close=self.on_close,
            on_message=self.on_message,
            on_error=self.on_error,
        )

    @trace
    def on_open(self, _):
        self.log('Open', None)

    @trace
    def on_close(self, _):
        self.log('Close', None)

    @trace
    def on_message(self, _, message):
        message = bytearray(message, 'utf-8')
        if chr(message[0]) == self.TYPES_CLIENT_ID:
            self.process_client_id(message)
            return
        if chr(message[0]) == self.TYPES_TOPIC_LOAD_MESSAGE:
            self.process_topic_load_message(message)
            return
        if chr(message[0]) == self.TYPES_DELTA_MESSAGE:
            self.process_delta_message(message)
            return
        if chr(message[0]) == self.TYPES_PING_CLIENT:
            self.process_ping_client(message)
            return
        self.log('Unknown', message)

    @trace
    def process_client_id(self, message):
        message = message.split(b'\x02')
        client_id = message[2]
        client_id = client_id.decode('utf-8')
        self.dictionary['client_id'] = client_id
        self.log('Client ID', self.dictionary['client_id'])
        for topic in self.TOPICS:
            self.dictionary[topic] = None
            message = topic
            message = message.format(id=self.match['id'])
            type = self.TYPES_SUBSCRIBE
            headers = [message]
            data = None
            self.send(type, headers, data)

    @trace
    def process_topic_load_message(self, message):
        message = message[1:]
        message = message.split(b'\x01')
        message[0] = message[0].decode('utf-8')
        message[0] = message[0].split('!')
        self.dictionary['topics'][message[0][0]] = message[0][1]
        message[1] = message[1].split(b'\x01')
        self.log('Topic Load Message', message[0][0])
        if message[0][0].endswith('/animation'):
            return
        if message[0][0].endswith('/i18n/en-gb/commentary'):
            return
        if message[0][0].endswith('/stats/away'):
            return
        if message[0][0].endswith('/stats/away/cards/red'):
            return
        if message[0][0].endswith('/stats/away/cards/yellow'):
            return
        if message[0][0].endswith('/stats/away/corners'):
            return
        if message[0][0].endswith('/stats/away/freeKicks'):
            return
        if message[0][0].endswith('/stats/away/goals'):
            return
        if message[0][0].endswith('/stats/away/lineup'):
            return
        if message[0][0].endswith('/stats/away/penalties'):
            return
        if message[0][0].endswith('/stats/away/shots/offTarget'):
            return
        if message[0][0].endswith('/stats/away/shots/onTarget'):
            return
        if message[0][0].endswith('/stats/away/shots/onWoodwork'):
            return
        if message[0][0].endswith('/stats/away/substitutions'):
            return
        if message[0][0].endswith('/stats/away/throwIns'):
            return
        if message[0][0].endswith('/stats/home'):
            return
        if message[0][0].endswith('/stats/home/cards/red'):
            return
        if message[0][0].endswith('/stats/home/cards/yellow'):
            return
        if message[0][0].endswith('/stats/home/corners'):
            return
        if message[0][0].endswith('/stats/home/freeKicks'):
            return
        if message[0][0].endswith('/stats/home/goals'):
            return
        if message[0][0].endswith('/stats/home/lineup'):
            return
        if message[0][0].endswith('/stats/home/penalties'):
            return
        if message[0][0].endswith('/stats/home/shots/offTarget'):
            return
        if message[0][0].endswith('/stats/home/shots/onTarget'):
            return
        if message[0][0].endswith('/stats/home/shots/onWoodwork'):
            return
        if message[0][0].endswith('/stats/home/substitutions'):
            return
        if message[0][0].endswith('/stats/home/throwIns'):
            return
        if message[0][0].endswith('/stats/homeTeamPossesion'):
            return
        if message[0][0].endswith('/stats/mode'):
            return
        if message[0][0].endswith('/stats/period'):
            return
        if message[0][0].endswith('/stats/score'):
            return
        if message[0][0].endswith('/stats/time'):
            return

    @trace
    def process_delta_message(self, message):
        message = message[1:]
        message = message.split(b'\x01')
        message[0] = message[0].split(b'\x02')
        message[0][0] = message[0][0].decode('utf-8')
        for key, value in self.dictionary['topics'].items():
            if message[0][0][1:] != value:
                continue
            self.log('Delta Message', key)
            if key.endswith('/animation'):
                return
            if key.endswith('/i18n/en-gb/commentary'):
                return
            if key.endswith('/stats/away'):
                return
            if key.endswith('/stats/away/cards/red'):
                return
            if key.endswith('/stats/away/cards/yellow'):
                return
            if key.endswith('/stats/away/corners'):
                return
            if key.endswith('/stats/away/freeKicks'):
                return
            if key.endswith('/stats/away/goals'):
                return
            if key.endswith('/stats/away/lineup'):
                return
            if key.endswith('/stats/away/penalties'):
                return
            if key.endswith('/stats/away/shots/offTarget'):
                return
            if key.endswith('/stats/away/shots/onTarget'):
                return
            if key.endswith('/stats/away/shots/onWoodwork'):
                return
            if key.endswith('/stats/away/substitutions'):
                return
            if key.endswith('/stats/away/throwIns'):
                return
            if key.endswith('/stats/home'):
                return
            if key.endswith('/stats/home/cards/red'):
                return
            if key.endswith('/stats/home/cards/yellow'):
                return
            if key.endswith('/stats/home/corners'):
                return
            if key.endswith('/stats/home/freeKicks'):
                return
            if key.endswith('/stats/home/goals'):
                return
            if key.endswith('/stats/home/lineup'):
                return
            if key.endswith('/stats/home/penalties'):
                return
            if key.endswith('/stats/home/shots/offTarget'):
                return
            if key.endswith('/stats/home/shots/onTarget'):
                return
            if key.endswith('/stats/home/shots/onWoodwork'):
                return
            if key.endswith('/stats/home/substitutions'):
                return
            if key.endswith('/stats/home/throwIns'):
                return
            if key.endswith('/stats/homeTeamPossesion'):
                return
            if key.endswith('/stats/mode'):
                return
            if key.endswith('/stats/period'):
                return
            if key.endswith('/stats/score'):
                return
            if key.endswith('/stats/time'):
                return
        pprint(self.dictionary['topics'])
        self.log('Delta Message (unknown)', message)

    @trace
    def process_ping_client(self, message):
        message = message[1:]
        message = message.split(b'\x01')
        timestamp = message[0]
        timestamp = timestamp.decode('utf-8')
        type = self.TYPES_PING_CLIENT
        headers = [timestamp]
        data = None
        self.send(type, headers, data)

    @trace
    def process_topic_status_notification(self, message):
        message = message[1:]
        message = message.split(b'\x01')
        message = map(lambda item: item.decode('utf-8'), message)
        message = list(message)
        self.log('Topic Status Notification', message)

    @trace
    def on_error(self, _, error):
        self.log('Error', error)

    @trace
    def run_forever(self):
        self.connection.run_forever()

    @trace
    def send(self, type, headers, data):
        headers = self.get_headers(headers)
        message = []
        message.append(type)
        message.append(headers)
        if data:
            message.append(data)
        message = ''.join(message)
        message = bytearray(message, 'utf-8')
        self.connection.send(message)

    @trace
    def get_headers(self, headers):
        items = []
        for header in headers:
            i = []
            i.append(header)
            i.append(self.DELIMITERS_RECORD)
            i = ''.join(i)
            items.append(i)
        length = len(items)
        if length == 1:
            items = items[0]
            return items
        items = self.DELIMITERS_FIELD.join(items)
        return items

    @trace
    def log(self, prefix, suffix):
        if prefix and suffix:
            prefix = prefix.ljust(25, ' ')
            suffix = repr(suffix)
            suffix = suffix[0:75]
            print('[+]', prefix, ':', suffix)
            return
        if prefix:
            print('[+]', prefix)
            return


@trace
def main(options):
    if options[1] == '--matches':
        execute_matches()
        return
    if options[1] == '--web-sockets':
        execute_web_sockets(options[2])
        return


@trace
def execute_matches():
    matches = process_matches()
    pprint(matches)


@trace
def process_matches():
    matches = []
    url = 'http://sports.williamhill.com/bet/en-gb/betlive/9'
    response = request(method='GET', url=url)
    if not response:
        return matches
    contents = response.text
    contents = contents.replace('\n', '')
    items = PATTERN.findall(contents)
    for item in items:
        item = loads(item)
        id = item['event']
        id = int(id)
        teams = {
            'home': None,
            'away': None,
        }
        for selection in item['selections']:
            if selection['fb_result'] == 'H':
                teams['home'] = selection['name']
            if selection['fb_result'] == 'A':
                teams['away'] = selection['name']
        date = get_date(item['start_time'])
        match = {
            'id': id,
            'teams': teams,
            'date': date,
        }
        if match['id'] and match['teams']['home'] and match['teams']['away'] and match['date']:
            matches.append(match)
    return matches


@trace
def get_date(date):
    date = datetime.strptime(date, '%Y-%m-%d %H:%M:%S')
    bst = timezone('Europe/London')
    date = bst.localize(date)
    date = date.astimezone(utc)
    date = date.replace(tzinfo=None)
    return date


@trace
def execute_web_sockets(id):
    id = int(id)
    match = {
        'id': id,
    }
    web_sockets = WebSockets(match)
    web_sockets.connect()
    web_sockets.run_forever()


if __name__ == '__main__':
    main(argv)
