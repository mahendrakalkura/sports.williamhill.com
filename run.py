'''
MD - \x00 - Message delimiter
RD - \x01 - Record delimiter
FD - \x02 - Field delimiter

4 <FD> 100 <FD> <CLIENT ID>                       0xff
4 \x02 100 \x02 C8C4048C779163D1-003B07C40000000A ?

T {header<RD>} {data} D
'''

from pprint import pprint

from requests import request
from scrapy import Selector
from websocket import WebSocketApp


def matches():
    url = 'http://sports.williamhill.com/bet/en-gb/betlive/9'
    response = request(method='GET', url=url)
    if not response:
        return
    selector = Selector(text=response.text)
    trs = selector.xpath('//div[@id="ip_sport_9_types"]/div/div/div/table/tbody/tr')
    for tr in trs:
        url = None
        try:
            url = tr.xpath('.//td[3]/a/@href').extract()[0]
        except Exception:
            pass
        id = url.split('/')[-2]
        teams = {
            'home': None,
            'away': None,
        }
        try:
            title = tr.xpath('.//td[3]/a/span/text()').extract()[0]
            title = title.replace('&nbsp;', '')
            title = title.split(' v ')
            title = map(str.strip, title)
            title = list(title)
            teams['home'] = title[0]
            teams['away'] = title[1]
        except Exception:
            pass
        date = None
        status = {
            'period': None,
        }
        events = None
        timestamp = None
        match = {
            'id': id,
            'teams': teams,
            'date': date,
            'status': status,
            'events': events,
            'timestamp': timestamp, # to be updated whenever match itself is
                                    # updated
        }
        web_sockets(match)
        break


def web_sockets(match):

    def on_open(web_socket):
        print('[+] Open')

    def on_close(web_socket):
        print('[+] Close')

    def on_message(web_socket, message):
        message = bytearray(message, 'utf-8')
        if message[0] == 52:
            message = message.split(b'\x02')
            client_id = message[2]
            print('[+] Client ID:', client_id.decode('utf-8'))
            send(bytearray(b'\x16sportsbook/football/' + bytes(match['id'], 'utf-8') + b'\x01'))
            send(bytearray(b'\x16sportsbook/football/' + bytes(match['id'], 'utf-8') + b'/stats/away\x01'))
            send(bytearray(b'\x16sportsbook/football/' + bytes(match['id'], 'utf-8') + b'/stats/away/cards/red\x01'))
            send(bytearray(b'\x16sportsbook/football/' + bytes(match['id'], 'utf-8') + b'/stats/away/cards/yellow\x01'))
            send(bytearray(b'\x16sportsbook/football/' + bytes(match['id'], 'utf-8') + b'/stats/away/corners\x01'))
            send(bytearray(b'\x16sportsbook/football/' + bytes(match['id'], 'utf-8') + b'/stats/away/freeKicks\x01'))
            send(bytearray(b'\x16sportsbook/football/' + bytes(match['id'], 'utf-8') + b'/stats/away/goals\x01'))
            send(bytearray(b'\x16sportsbook/football/' + bytes(match['id'], 'utf-8') + b'/stats/away/lineup\x01'))
            send(bytearray(b'\x16sportsbook/football/' + bytes(match['id'], 'utf-8') + b'/stats/away/penalties\x01'))
            send(bytearray(b'\x16sportsbook/football/' + bytes(match['id'], 'utf-8') + b'/stats/away/shots/offTarget\x01'))
            send(bytearray(b'\x16sportsbook/football/' + bytes(match['id'], 'utf-8') + b'/stats/away/shots/onTarget\x01'))
            send(bytearray(b'\x16sportsbook/football/' + bytes(match['id'], 'utf-8') + b'/stats/away/shots/onWoodwork\x01'))
            send(bytearray(b'\x16sportsbook/football/' + bytes(match['id'], 'utf-8') + b'/stats/away/substitutions\x01'))
            send(bytearray(b'\x16sportsbook/football/' + bytes(match['id'], 'utf-8') + b'/stats/away/throwIns\x01'))
            send(bytearray(b'\x16sportsbook/football/' + bytes(match['id'], 'utf-8') + b'/stats/home\x01'))
            send(bytearray(b'\x16sportsbook/football/' + bytes(match['id'], 'utf-8') + b'/stats/home/cards/red\x01'))
            send(bytearray(b'\x16sportsbook/football/' + bytes(match['id'], 'utf-8') + b'/stats/home/cards/yellow\x01'))
            send(bytearray(b'\x16sportsbook/football/' + bytes(match['id'], 'utf-8') + b'/stats/home/corners\x01'))
            send(bytearray(b'\x16sportsbook/football/' + bytes(match['id'], 'utf-8') + b'/stats/home/freeKicks\x01'))
            send(bytearray(b'\x16sportsbook/football/' + bytes(match['id'], 'utf-8') + b'/stats/home/goals\x01'))
            send(bytearray(b'\x16sportsbook/football/' + bytes(match['id'], 'utf-8') + b'/stats/home/lineup\x01'))
            send(bytearray(b'\x16sportsbook/football/' + bytes(match['id'], 'utf-8') + b'/stats/home/penalties\x01'))
            send(bytearray(b'\x16sportsbook/football/' + bytes(match['id'], 'utf-8') + b'/stats/home/shots/offTarget\x01'))
            send(bytearray(b'\x16sportsbook/football/' + bytes(match['id'], 'utf-8') + b'/stats/home/shots/onTarget\x01'))
            send(bytearray(b'\x16sportsbook/football/' + bytes(match['id'], 'utf-8') + b'/stats/home/shots/onWoodwork\x01'))
            send(bytearray(b'\x16sportsbook/football/' + bytes(match['id'], 'utf-8') + b'/stats/home/throwIns\x01'))
            send(bytearray(b'\x16sportsbook/football/' + bytes(match['id'], 'utf-8') + b'/stats/homeTeamPossesion\x01'))
            send(bytearray(b'\x16sportsbook/football/' + bytes(match['id'], 'utf-8') + b'/stats/mode\x01'))
            send(bytearray(b'\x16sportsbook/football/' + bytes(match['id'], 'utf-8') + b'/stats/period\x01'))
            send(bytearray(b'\x16sportsbook/football/' + bytes(match['id'], 'utf-8') + b'/stats/score\x01'))
            send(bytearray(b'\x16sportsbook/football/' + bytes(match['id'], 'utf-8') + b'/stats/time\x01'))
            return
        if message[0] == 25:
            message = message[1:]
            message = message.split(b'\x01')
            timestamp = message[0]
            print('[+] Ping     :', timestamp.decode('utf-8'))
            send(bytearray(b'\x18' + timestamp + b'\x02999\x01'))
            return
        print('[+] Unknown  :', message)

    def send(message):
        message.decode('utf-8')
        print('[+] Send     :', message)
        web_socket.send(message)

    def on_error(web_socket, error):
        print('[+] Error    :', error)

    web_socket = WebSocketApp(
        'wss://scoreboards-ssl.williamhill.com/diffusion?v=4&ty=WB',
        on_open=on_open,
        on_close=on_close,
        on_message=on_message,
        on_error=on_error,
    )
    web_socket.run_forever()


def main():
    matches()


if __name__ == '__main__':
    main()
