from datetime import datetime
from json import loads
from math import floor
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
        #     'sportsbook/football/{id:d}/animation',
        #     'sportsbook/football/{id:d}/i18n/en-gb/commentary',
        'sportsbook/football/{id:d}/stats/away/cards/red',
        'sportsbook/football/{id:d}/stats/away/cards/yellow',
        'sportsbook/football/{id:d}/stats/away/corners',
        'sportsbook/football/{id:d}/stats/away/freeKicks',
        'sportsbook/football/{id:d}/stats/away/goals',
        #     'sportsbook/football/{id:d}/stats/away/lineup',
        'sportsbook/football/{id:d}/stats/away/penalties',
        #     'sportsbook/football/{id:d}/stats/away/shots/offTarget',
        #     'sportsbook/football/{id:d}/stats/away/shots/onTarget',
        #     'sportsbook/football/{id:d}/stats/away/shots/onWoodwork',
        #     'sportsbook/football/{id:d}/stats/away/substitutions',
        #     'sportsbook/football/{id:d}/stats/away/throwIns',
        'sportsbook/football/{id:d}/stats/home/cards/red',
        'sportsbook/football/{id:d}/stats/home/cards/yellow',
        'sportsbook/football/{id:d}/stats/home/corners',
        'sportsbook/football/{id:d}/stats/home/freeKicks',
        'sportsbook/football/{id:d}/stats/home/goals',
        #     'sportsbook/football/{id:d}/stats/home/lineup',
        'sportsbook/football/{id:d}/stats/home/penalties',
        #     'sportsbook/football/{id:d}/stats/home/shots/offTarget',
        #     'sportsbook/football/{id:d}/stats/home/shots/onTarget',
        #     'sportsbook/football/{id:d}/stats/home/shots/onWoodwork',
        #     'sportsbook/football/{id:d}/stats/home/substitutions',
        #     'sportsbook/football/{id:d}/stats/home/throwIns',
        'sportsbook/football/{id:d}/stats/homeTeamPossesion',
        'sportsbook/football/{id:d}/stats/period',
        'sportsbook/football/{id:d}/stats/time',
    ]

    @trace
    def __init__(self, id):
        self.id = id
        self.client_id = None
        self.topics = {}
        self.status = {
            'period': None,
            'minute': 0,
        }
        self.events = {}

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
    def run_forever(self):
        self.connection.run_forever()

    @trace
    def on_open(self, _):
        self.log('Open', None)

    @trace
    def on_close(self, _):
        self.log('Close', None)

    @trace
    def on_message(self, _, message):
        message = bytearray(message, 'utf-8')
        type = message[0]
        type = chr(type)
        payload = message[1:]
        payload = self.decode(payload)
        if type == self.TYPES_CLIENT_ID:
            self.process_client_id(payload)
            return
        if type == self.TYPES_TOPIC_LOAD_MESSAGE:
            self.process_topic_load_message(payload)
            return
        if type == self.TYPES_DELTA_MESSAGE:
            self.process_delta_message(payload)
            return
        if type == self.TYPES_PING_CLIENT:
            self.process_ping_client(payload)
            return

    @trace
    def on_error(self, _, error):
        self.log('Error', error)

    @trace
    def process_client_id(self, payload):
        client_id = payload[0][1]
        self.client_id = client_id
        self.log('Client ID', self.client_id)
        for topic in self.TOPICS:
            message = topic
            message = message.format(id=self.id)
            type = self.TYPES_SUBSCRIBE
            headers = [message]
            data = None
            self.send(type, headers, data)

    @trace
    def process_topic_load_message(self, payload):
        payload[0][0] = payload[0][0].split('!')
        self.topics[payload[0][0][1]] = payload[0][0][0]
        payload[0][0] = payload[0][0][0]
        self.process_payload(payload)

    @trace
    def process_delta_message(self, payload):
        payload[0][0] = payload[0][0][1:]
        payload[0][0] = self.get_topic(payload[0][0])
        if not payload[0][0]:
            return
        self.process_payload(payload)

    @trace
    def process_ping_client(self, payload):
        timestamp = payload[0][0]
        type = self.TYPES_PING_CLIENT
        headers = [timestamp]
        data = None
        self.send(type, headers, data)

    @trace
    def process_payload(self, payload):
        if payload[0][0].endswith('/animation'):
            # TODO
            return
        if payload[0][0].endswith('/i18n/en-gb/commentary'):
            # TODO
            return
        if payload[0][0].endswith('/stats/away/cards/red'):
            for item in payload[1:]:
                minute = item[1]
                minute = self.get_minute(minute)
                event = {
                    'team': 'away',
                    'player': None,
                    'minute': minute,
                    'coordinates': None,
                    'description': 'redCard',
                    'type': None,
                    'percentage': None,
                    'timestamp': datetime.utcnow(),
                    '_dispatch_match_event': True,
                }
                uuid = self.get_uuid(event)
                self.events[uuid] = event
            count = self.get_count('away', 'redCard')
            self.log('/stats/away/cards/red', count)
            return
        if payload[0][0].endswith('/stats/away/cards/yellow'):
            for item in payload[1:]:
                minute = item[1]
                minute = self.get_minute(minute)
                event = {
                    'team': 'away',
                    'player': None,
                    'minute': minute,
                    'coordinates': None,
                    'description': 'yellowCard',
                    'type': None,
                    'percentage': None,
                    'timestamp': datetime.utcnow(),
                    '_dispatch_match_event': True,
                }
                uuid = self.get_uuid(event)
                self.events[uuid] = event
            count = self.get_count('away', 'yellowCard')
            self.log('/stats/away/cards/yellow', count)
            return
        if payload[0][0].endswith('/stats/away/corners'):
            for item in payload[1:]:
                minute = item[1]
                minute = self.get_minute(minute)
                event = {
                    'team': 'away',
                    'player': None,
                    'minute': minute,
                    'coordinates': None,
                    'description': 'corner',
                    'type': None,
                    'percentage': None,
                    'timestamp': datetime.utcnow(),
                    '_dispatch_match_event': True,
                }
                uuid = self.get_uuid(event)
                self.events[uuid] = event
            count = self.get_count('away', 'corner')
            self.log('/stats/away/corners', count)
            return
        if payload[0][0].endswith('/stats/away/freeKicks'):
            for item in payload[1:]:
                minute = item[1]
                minute = self.get_minute(minute)
                event = {
                    'team': 'away',
                    'player': None,
                    'minute': minute,
                    'coordinates': None,
                    'description': 'dfreekick',
                    'type': None,
                    'percentage': None,
                    'timestamp': datetime.utcnow(),
                    '_dispatch_match_event': True,
                }
                uuid = self.get_uuid(event)
                self.events[uuid] = event
            count = self.get_count('away', 'dfreekick')
            self.log('/stats/away/freeKicks', count)
            return
        if payload[0][0].endswith('/stats/away/goals'):
            for item in payload[1:]:
                minute = item[1]
                minute = self.get_minute(minute)
                event = {
                    'team': 'away',
                    'player': None,
                    'minute': minute,
                    'coordinates': None,
                    'description': 'goal',
                    'type': 'G',
                    'percentage': None,
                    'timestamp': datetime.utcnow(),
                    '_dispatch_match_event': True,
                }
                uuid = self.get_uuid(event)
                self.events[uuid] = event
            count = self.get_count('away', 'goal')
            self.log('/stats/away/goals', count)
            return
        if payload[0][0].endswith('/stats/away/lineup'):
            # TODO
            print(repr(payload))
            return
        if payload[0][0].endswith('/stats/away/penalties'):
            for item in payload[1:]:
                minute = item[1]
                minute = self.get_minute(minute)
                event = {
                    'team': 'away',
                    'player': None,
                    'minute': minute,
                    'coordinates': None,
                    'description': 'penalty',
                    'type': 'P',
                    'percentage': None,
                    'timestamp': datetime.utcnow(),
                    '_dispatch_match_event': True,
                }
                uuid = self.get_uuid(event)
                self.events[uuid] = event
            count = self.get_count('away', 'penalty')
            self.log('/stats/away/penalties', count)
            return
        if payload[0][0].endswith('/stats/away/shots/offTarget'):
            # TODO
            return
        if payload[0][0].endswith('/stats/away/shots/onTarget'):
            # TODO
            return
        if payload[0][0].endswith('/stats/away/shots/onWoodwork'):
            # TODO
            return
        if payload[0][0].endswith('/stats/away/substitutions'):
            # TODO
            print(repr(payload))
            return
        if payload[0][0].endswith('/stats/away/throwIns'):
            # TODO
            print(repr(payload))
            return
        if payload[0][0].endswith('/stats/home/cards/red'):
            for item in payload[1:]:
                minute = item[1]
                minute = self.get_minute(minute)
                event = {
                    'team': 'home',
                    'player': None,
                    'minute': minute,
                    'coordinates': None,
                    'description': 'redCard',
                    'type': None,
                    'percentage': None,
                    'timestamp': datetime.utcnow(),
                    '_dispatch_match_event': True,
                }
                uuid = self.get_uuid(event)
                self.events[uuid] = event
            count = self.get_count('home', 'redCard')
            self.log('/stats/home/cards/red', count)
            return
        if payload[0][0].endswith('/stats/home/cards/yellow'):
            for item in payload[1:]:
                minute = item[1]
                minute = self.get_minute(minute)
                event = {
                    'team': 'home',
                    'player': None,
                    'minute': minute,
                    'coordinates': None,
                    'description': 'yellowCard',
                    'type': None,
                    'percentage': None,
                    'timestamp': datetime.utcnow(),
                    '_dispatch_match_event': True,
                }
                uuid = self.get_uuid(event)
                self.events[uuid] = event
            count = self.get_count('home', 'yellowCard')
            self.log('/stats/home/cards/yellow', count)
            return
        if payload[0][0].endswith('/stats/home/corners'):
            for item in payload[1:]:
                minute = item[1]
                minute = self.get_minute(minute)
                event = {
                    'team': 'home',
                    'player': None,
                    'minute': minute,
                    'coordinates': None,
                    'description': 'corner',
                    'type': None,
                    'percentage': None,
                    'timestamp': datetime.utcnow(),
                    '_dispatch_match_event': True,
                }
                uuid = self.get_uuid(event)
                self.events[uuid] = event
            count = self.get_count('home', 'corner')
            self.log('/stats/home/corners', count)
            return
        if payload[0][0].endswith('/stats/home/freeKicks'):
            for item in payload[1:]:
                minute = item[1]
                minute = self.get_minute(minute)
                event = {
                    'team': 'home',
                    'player': None,
                    'minute': minute,
                    'coordinates': None,
                    'description': 'dfreekick',
                    'type': None,
                    'percentage': None,
                    'timestamp': datetime.utcnow(),
                    '_dispatch_match_event': True,
                }
                uuid = self.get_uuid(event)
                self.events[uuid] = event
            count = self.get_count('home', 'dfreekick')
            self.log('/stats/home/freeKicks', count)
            return
        if payload[0][0].endswith('/stats/home/goals'):
            for item in payload[1:]:
                minute = item[1]
                minute = self.get_minute(minute)
                event = {
                    'team': 'home',
                    'player': None,
                    'minute': minute,
                    'coordinates': None,
                    'description': 'goal',
                    'type': 'G',
                    'percentage': None,
                    'timestamp': datetime.utcnow(),
                    '_dispatch_match_event': True,
                }
                uuid = self.get_uuid(event)
                self.events[uuid] = event
            count = self.get_count('home', 'goal')
            self.log('/stats/home/goals', count)
            return
        if payload[0][0].endswith('/stats/home/lineup'):
            # TODO
            print(repr(payload))
            return
        if payload[0][0].endswith('/stats/home/penalties'):
            for item in payload[1:]:
                minute = item[1]
                minute = self.get_minute(minute)
                event = {
                    'team': 'home',
                    'player': None,
                    'minute': minute,
                    'coordinates': None,
                    'description': 'penalty',
                    'type': 'P',
                    'percentage': None,
                    'timestamp': datetime.utcnow(),
                    '_dispatch_match_event': True,
                }
                uuid = self.get_uuid(event)
                self.events[uuid] = event
            count = self.get_count('home', 'penalty')
            self.log('/stats/home/penalties', count)
            return
        if payload[0][0].endswith('/stats/home/shots/offTarget'):
            # TODO
            print(repr(payload))
            return
        if payload[0][0].endswith('/stats/home/shots/onTarget'):
            # TODO
            print(repr(payload))
            return
        if payload[0][0].endswith('/stats/home/shots/onWoodwork'):
            # TODO
            print(repr(payload))
            return
        if payload[0][0].endswith('/stats/home/substitutions'):
            # TODO
            print(repr(payload))
            return
        if payload[0][0].endswith('/stats/home/throwIns'):
            # TODO
            print(repr(payload))
            return
        if payload[0][0].endswith('/stats/homeTeamPossesion'):
            possession = payload[1][0]
            home, away = self.get_possession(possession)
            event = {
                'team': 'home',
                'player': None,
                'minute': None,
                'coordinates': None,
                'description': 'possession',
                'type': None,
                'percentage': home,
                'timestamp': datetime.utcnow(),
                '_dispatch_match_event': True,
            }
            uuid = self.get_uuid(event)
            self.events[uuid] = event
            event = {
                'team': 'away',
                'player': None,
                'minute': None,
                'coordinates': None,
                'description': 'possession',
                'type': None,
                'percentage': away,
                'timestamp': datetime.utcnow(),
                '_dispatch_match_event': True,
            }
            uuid = self.get_uuid(event)
            self.events[uuid] = event
            self.log('/stats/homeTeamPossesion', [home, away])
            return
        if payload[0][0].endswith('/stats/period'):
            period = payload[1][0]
            period = self.get_status_period(period)
            self.status['period'] = period
            self.log('/stats/period', self.status)
            return
        if payload[0][0].endswith('/stats/time'):
            minute = payload[1][0]
            minute = self.get_minute(minute)
            self.status['minute'] = minute
            self.log('/stats/time', self.status)
            return

    @trace
    def decode(self, payload):
        payload = payload.split(bytes(self.DELIMITERS_RECORD, 'utf-8'))
        payload = map(lambda item: item.split(bytes(self.DELIMITERS_FIELD, 'utf-8')), payload)
        payload = [map(lambda item: item.decode('utf-8'), p) for p in payload]
        payload = [filter(None, p) for p in payload]
        payload = [list(p) for p in payload]
        payload = filter(None, payload)
        payload = list(payload)
        return payload

    @trace
    def log(self, prefix, suffix):
        if prefix and suffix:
            prefix = prefix.ljust(28, ' ')
            suffix = repr(suffix)
            print('[+]', prefix, ':', suffix)
            return
        if prefix:
            print('[+]', prefix)
            return

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
    def get_count(self, team, description):
        count = 0
        for key, value in self.events.items():
            if value['team'] == team and value['description'] == description:
                count = count + 1
        return count

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
    def get_possession(self, possession):
        home = possession
        home = int(home)
        away = 100 - home
        return home, away

    @trace
    def get_minute(self, minute):
        minute = int(minute)
        minute = (minute * 1.0) / 60.0
        minute = floor(minute)
        minute = int(minute)
        return minute

    @trace
    def get_status_period(self, period):
        if period == 'H1':
            return '1st half'
        if period == 'HT':
            return 'halftime'
        if period == 'H2':
            return '2nd half'
        if period == 'FT':
            return '2nd half'
        if period == 'ETNS':
            return '2nd half'
        if period == 'ETH1':
            return '2nd half'
        if period == 'ETHT':
            return '2nd half'
        if period == 'ETH2':
            return '2nd half'
        if period == 'ETFT':
            return '2nd half'
        if period == 'PNS':
            return '2nd half'
        return 'ended'

    @trace
    def get_topic(self, payload):
        if payload in self.topics:
            return self.topics[payload]
        return None

    @trace
    def get_uuid(self, event):
        del event['_dispatch_match_event']
        del event['percentage']
        del event['timestamp']
        items = event.items()
        items = sorted(items)
        items = tuple(items)
        uuid = hash(items)
        return uuid


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
def execute_web_sockets(id):
    id = int(id)
    web_sockets = WebSockets(id)
    web_sockets.connect()
    web_sockets.run_forever()


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


if __name__ == '__main__':
    main(argv)
