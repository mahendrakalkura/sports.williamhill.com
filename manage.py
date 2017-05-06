from datetime import datetime
from json import loads
from math import floor
from pprint import pprint
from re import compile
from sys import argv
from threading import Thread
from time import time
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
        'sportsbook/football/{id:d}/i18n/en-gb/commentary',
        'sportsbook/football/{id:d}/stats/away/cards/red',
        'sportsbook/football/{id:d}/stats/away/cards/yellow',
        'sportsbook/football/{id:d}/stats/away/corners',
        'sportsbook/football/{id:d}/stats/away/freeKicks',
        'sportsbook/football/{id:d}/stats/away/goals',
        'sportsbook/football/{id:d}/stats/away/penalties',
        'sportsbook/football/{id:d}/stats/away/shots/offTarget',
        'sportsbook/football/{id:d}/stats/away/shots/onTarget',
        'sportsbook/football/{id:d}/stats/away/shots/onWoodwork',
        'sportsbook/football/{id:d}/stats/away/substitutions',
        'sportsbook/football/{id:d}/stats/away/throwIns',
        'sportsbook/football/{id:d}/stats/home/cards/red',
        'sportsbook/football/{id:d}/stats/home/cards/yellow',
        'sportsbook/football/{id:d}/stats/home/corners',
        'sportsbook/football/{id:d}/stats/home/freeKicks',
        'sportsbook/football/{id:d}/stats/home/goals',
        'sportsbook/football/{id:d}/stats/home/penalties',
        'sportsbook/football/{id:d}/stats/home/shots/offTarget',
        'sportsbook/football/{id:d}/stats/home/shots/onTarget',
        'sportsbook/football/{id:d}/stats/home/shots/onWoodwork',
        'sportsbook/football/{id:d}/stats/home/substitutions',
        'sportsbook/football/{id:d}/stats/home/throwIns',
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
    def open(self):
        self.connection = WebSocketApp(
            self.URL,
            on_open=self.on_open,
            on_close=self.on_close,
            on_message=self.on_message,
            on_error=self.on_error,
        )
        while True:
            try:
                self.connection.run_forever()
            except KeyboardInterrupt:
                break
            except Exception:
                pass

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
        if payload[0][0].endswith('/i18n/en-gb/commentary'):
            for item in payload[1:]:
                if len(item) != 6:
                    continue
                if item[4] == 'AWAY_ATTACK':
                    seconds = item[3]
                    coordinates = self.get_coordinates(item[5])
                    event = {
                        'team': 'away',
                        'player': None,
                        'seconds': seconds,
                        'coordinates': coordinates,
                        'description': 'attack',
                        'type': None,
                        'percentage': None,
                        'timestamp': self.get_timestamp(),
                        '_dispatch_match_event': True,
                    }
                    id = self.get_id(event)
                    self.events[id] = event
                    self.log('/i18n/en-gb/commentary', [event['team'], event['seconds'], event['description']])
                    continue
                if item[4] == 'AWAY_DANGER':
                    seconds = item[3]
                    coordinates = self.get_coordinates(item[5])
                    event = {
                        'team': 'away',
                        'player': None,
                        'seconds': seconds,
                        'coordinates': coordinates,
                        'description': 'danger',
                        'type': None,
                        'percentage': None,
                        'timestamp': self.get_timestamp(),
                        '_dispatch_match_event': True,
                    }
                    id = self.get_id(event)
                    self.events[id] = event
                    self.log('/i18n/en-gb/commentary', [event['team'], event['seconds'], event['description']])
                    continue
                if item[4] == 'AWAY_SAFE':
                    seconds = item[3]
                    coordinates = self.get_coordinates(item[5])
                    event = {
                        'team': 'away',
                        'player': None,
                        'seconds': seconds,
                        'coordinates': coordinates,
                        'description': 'safe',
                        'type': None,
                        'percentage': None,
                        'timestamp': self.get_timestamp(),
                        '_dispatch_match_event': True,
                    }
                    id = self.get_id(event)
                    self.events[id] = event
                    self.log('/i18n/en-gb/commentary', [event['team'], event['seconds'], event['description']])
                    continue
                if item[4] == 'BALL_SAFE':
                    seconds = item[3]
                    coordinates = self.get_coordinates(item[5])
                    if not coordinates:
                        continue
                    event = {
                        'team': None,
                        'player': None,
                        'seconds': seconds,
                        'coordinates': coordinates,
                        'description': None,
                        'type': None,
                        'percentage': None,
                        'timestamp': self.get_timestamp(),
                        '_dispatch_match_event': True,
                    }
                    id = self.get_id(event)
                    self.events[id] = event
                    self.log('/i18n/en-gb/commentary', [event['team'], event['seconds'], event['description']])
                    continue
                if item[4] == 'CORNER_AWAY':
                    seconds = item[3]
                    coordinates = self.get_coordinates(item[5])
                    event = {
                        'team': 'away',
                        'player': None,
                        'seconds': seconds,
                        'coordinates': coordinates,
                        'description': 'corner',
                        'type': None,
                        'percentage': None,
                        'timestamp': self.get_timestamp(),
                        '_dispatch_match_event': True,
                    }
                    id = self.get_id(event)
                    self.events[id] = event
                    self.log('/i18n/en-gb/commentary', [event['team'], event['seconds'], event['description']])
                    continue
                if item[4] == 'CORNER_HOME':
                    seconds = item[3]
                    coordinates = self.get_coordinates(item[5])
                    event = {
                        'team': 'home',
                        'player': None,
                        'seconds': seconds,
                        'coordinates': coordinates,
                        'description': 'corner',
                        'type': None,
                        'percentage': None,
                        'timestamp': self.get_timestamp(),
                        '_dispatch_match_event': True,
                    }
                    id = self.get_id(event)
                    self.events[id] = event
                    self.log('/i18n/en-gb/commentary', [event['team'], event['seconds'], event['description']])
                    continue
                if item[4] == 'FIRST_HALF':
                    continue
                if item[4] == 'FREE_KICK_AWAY':
                    seconds = item[3]
                    coordinates = self.get_coordinates(item[5])
                    if not coordinates:
                        continue
                    if coordinates[1] < 0.5:
                        description = 'dfreekick'
                    else:
                        description = 'sfreekick'
                    event = {
                        'team': 'away',
                        'player': None,
                        'seconds': seconds,
                        'coordinates': coordinates,
                        'description': description,
                        'type': None,
                        'percentage': None,
                        'timestamp': self.get_timestamp(),
                        '_dispatch_match_event': True,
                    }
                    id = self.get_id(event)
                    self.events[id] = event
                    self.log('/i18n/en-gb/commentary', [event['team'], event['seconds'], event['description']])
                    continue
                if item[4] == 'FREE_KICK_HOME':
                    seconds = item[3]
                    coordinates = self.get_coordinates(item[5])
                    if not coordinates:
                        continue
                    if coordinates[1] < 0.5:
                        description = 'sfreekick'
                    else:
                        description = 'dfreekick'
                    event = {
                        'team': 'home',
                        'player': None,
                        'seconds': seconds,
                        'coordinates': coordinates,
                        'description': description,
                        'type': None,
                        'percentage': None,
                        'timestamp': self.get_timestamp(),
                        '_dispatch_match_event': True,
                    }
                    id = self.get_id(event)
                    self.events[id] = event
                    self.log('/i18n/en-gb/commentary', [event['team'], event['seconds'], event['description']])
                    continue
                if item[4] == 'FREE_TEXT':
                    continue
                if item[4] == 'GAME_STARTING_SOON':
                    continue
                if item[4] == 'GOAL_AWAY':
                    continue
                if item[4] == 'GOAL_HOME':
                    continue
                if item[4] == 'GOAL_KICK_AWAY':
                    seconds = item[3]
                    coordinates = self.get_coordinates(item[5])
                    event = {
                        'team': 'away',
                        'player': None,
                        'seconds': seconds,
                        'coordinates': coordinates,
                        'description': 'goalkick',
                        'type': None,
                        'percentage': None,
                        'timestamp': self.get_timestamp(),
                        '_dispatch_match_event': True,
                    }
                    id = self.get_id(event)
                    self.events[id] = event
                    self.log('/i18n/en-gb/commentary', [event['team'], event['seconds'], event['description']])
                    continue
                if item[4] == 'GOAL_KICK_HOME':
                    seconds = item[3]
                    coordinates = self.get_coordinates(item[5])
                    event = {
                        'team': 'home',
                        'player': None,
                        'seconds': seconds,
                        'coordinates': coordinates,
                        'description': 'goalkick',
                        'type': None,
                        'percentage': None,
                        'timestamp': self.get_timestamp(),
                        '_dispatch_match_event': True,
                    }
                    id = self.get_id(event)
                    self.events[id] = event
                    self.log('/i18n/en-gb/commentary', [event['team'], event['seconds'], event['description']])
                    continue
                if item[4] == 'HALF_TIME':
                    seconds = item[3]
                    coordinates = self.get_coordinates(item[5])
                    event = {
                        'team': None,
                        'player': None,
                        'seconds': seconds,
                        'coordinates': coordinates,
                        'description': 'halftime',
                        'type': None,
                        'percentage': None,
                        'timestamp': self.get_timestamp(),
                        '_dispatch_match_event': True,
                    }
                    id = self.get_id(event)
                    self.events[id] = event
                    self.log('/i18n/en-gb/commentary', [event['team'], event['seconds'], event['description']])
                    continue
                if item[4] == 'HOME_ATTACK':
                    seconds = item[3]
                    coordinates = self.get_coordinates(item[5])
                    event = {
                        'team': 'home',
                        'player': None,
                        'seconds': seconds,
                        'coordinates': coordinates,
                        'description': 'attack',
                        'type': None,
                        'percentage': None,
                        'timestamp': self.get_timestamp(),
                        '_dispatch_match_event': True,
                    }
                    id = self.get_id(event)
                    self.events[id] = event
                    self.log('/i18n/en-gb/commentary', [event['team'], event['seconds'], event['description']])
                    continue
                if item[4] == 'HOME_DANGER':
                    seconds = item[3]
                    coordinates = self.get_coordinates(item[5])
                    event = {
                        'team': 'home',
                        'player': None,
                        'seconds': seconds,
                        'coordinates': coordinates,
                        'description': 'danger',
                        'type': None,
                        'percentage': None,
                        'timestamp': self.get_timestamp(),
                        '_dispatch_match_event': True,
                    }
                    id = self.get_id(event)
                    self.events[id] = event
                    self.log('/i18n/en-gb/commentary', [event['team'], event['seconds'], event['description']])
                    continue
                if item[4] == 'HOME_SAFE':
                    seconds = item[3]
                    coordinates = self.get_coordinates(item[5])
                    event = {
                        'team': 'home',
                        'player': None,
                        'seconds': seconds,
                        'coordinates': coordinates,
                        'description': 'safe',
                        'type': None,
                        'percentage': None,
                        'timestamp': self.get_timestamp(),
                        '_dispatch_match_event': True,
                    }
                    id = self.get_id(event)
                    self.events[id] = event
                    self.log('/i18n/en-gb/commentary', [event['team'], event['seconds'], event['description']])
                    continue
                if item[4] == 'KICK_OFF_AWAY':
                    seconds = item[3]
                    coordinates = self.get_coordinates(item[5])
                    event = {
                        'team': 'away',
                        'player': None,
                        'seconds': seconds,
                        'coordinates': coordinates,
                        'description': 'kickoff',
                        'type': None,
                        'percentage': None,
                        'timestamp': self.get_timestamp(),
                        '_dispatch_match_event': True,
                    }
                    id = self.get_id(event)
                    self.events[id] = event
                    self.log('/i18n/en-gb/commentary', [event['team'], event['seconds'], event['description']])
                    continue
                if item[4] == 'KICK_OFF_HOME':
                    seconds = item[3]
                    coordinates = self.get_coordinates(item[5])
                    event = {
                        'team': 'home',
                        'player': None,
                        'seconds': seconds,
                        'coordinates': coordinates,
                        'description': 'kickoff',
                        'type': None,
                        'percentage': None,
                        'timestamp': self.get_timestamp(),
                        '_dispatch_match_event': True,
                    }
                    id = self.get_id(event)
                    self.events[id] = event
                    self.log('/i18n/en-gb/commentary', [event['team'], event['seconds'], event['description']])
                    continue
                if item[4] == 'LINE_UP':
                    continue
                if item[4] == 'PENALTY_AWAY':
                    continue
                if item[4] == 'PENALTY_HOME':
                    continue
                if item[4] == 'PENALTY_MISSED_AWAY':
                    seconds = item[3]
                    coordinates = self.get_coordinates(item[5])
                    event = {
                        'team': 'away',
                        'player': None,
                        'seconds': seconds,
                        'coordinates': coordinates,
                        'description': 'penaltyMiss',
                        'type': None,
                        'percentage': None,
                        'timestamp': self.get_timestamp(),
                        '_dispatch_match_event': True,
                    }
                    id = self.get_id(event)
                    self.events[id] = event
                    self.log('/i18n/en-gb/commentary', [event['team'], event['seconds'], event['description']])
                    continue
                if item[4] == 'PENALTY_MISSED_HOME':
                    seconds = item[3]
                    coordinates = self.get_coordinates(item[5])
                    event = {
                        'team': 'home',
                        'player': None,
                        'seconds': seconds,
                        'coordinates': coordinates,
                        'description': 'penaltyMiss',
                        'type': None,
                        'percentage': None,
                        'timestamp': self.get_timestamp(),
                        '_dispatch_match_event': True,
                    }
                    id = self.get_id(event)
                    self.events[id] = event
                    self.log('/i18n/en-gb/commentary', [event['team'], event['seconds'], event['description']])
                    continue
                if item[4] == 'RED_CARD_AWAY':
                    continue
                if item[4] == 'RED_CARD_HOME':
                    continue
                if item[4] == 'SECOND_HALF':
                    seconds = item[3]
                    coordinates = self.get_coordinates(item[5])
                    event = {
                        'team': None,
                        'player': None,
                        'seconds': seconds,
                        'coordinates': coordinates,
                        'description': 'secondhalf',
                        'type': None,
                        'percentage': None,
                        'timestamp': self.get_timestamp(),
                        '_dispatch_match_event': True,
                    }
                    id = self.get_id(event)
                    self.events[id] = event
                    self.log('/i18n/en-gb/commentary', [event['team'], event['seconds'], event['description']])
                    continue
                if item[4] == 'SHOT_BLOCKED_AWAY':
                    continue
                if item[4] == 'SHOT_BLOCKED_HOME':
                    continue
                if item[4] == 'SHOT_OFF_TARGET_AWAY':
                    continue
                if item[4] == 'SHOT_OFF_TARGET_HOME':
                    continue
                if item[4] == 'SHOT_ON_TARGET_AWAY':
                    continue
                if item[4] == 'SHOT_ON_TARGET_HOME':
                    continue
                if item[4] == 'SHOT_ON_WOODWORK_AWAY':
                    continue
                if item[4] == 'SHOT_ON_WOODWORK_HOME':
                    continue
                if item[4] == 'SUBSTITUTION_AWAY':
                    seconds = item[3]
                    coordinates = self.get_coordinates(item[5])
                    event = {
                        'team': 'away',
                        'player': None,
                        'seconds': seconds,
                        'coordinates': coordinates,
                        'description': 'substitution',
                        'type': None,
                        'percentage': None,
                        'timestamp': self.get_timestamp(),
                        '_dispatch_match_event': True,
                    }
                    id = self.get_id(event)
                    self.events[id] = event
                    self.log('/i18n/en-gb/commentary', [event['team'], event['seconds'], event['description']])
                    continue
                if item[4] == 'SUBSTITUTION_HOME':
                    seconds = item[3]
                    coordinates = self.get_coordinates(item[5])
                    event = {
                        'team': 'home',
                        'player': None,
                        'seconds': seconds,
                        'coordinates': coordinates,
                        'description': 'substitution',
                        'type': None,
                        'percentage': None,
                        'timestamp': self.get_timestamp(),
                        '_dispatch_match_event': True,
                    }
                    id = self.get_id(event)
                    self.events[id] = event
                    self.log('/i18n/en-gb/commentary', [event['team'], event['seconds'], event['description']])
                    continue
                if item[4] == 'THROW_IN_AWAY':
                    seconds = item[3]
                    coordinates = self.get_coordinates(item[5])
                    event = {
                        'team': 'away',
                        'player': None,
                        'seconds': seconds,
                        'coordinates': coordinates,
                        'description': 'throw',
                        'type': None,
                        'percentage': None,
                        'timestamp': self.get_timestamp(),
                        '_dispatch_match_event': True,
                    }
                    id = self.get_id(event)
                    self.events[id] = event
                    self.log('/i18n/en-gb/commentary', [event['team'], event['seconds'], event['description']])
                    continue
                if item[4] == 'THROW_IN_HOME':
                    seconds = item[3]
                    coordinates = self.get_coordinates(item[5])
                    event = {
                        'team': 'home',
                        'player': None,
                        'seconds': seconds,
                        'coordinates': coordinates,
                        'description': 'throw',
                        'type': None,
                        'percentage': None,
                        'timestamp': self.get_timestamp(),
                        '_dispatch_match_event': True,
                    }
                    id = self.get_id(event)
                    self.events[id] = event
                    self.log('/i18n/en-gb/commentary', [event['team'], event['seconds'], event['description']])
                    continue
                if item[4] == 'YELLOW_CARD_AWAY':
                    continue
                if item[4] == 'YELLOW_CARD_HOME':
                    continue
            return
        if payload[0][0].endswith('/stats/away/cards/red'):
            for item in payload[1:]:
                player = None
                if len(item) >= 3:
                    player = item[2]
                seconds = item[1]
                event = {
                    'team': 'away',
                    'player': player,
                    'seconds': seconds,
                    'coordinates': None,
                    'description': 'redCard',
                    'type': None,
                    'percentage': None,
                    'timestamp': self.get_timestamp(),
                    '_dispatch_match_event': True,
                }
                id = self.get_id(event)
                self.events[id] = event
            count = self.get_count('away', 'redCard')
            self.log('/stats/away/cards/red', count)
            return
        if payload[0][0].endswith('/stats/away/cards/yellow'):
            for item in payload[1:]:
                player = None
                if len(item) >= 3:
                    player = item[2]
                seconds = item[1]
                event = {
                    'team': 'away',
                    'player': player,
                    'seconds': seconds,
                    'coordinates': None,
                    'description': 'yellowCard',
                    'type': None,
                    'percentage': None,
                    'timestamp': self.get_timestamp(),
                    '_dispatch_match_event': True,
                }
                id = self.get_id(event)
                self.events[id] = event
            count = self.get_count('away', 'yellowCard')
            self.log('/stats/away/cards/yellow', count)
            return
        if payload[0][0].endswith('/stats/away/corners'):
            for item in payload[1:]:
                seconds = item[1]
                event = {
                    'team': 'away',
                    'player': None,
                    'seconds': seconds,
                    'coordinates': None,
                    'description': 'corner',
                    'type': None,
                    'percentage': None,
                    'timestamp': self.get_timestamp(),
                    '_dispatch_match_event': True,
                }
                id = self.get_id(event)
                self.events[id] = event
            count = self.get_count('away', 'corner')
            self.log('/stats/away/corners', count)
            return
        if payload[0][0].endswith('/stats/away/freeKicks'):
            for item in payload[1:]:
                seconds = item[1]
                event = {
                    'team': 'away',
                    'player': None,
                    'seconds': seconds,
                    'coordinates': None,
                    'description': 'dfreekick',
                    'type': None,
                    'percentage': None,
                    'timestamp': self.get_timestamp(),
                    '_dispatch_match_event': True,
                }
                id = self.get_id(event)
                self.events[id] = event
            count = self.get_count('away', 'dfreekick')
            self.log('/stats/away/freeKicks', count)
            return
        if payload[0][0].endswith('/stats/away/goals'):
            for item in payload[1:]:
                player = None
                if len(item) >= 3:
                    player = item[2]
                seconds = item[1]
                event = {
                    'team': 'away',
                    'player': player,
                    'seconds': seconds,
                    'coordinates': None,
                    'description': 'goal',
                    'type': 'G',
                    'percentage': None,
                    'timestamp': self.get_timestamp(),
                    '_dispatch_match_event': True,
                }
                id = self.get_id(event)
                self.events[id] = event
            count = self.get_count('away', 'goal')
            self.log('/stats/away/goals', count)
            return
        if payload[0][0].endswith('/stats/away/penalties'):
            for item in payload[1:]:
                player = None
                if len(item) >= 3:
                    player = item[2]
                seconds = item[1]
                event = {
                    'team': 'away',
                    'player': player,
                    'seconds': seconds,
                    'coordinates': None,
                    'description': 'penalty',
                    'type': 'P',
                    'percentage': None,
                    'timestamp': self.get_timestamp(),
                    '_dispatch_match_event': True,
                }
                id = self.get_id(event)
                self.events[id] = event
            count = self.get_count('away', 'penalty')
            self.log('/stats/away/penalties', count)
            return
        if payload[0][0].endswith('/stats/away/shots/offTarget'):
            for item in payload[1:]:
                seconds = item[1]
                event = {
                    'team': 'away',
                    'player': None,
                    'seconds': seconds,
                    'coordinates': None,
                    'description': 'shotoffgoal',
                    'type': None,
                    'percentage': None,
                    'timestamp': self.get_timestamp(),
                    '_dispatch_match_event': True,
                }
                id = self.get_id(event)
                self.events[id] = event
            count = self.get_count('away', 'shotoffgoal')
            self.log('/stats/away/shots/offTarget', count)
            return
        if payload[0][0].endswith('/stats/away/shots/onTarget'):
            for item in payload[1:]:
                seconds = item[1]
                event = {
                    'team': 'away',
                    'player': None,
                    'seconds': seconds,
                    'coordinates': None,
                    'description': 'shotongoal',
                    'type': None,
                    'percentage': None,
                    'timestamp': self.get_timestamp(),
                    '_dispatch_match_event': True,
                }
                id = self.get_id(event)
                self.events[id] = event
            count = self.get_count('away', 'shotongoal')
            self.log('/stats/away/shots/onTarget', count)
            return
        if payload[0][0].endswith('/stats/away/shots/onWoodwork'):
            for item in payload[1:]:
                seconds = item[1]
                event = {
                    'team': 'away',
                    'player': None,
                    'seconds': seconds,
                    'coordinates': None,
                    'description': 'shotongoal',
                    'type': None,
                    'percentage': None,
                    'timestamp': self.get_timestamp(),
                    '_dispatch_match_event': True,
                }
                id = self.get_id(event)
                self.events[id] = event
            count = self.get_count('away', 'shotongoal')
            self.log('/stats/away/shots/onWoodwork', count)
            return
        if payload[0][0].endswith('/stats/away/substitutions'):
            for item in payload[1:]:
                seconds = item[1]
                event = {
                    'team': 'away',
                    'player': None,
                    'seconds': seconds,
                    'coordinates': None,
                    'description': 'substitution',
                    'type': None,
                    'percentage': None,
                    'timestamp': self.get_timestamp(),
                    '_dispatch_match_event': True,
                }
                id = self.get_id(event)
                self.events[id] = event
            count = self.get_count('away', 'substitution')
            self.log('/stats/away/substitutions', count)
            return
        if payload[0][0].endswith('/stats/away/throwIns'):
            for item in payload[1:]:
                seconds = item[1]
                event = {
                    'team': 'away',
                    'player': None,
                    'seconds': seconds,
                    'coordinates': None,
                    'description': 'throw',
                    'type': None,
                    'percentage': None,
                    'timestamp': self.get_timestamp(),
                    '_dispatch_match_event': True,
                }
                id = self.get_id(event)
                self.events[id] = event
            count = self.get_count('away', 'throw')
            self.log('/stats/away/throwIns', count)
            return
        if payload[0][0].endswith('/stats/home/cards/red'):
            for item in payload[1:]:
                player = None
                if len(item) >= 3:
                    player = item[2]
                seconds = item[1]
                event = {
                    'team': 'home',
                    'player': player,
                    'seconds': seconds,
                    'coordinates': None,
                    'description': 'redCard',
                    'type': None,
                    'percentage': None,
                    'timestamp': self.get_timestamp(),
                    '_dispatch_match_event': True,
                }
                id = self.get_id(event)
                self.events[id] = event
            count = self.get_count('home', 'redCard')
            self.log('/stats/home/cards/red', count)
            return
        if payload[0][0].endswith('/stats/home/cards/yellow'):
            for item in payload[1:]:
                player = None
                if len(item) >= 3:
                    player = item[2]
                seconds = item[1]
                event = {
                    'team': 'home',
                    'player': player,
                    'seconds': seconds,
                    'coordinates': None,
                    'description': 'yellowCard',
                    'type': None,
                    'percentage': None,
                    'timestamp': self.get_timestamp(),
                    '_dispatch_match_event': True,
                }
                id = self.get_id(event)
                self.events[id] = event
            count = self.get_count('home', 'yellowCard')
            self.log('/stats/home/cards/yellow', count)
            return
        if payload[0][0].endswith('/stats/home/corners'):
            for item in payload[1:]:
                seconds = item[1]
                event = {
                    'team': 'home',
                    'player': None,
                    'seconds': seconds,
                    'coordinates': None,
                    'description': 'corner',
                    'type': None,
                    'percentage': None,
                    'timestamp': self.get_timestamp(),
                    '_dispatch_match_event': True,
                }
                id = self.get_id(event)
                self.events[id] = event
            count = self.get_count('home', 'corner')
            self.log('/stats/home/corners', count)
            return
        if payload[0][0].endswith('/stats/home/freeKicks'):
            for item in payload[1:]:
                seconds = item[1]
                event = {
                    'team': 'home',
                    'player': None,
                    'seconds': seconds,
                    'coordinates': None,
                    'description': 'dfreekick',
                    'type': None,
                    'percentage': None,
                    'timestamp': self.get_timestamp(),
                    '_dispatch_match_event': True,
                }
                id = self.get_id(event)
                self.events[id] = event
            count = self.get_count('home', 'dfreekick')
            self.log('/stats/home/freeKicks', count)
            return
        if payload[0][0].endswith('/stats/home/goals'):
            for item in payload[1:]:
                player = None
                if len(item) >= 3:
                    player = item[2]
                seconds = item[1]
                event = {
                    'team': 'home',
                    'player': player,
                    'seconds': seconds,
                    'coordinates': None,
                    'description': 'goal',
                    'type': 'G',
                    'percentage': None,
                    'timestamp': self.get_timestamp(),
                    '_dispatch_match_event': True,
                }
                id = self.get_id(event)
                self.events[id] = event
            count = self.get_count('home', 'goal')
            self.log('/stats/home/goals', count)
            return
        if payload[0][0].endswith('/stats/home/penalties'):
            for item in payload[1:]:
                player = None
                if len(item) >= 3:
                    player = item[2]
                seconds = item[1]
                event = {
                    'team': 'home',
                    'player': player,
                    'seconds': seconds,
                    'coordinates': None,
                    'description': 'penalty',
                    'type': 'P',
                    'percentage': None,
                    'timestamp': self.get_timestamp(),
                    '_dispatch_match_event': True,
                }
                id = self.get_id(event)
                self.events[id] = event
            count = self.get_count('home', 'penalty')
            self.log('/stats/home/penalties', count)
            return
        if payload[0][0].endswith('/stats/home/shots/offTarget'):
            for item in payload[1:]:
                seconds = item[1]
                event = {
                    'team': 'home',
                    'player': None,
                    'seconds': seconds,
                    'coordinates': None,
                    'description': 'shotoffgoal',
                    'type': None,
                    'percentage': None,
                    'timestamp': self.get_timestamp(),
                    '_dispatch_match_event': True,
                }
                id = self.get_id(event)
                self.events[id] = event
            count = self.get_count('home', 'shotoffgoal')
            self.log('/stats/home/shots/offTarget', count)
            return
        if payload[0][0].endswith('/stats/home/shots/onTarget'):
            for item in payload[1:]:
                seconds = item[1]
                event = {
                    'team': 'home',
                    'player': None,
                    'seconds': seconds,
                    'coordinates': None,
                    'description': 'shotongoal',
                    'type': None,
                    'percentage': None,
                    'timestamp': self.get_timestamp(),
                    '_dispatch_match_event': True,
                }
                id = self.get_id(event)
                self.events[id] = event
            count = self.get_count('home', 'shotongoal')
            self.log('/stats/home/shots/onTarget', count)
            return
        if payload[0][0].endswith('/stats/home/shots/onWoodwork'):
            for item in payload[1:]:
                seconds = item[1]
                event = {
                    'team': 'home',
                    'player': None,
                    'seconds': seconds,
                    'coordinates': None,
                    'description': 'shotongoal',
                    'type': None,
                    'percentage': None,
                    'timestamp': self.get_timestamp(),
                    '_dispatch_match_event': True,
                }
                id = self.get_id(event)
                self.events[id] = event
            count = self.get_count('home', 'shotongoal')
            self.log('/stats/home/shots/onWoodwork', count)
            return
        if payload[0][0].endswith('/stats/home/substitutions'):
            for item in payload[1:]:
                seconds = item[1]
                event = {
                    'team': 'home',
                    'player': None,
                    'seconds': seconds,
                    'coordinates': None,
                    'description': 'substitution',
                    'type': None,
                    'percentage': None,
                    'timestamp': self.get_timestamp(),
                    '_dispatch_match_event': True,
                }
                id = self.get_id(event)
                self.events[id] = event
            count = self.get_count('home', 'substitution')
            self.log('/stats/home/substitutions', count)
            return
        if payload[0][0].endswith('/stats/home/throwIns'):
            for item in payload[1:]:
                seconds = item[1]
                event = {
                    'team': 'home',
                    'player': None,
                    'seconds': seconds,
                    'coordinates': None,
                    'description': 'throw',
                    'type': None,
                    'percentage': None,
                    'timestamp': self.get_timestamp(),
                    '_dispatch_match_event': True,
                }
                id = self.get_id(event)
                self.events[id] = event
            count = self.get_count('home', 'throw')
            self.log('/stats/home/throwIns', count)
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
                'timestamp': self.get_timestamp(),
                '_dispatch_match_event': True,
            }
            id = self.get_id(event)
            self.events[id] = event
            event = {
                'team': 'away',
                'player': None,
                'minute': None,
                'coordinates': None,
                'description': 'possession',
                'type': None,
                'percentage': away,
                'timestamp': self.get_timestamp(),
                '_dispatch_match_event': True,
            }
            id = self.get_id(event)
            self.events[id] = event
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
    def get_coordinates(self, coordinates):
        if not coordinates:
            return None
        # TODO
        return (0.0, 0.0)

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
    def get_id(self, event):
        items = []
        for key, value in event.items():
            if key == '_dispatch_match_event':
                continue
            if key == 'percentage':
                continue
            if key == 'timestamp':
                continue
            items.append((key, value,))
        items = sorted(items)
        items = tuple(items)
        id = hash(items)
        return id

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
    def get_timestamp(self):
        timestamp = time()
        timestamp = int(timestamp)
        return timestamp

    @trace
    def get_topic(self, payload):
        if payload in self.topics:
            return self.topics[payload]
        return None


@trace
def main(options):
    if options[1] == '--matches':
        execute_matches()
        return
    if options[1] == '--web-sockets':
        execute_web_sockets(options[2])
        return
    if options[1] == '--threads':
        execute_threads()
        return


@trace
def execute_matches():
    matches = process_matches()
    pprint(matches)


@trace
def execute_web_sockets(id):
    id = int(id)
    web_sockets = WebSockets(id)
    web_sockets.open()


@trace
def execute_threads():
    threads = []
    matches = process_matches()
    for match in matches:
        thread = Thread(target=execute_web_sockets, args=[match['id']])
        threads.append(thread)
    for thread in threads:
        thread.start()
    for thread in threads:
        thread.join()


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
