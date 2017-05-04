from json import loads
from pprint import pprint
from re import compile

from requests import request
from websocket import WebSocketApp

PATTERN = compile(r'document\.aip_list\.create_prebuilt_event\((.*?)\);')

DELIMITERS_MESSAGE = '\x00'
DELIMITERS_RECORD = '\x01'
DELIMITERS_FIELD = '\x02'

TYPES_CLIENT_ID = '4'
TYPES_TOPIC_LOAD_MESSAGE = '\x14'
TYPES_DELTA_MESSAGE = '\x15'
TYPES_SUBSCRIBE = '\x16'
TYPES_PING_CLIENT = '\x19'
TYPES_TOPIC_STATUS_NOTIFICATION = '\x23'


def fetch_matches():
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
        date = self._get_date(item['start_time'])
        match = {
            'id': id,
            'teams': teams,
            'date': date,
        }
        if match['id'] and match['teams']['home'] and match['teams']['away'] and match['date']:
            matches.append(match)
    return matches


def web_sockets(match):

    def on_open(web_socket):
        print('[+] Open')

    def on_close(web_socket):
        print('[+] Close')

    def on_message(web_socket, message):
        global INITIALIZED
        message = bytearray(message, 'utf-8')
        if chr(message[0]) == TYPES_CLIENT_ID:
            message = message.split(b'\x02')
            client_id = message[2]
            client_id = client_id.decode('utf-8')
            print('[+] Client ID:', client_id)
            topics = [
                'sportsbook/football/{id:d}',
                'sportsbook/football/{id:d}/animation',
                'sportsbook/football/{id:d}/i18n/en-gb/commentary',
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
            for topic in topics:
                message = topic
                message = message.format(id=match['id'])
                message = TYPES_SUBSCRIBE + message + DELIMITERS_RECORD
                message = bytearray(message, 'utf-8')
                send(message)
            return
        if chr(message[0]) == TYPES_TOPIC_LOAD_MESSAGE:
            message = message[1:]
            message = message.split(b'\x01')
            message = map(lambda item: item.decode('utf-8'), message)
            message = list(message)
            print('[+] Topic Load Message:', message)
            return
        if chr(message[0]) == TYPES_DELTA_MESSAGE:
            message = message[1:]
            message = message.split(b'\x01')
            message = map(lambda item: item.decode('utf-8'), message)
            message = list(message)
            print('[+] Delta Message:', message)
            return
        if chr(message[0]) == TYPES_PING_CLIENT:
            message = message[1:]
            message = message.split(b'\x01')
            timestamp = message[0]
            timestamp = timestamp.decode('utf-8')
            print('[+] Ping:', timestamp)
            message = TYPES_PING_CLIENT + timestamp + DELIMITERS_RECORD
            message = bytearray(message, 'utf-8')
            send(message)
            return
        if chr(message[0]) == TYPES_TOPIC_STATUS_NOTIFICATION:
            message = message[1:]
            message = message.split(b'\x01')
            message = map(lambda item: item.decode('utf-8'), message)
            message = list(message)
            print('[+] Topic Status Notification:', message)
        print('[+] Unknown:', repr(message))

    def send(message):
        print('[+] Send:', repr(message))
        web_socket.send(message)

    def on_error(web_socket, error):
        print('[+] Error:', error)

    web_socket = WebSocketApp(
        'wss://scoreboards-ssl.williamhill.com/diffusion?v=4&ty=WB',
        on_open=on_open,
        on_close=on_close,
        on_message=on_message,
        on_error=on_error,
    )
    web_socket.run_forever()


def main():
    matches = fetch_matches()
    pprint(matches)
    for match in matches:
        web_sockets(match)


if __name__ == '__main__':
    main()
