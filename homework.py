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
YANDEX_HOMEWORK = 'https://praktikum.yandex.ru/api/user_api/homework_statuses/'

logging.basicConfig(
    level=logging.DEBUG,
    filename='main_program.log',
    filemode='w',
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)


def parse_homework_status(homework):
    try:
        homework_name = homework['homework_name']
        if homework['status'] == 'rejected':
            verdict = 'К сожалению в работе нашлись ошибки.'
        else:
            verdict = ('Ревьюеру всё понравилось, '
                       'можно приступать к следующему уроку.')
        return f'У вас проверили работу "{homework_name}"!\n\n{verdict}'
    except Exception as e:
        error_text = f'Have a problem with API: {e}'
        logging.error(error_text, exc_info=True)


def get_homework_statuses(current_timestamp):
    headers = {'Authorization': f'OAuth {PRAKTIKUM_TOKEN}'}
    params = {'from_date': current_timestamp}
    homework_statuses = requests.get(
        YANDEX_HOMEWORK,
        headers=headers,
        params=params
    )
    try:
        homework_statuses.raise_for_status()
    except Exception as e:
        error_text = f'Response has an exeption: {e}'
        logging.error(error_text, exc_info=True)
    return homework_statuses.json()


def send_message(message, bot_client):
    logging.info(f'Have sent a message: {message}')
    return bot_client.send_message(CHAT_ID, message)


def main():
    bot_client = telegram.Bot(token=TELEGRAM_TOKEN)
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
    main()
