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
YANDEX_HOMEWORK_URL = 'https://praktikum.yandex.ru/api/user_api/homework_statuses/'
HOMEWORK_IS_CHECKED = 'У вас проверили работу "{homework_name}"!\n\n{verdict}'
HOMEWORK_STATUS_DICTIONARY = {
    'rejected': 'К сожалению в работе нашлись ошибки.',
    'approved': ('Ревьюеру всё понравилось, '
                'можно приступать к следующему уроку.'),
}
SERVER_ERROR_KEYS = ['error', 'code']


def parse_homework_status(homework):
    homework_name = homework['homework_name']
    try:
        # Check if server gives us correct json with statuses
        status = homework['status']
        # Check if json contains expected values
        if homework['status'] not in HOMEWORK_STATUS_DICTIONARY.keys():
            raise KeyError
    except KeyError as e:
        logging.error(f'API gives an unexpected response : {e}', exc_info=True)
        raise KeyError('API gives an unexpected response')
    for status in HOMEWORK_STATUS_DICTIONARY:
        if homework['status'] == status:
            verdict = HOMEWORK_STATUS_DICTIONARY[status]
    return HOMEWORK_IS_CHECKED.format(
               homework_name=homework_name,
               verdict=verdict
           )


def get_homework_statuses(current_timestamp):
    headers = {'Authorization': f'OAuth {PRAKTIKUM_TOKEN}'}
    params = {'from_date': current_timestamp}
    try:
        response = requests.get(
            YANDEX_HOMEWORK_URL,
            headers=headers,
            params=params
        )
    except (ConnectionError, TimeoutError) as e:
        logging.error(f'Response has an exeption: {e}', exc_info=True)
        raise ConnectionError('Server doesnt work properly')
    r_json = response.json()
    print(r_json)
    # Check if server sent an error message
    for error_key in SERVER_ERROR_KEYS:
        try:
            error_message = r_json[error_key]
            raise ConnectionError
        except KeyError:
            pass
        except ConnectionError as e:
            logging.error(f'Server said that it is in trouble: {error_message}', exc_info=True)
            raise ConnectionError(f'Server said that it is in trouble: {error_message}')
    return r_json


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
                    bot_client
                )
            current_timestamp = new_homework.get(
                'current_date',
                current_timestamp
            )
            time.sleep(1200)

        except Exception as e:
            logging.error(f'Bot has faced an error: {e}', exc_info=True)
            time.sleep(5)


if __name__ == '__main__':
    bot_client = telegram.Bot(token=TELEGRAM_TOKEN)
    logging.basicConfig(
        level=logging.DEBUG,
        filename= __file__ + '.log',
        filemode='w',
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    main()
