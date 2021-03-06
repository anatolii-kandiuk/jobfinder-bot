import requests
import re
from flask import Flask
from flask.views import MethodView
from flask import request
import os
# from dotenv import load_dotenv
# load_dotenv()

app = Flask(__name__)
TOKEN = os.environ.get('TOKEN')
API_URL = os.environ.get('API_URL')
TELEGRAM_URL = f'https://api.telegram.org/bot{TOKEN}/sendMessage'


def get_data_from_api(command):
    url = API_URL + command
    session = requests.Session()
    r = session.get(url).json()
    return r


def send_message(chat_id, msg):
    session = requests.Session()
    r = session.get(TELEGRAM_URL, params=dict(chat_id=chat_id,
                                              text=msg,
                                              parse_mode='Markdown'))
    return r.json()


def parse_text(text_msg):
    '''/start /help, /city /pl, @kyiv @python'''
    addresses = {'city': '/cities', 'pl': '/pl'}
    command_p = r'/\w+'
    dog_p = r'@\w+'
    message = 'Невірний запит'
    if '/' in text_msg:
        if '/start' in text_msg or '/help' in text_msg:
            message = '''
            Щоб дізнатися які міста доступні введіть `/city`.
            Щоб дізнатися які мови програмування доступні введіть `/pl`
            Щоб зробити запит, використайте конструкцію - @city @pl.
            Наприклад: `@kyiv @python`
            '''
            return message
        else:
            command = re.search(command_p, text_msg).group().replace('/', '')
            command = addresses.get(command, None)
            return [command] if command else None
    elif '@' in text_msg:
        result = re.findall(dog_p, text_msg)
        commands = [s.replace('@', '') for s in result]
        return commands if len(commands) == 2 else None
    else:
        return message


@app.route('/', methods=["POST", "GET"])
def index():
    if request.method == "POST":
        resp = request.get_json()
        print(resp)
        return '<h1> Hi Telegram!!! </h1>'
    return '<h1> Hi BOT!!! </h1>'


class BotAPI(MethodView):

    def get(self):
        return '<h1> Hi BOT_Class!!! </h1>'

    def post(self):
        resp = request.get_json()
        text_msg = resp['message']['text']
        chat_id = resp['message']['chat']['id']
        tmp = parse_text(text_msg)
        text = 'Невірний запит'
        error_msg = 'По вашому запиту нічого не знайдено'
        if tmp:
            if len(tmp) > 10:
                send_message(chat_id, tmp)
            elif len(tmp) == 1:
                resp = get_data_from_api(tmp[0])
                if resp:
                    message = ''
                    for d in resp:
                        message += '#' + d['slug'] + '\n'
                    if tmp[0] == '/pl':
                        msg = "Доступні мови програмування: \n"
                    else:
                        msg = "Доступні міста: \n"
                    send_message(chat_id, msg + message)
                else:
                    send_message(chat_id, error_msg)
            elif len(tmp) == 2:
                command = '/vacancy/?city={}&pl={}'.format(*tmp)
                resp = get_data_from_api(command)
                if resp:
                    pices = []
                    size = len(resp)
                    extra = len(resp) % 10
                    if size < 11:
                        pices.append(resp)
                    else:
                        for i in range(size // 10):
                            y = i * 10
                            pices.append(resp[y:y + 10])
                        if extra:
                            pices.append(resp[y + 10:])
                    # Відправляю в відповідь заголовок
                    text_msg = 'Результат:\n'
                    text_msg += '--- ' * 10 + '\n'
                    send_message(chat_id, text_msg)

                    for part in pices:
                        # для кожної частини формую нову відповідь
                        # і додаю в той же чат
                        message = ''
                        for v in part:
                            message += v['title'].replace('\t', '').replace('\n', '') + '\n'
                            url = v['url'].split('?')
                            message += url[0] + '\n'
                            message += '-' * 5 + '\n\n'
                        send_message(chat_id, message)
                else:
                    send_message(chat_id, error_msg)
        else:
            send_message(chat_id, text)
        return '<h1> Hi Telegram_Class!!! </h1>'


app.add_url_rule(f'/{TOKEN}/', view_func=BotAPI.as_view('bot'))

if __name__ == '__main__':
    app.run()
