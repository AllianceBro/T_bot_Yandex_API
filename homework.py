import logging
import os
import time

import requests
import telegram
from dotenv import load_dotenv

load_dotenv()


class APIError(Exception):
    def __init__(self, text):
        self.txt = text


PRAKTIKUM_TOKEN = os.getenv('PRAKTIKUM_TOKEN')
TELEGRAM_TOKEN = os.getenv('TELEGRAM_TOKEN')
CHAT_ID = os.getenv('TELEGRAM_CHAT_ID')
YANDEX_HOMEWORK_URL = ('https://praktikum.yandex.ru/'
                       'api/user_api/homework_statuses/')
REQUEST_HEADERS = {'Authorization': f'OAuth {PRAKTIKUM_TOKEN}'}
HOMEWORK_IS_CHECKED = 'У вас проверили работу "{homework_name}"!\n\n{verdict}'
HOMEWORK_STATUS = {
    'rejected': 'К сожалению в работе нашлись ошибки.',
    'approved': 'Ревьюеру всё понравилось, '
                'можно приступать к следующему уроку.',
}
REQUEST_LOG = ('Request url was: {url}\n'
               'Headers were: {headers}\n'
               'Params were: {params}')
BOT_ERROR = 'Bot has faced an error: {}'
LOG_VALUE_ERROR = ('Json doesnt contain expected homework status values. '
                   'Json value: {}')
LOG_CONNECTION_ERROR = 'Request faced an error: {error}!\n' + REQUEST_LOG
LOG_API_ERROR = 'Server said that he faced a trouble: {error}!\n' + REQUEST_LOG


def parse_homework_status(homework):
    # Check if json contains expected values
    if homework['status'] not in HOMEWORK_STATUS:
        raise ValueError(
           LOG_VALUE_ERROR.format(homework['status'])
        )
    verdict = HOMEWORK_STATUS[homework['status']]
    return HOMEWORK_IS_CHECKED.format(
        homework_name=homework['homework_name'],
        verdict=verdict
    )


def get_homework_statuses(current_timestamp):
    headers = REQUEST_HEADERS
    params = {'from_date': current_timestamp}
    try:
        response = requests.get(
            YANDEX_HOMEWORK_URL,
            headers=headers,
            params=params
        )
    except requests.RequestException as error:
        raise ConnectionError(
            LOG_CONNECTION_ERROR.format(
                error=error,
                url=YANDEX_HOMEWORK_URL,
                headers=headers,
                params=params
            )
        )
    response_json = response.json()
    # Check if server sent an error message
    server_error_keys = ['error', 'code']
    for error_key in server_error_keys:
        if error_key in response_json:
            raise APIError(
                LOG_API_ERROR.format(
                    error=response_json[error_key],
                    url=YANDEX_HOMEWORK_URL,
                    headers=headers,
                    params=params
                )
            )
    return response_json


def send_message(message, bot_client):
    logging.info(f'Have sent a message: {message}')
    return bot_client.send_message(CHAT_ID, message)


def main():
    current_timestamp = int(time.time())
    logging.debug('Bot has launched')
    while True:
        try:
            new_homework = get_homework_statuses(current_timestamp)
            if new_homework.get('homeworks'):
                send_message(
                    parse_homework_status(new_homework.get('homeworks')[0]),
                    bot_client=telegram.Bot(token=TELEGRAM_TOKEN)
                )
            current_timestamp = new_homework.get(
                'current_date',
                current_timestamp
            )
            time.sleep(2000)
        except Exception as error:
            logging.error(
                BOT_ERROR.format(error),
                exc_info=False
            )
            time.sleep(5)


if __name__ == '__main__':
    bot_client = telegram.Bot(token=TELEGRAM_TOKEN)
    logging.basicConfig(
        level=logging.DEBUG,
        filename=__file__ + '.log',
        filemode='w',
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    main()
