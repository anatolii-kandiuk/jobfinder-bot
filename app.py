# -*- coding: utf-8 -*-
import re
import os
import requests
from flask import Flask
from flask import request
from flask import jsonify

# from dotenv import load_dotenv

# from flask_sslify import SSLify
# load_dotenv()

TOKEN = os.environ.get('TOKEN')
URL = 'https://api.telegram.org/bot{}/'.format(TOKEN)
headers = {'user-agent': 'my-app/0.0.1'}
API_URL = os.environ.get('API_URL')
app = Flask(__name__)
app.config['DEBUG'] = False


# https://api.telegram.org/botTOKEN/setWebhook?url=https://b9f92555.ngrok.io
# https://api.telegram.org/botTOKEN/deleteWebhook


def send_message(chat_id, text='Empty'):
    session = requests.Session()
    url = URL + 'sendMessage'
    r = session.get(url, headers=headers,
                    params=dict(chat_id=chat_id,
                                text=text,
                                parse_mode='Markdown', ))  # parse_mode = 'HTML'

    return r.json()


def parse_text(text):
    command_pattern = r'/\w+'
    vacancy_pattern = r'@\w+'  # @\w+\+\w+

    if '/' in text:
        addresses = {'cities': '/cities', 'pl': '/program_languages'}
        if '/start' in text or '/help' in text:
            message = '''
            Щоб дізнатися які міста доступні введіть `/city`. 
            Щоб дізнатися які мови програмування доступні введіть `/pl` 
            Щоб зробити запит, використайте конструкцію - @city @program language. 
            Наприклад: `@kyiv @python` 
            '''
            return message
        command = re.search(command_pattern, text).group().replace('/', '')
        return addresses.get(command, None)
    elif '@' in text:
        # @kyiv @python
        v_search = re.findall(vacancy_pattern, text)
        commands = [x.replace('@', '') for x in v_search]
        return commands
    else:
        return None


def get_api_response(addr):
    session = requests.Session()
    url = API_URL + addr
    r = session.get(url, headers=headers).json()
    # print(r)
    return r


@app.route('/', methods=['POST', 'GET'])
def index():
    if request.method == 'POST':
        r = request.get_json()
        chat_id = r['message']['chat']['id']
        text_msg = r['message']['text']
        tmp = parse_text(text_msg)

        text_msg = 'Запит невірний'
        if tmp:
            # print('TMP!')
            if len(tmp) == 2:
                address = '/vacancies/?city={}&pl={}'.format(*tmp)
                print(address)
                resp = get_api_response(address)
                if resp:
                    pices = []
                    size_of_resp = len(resp)
                    extra = len(resp) % 10
                    if size_of_resp < 11:
                        pices.append(resp)
                    else:
                        for i in range(size_of_resp // 10):
                            y = i * 10
                            pices.append(resp[y:y + 10])
                        if extra:
                            pices.append(resp[y + 10:])

                    text_msg = '''Більше даних на сайті\n https://vacancies-finder.herokuapp.com \nРезультати пошуку:\n'''

                    send_message(chat_id, text_msg)
                    for part in pices:
                        message = ''
                        for v in part:
                            message += v['title'] + '\n'
                            # message +=  v['description'] + '\n'
                            # message +=  'Company:' + v['company'] + '\n'
                            # message +=  'Date:' + v['timestamp'] + '\n'
                            message += v['url'] + '\n'
                            message += '-' * 5 + '\n\n'
                        send_message(chat_id, message)
                else:
                    text_msg = 'За вашим запитом нічого не знайдено.'
                    send_message(chat_id, text_msg)
            elif len(tmp) >= 20:
                send_message(chat_id, tmp)
            else:
                resp = get_api_response(tmp)
                if resp:
                    message = ''
                    for d in resp:
                        message += '#' + d['slug'] + '\n'
                    if '/cities' == tmp:
                        text_msg = 'Доступні міста: \n'
                    else:
                        text_msg = 'Доступні мови програмування: \n'
                    text_msg += message
                send_message(chat_id, text_msg)
        else:
            send_message(chat_id, text_msg)
        return jsonify(r)
    return '<h1> HI Bot <h1>'


if __name__ == '__main__':
    app.run()
