import logging
import os
import time

import requests
import telegram
from dotenv import load_dotenv

load_dotenv()


PRAKTIKUM_TOKEN = os.getenv('PRAKTIKUM_TOKEN')
TELEGRAM_TOKEN = os.getenv('TELEGRAM_TOKEN')
CHAT_ID = os.getenv('TELEGRAM_CHAT_ID')
YANDEX_HOMEWORK_URL = ('https://praktikum.yandex.ru/'
                       'api/user_api/homework_statuses/')
REQUEST_HEADERS = {'Authorization': f'OAuth {PRAKTIKUM_TOKEN}'}
HOMEWORK_IS_CHECKED = 'У вас проверили работу "{homework_name}"!\n\n{verdict}'
HOMEWORK_STATUSES = {
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
LOG_SENT_MESSAGE = 'Have sent a message: {}'

bot_client = telegram.Bot(token=TELEGRAM_TOKEN)


def parse_homework_status(homework):
    status = homework['status']
    # Check if json contains expected values
    if status not in HOMEWORK_STATUSES:
        raise ValueError(
           LOG_VALUE_ERROR.format(status)
        )
    return HOMEWORK_IS_CHECKED.format(
        homework_name=homework['homework_name'],
        verdict=HOMEWORK_STATUSES[status]
    )


def get_homework_statuses(current_timestamp):
    params = {'from_date': current_timestamp}
    request_log = dict(
        url=YANDEX_HOMEWORK_URL,
        headers=REQUEST_HEADERS,
        params=params
    )
    try:
        response = requests.get(
            YANDEX_HOMEWORK_URL,
            headers=REQUEST_HEADERS,
            params=params
        )
    except requests.RequestException as error:
        raise ConnectionError(
            LOG_CONNECTION_ERROR.format(
                error=error,
                **request_log
            )
        )
    response_json = response.json()
    # Check if server sent an error message
    for error_key in ['error', 'code']:
        if error_key in response_json:
            raise ValueError(
                LOG_API_ERROR.format(
                    error=response_json[error_key],
                    **request_log
                )
            )
    return response_json


def send_message(message, bot_client):
    logging.info(LOG_SENT_MESSAGE.format(message))
    return bot_client.send_message(CHAT_ID, message)


def main():
    current_timestamp = int(time.time())
    logging.debug('Bot has launched')
    while True:
        try:
            new_homework = get_homework_statuses(0)
            if new_homework.get('homeworks'):
                send_message(
                    parse_homework_status(new_homework.get('homeworks')[0]),
                    bot_client
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
    logging.basicConfig(
        level=logging.DEBUG,
        filename=__file__ + '.log',
        filemode='w',
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    main()
