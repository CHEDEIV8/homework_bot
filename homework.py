import logging
import os
import sys
import time
from http import HTTPStatus

import requests
import telegram
from dotenv import load_dotenv

from exceptions import BadResponseStatus, EmptyElementError, TokensError

load_dotenv()


PRACTICUM_TOKEN = os.getenv('PRACTICUM_TOKEN')
TELEGRAM_TOKEN = os.getenv('TELEGRAM_TOKEN')
TELEGRAM_CHAT_ID = os.getenv('TELEGRAM_CHAT_ID')

RETRY_PERIOD = 600
ENDPOINT = 'https://practicum.yandex.ru/api/user_api/homework_statuses/123'
HEADERS = {'Authorization': f'OAuth {PRACTICUM_TOKEN}'}

PERIOD_30_DAYS = 2592000

HOMEWORK_VERDICTS = {
    'approved': 'Работа проверена: ревьюеру всё понравилось. Ура!',
    'reviewing': 'Работа взята на проверку ревьюером.',
    'rejected': 'Работа проверена: у ревьюера есть замечания.'
}


logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)
consoleHandler = logging.StreamHandler(sys.stdout)
formatter = logging.Formatter(
    '%(asctime)s, [%(levelname)s], %(message)s, %(name)s,'
    '%(funcName)s:%(lineno)d')
consoleHandler.setFormatter(formatter)
logger.addHandler(consoleHandler)


def check_tokens():
    """Проверяет доступность переменных окружения."""
    tokens = all([TELEGRAM_TOKEN, PRACTICUM_TOKEN, TELEGRAM_CHAT_ID])
    return tokens


def send_message(bot, message):
    """
    Отправляет сообщение в Telegram чат.
    Принимает на вход два параметра: экземпляр класса Bot
    и строку с текстом сообщения
    """
    try:
        logger.debug(f'Отправка собщения "{message}"')
        bot.send_message(TELEGRAM_CHAT_ID, text=message)
    except Exception as error:
        logger.error(f'Ошибка отправки сообщения. Ошибка {error}')


def get_api_answer(timestamp):
    """
    Делает запрос к единственному эндпоинту API-сервиса.
    В качестве параметра в функцию передается временная метка.
    В случае успешного запроса должна вернуть ответ API,
    приведя его из формата JSON к типам данных Python.
    """
    params = {'from_date': timestamp}
    try:
        response = requests.get(url=ENDPOINT, headers=HEADERS, params=params)
    except Exception as error:
        raise BadResponseStatus(str(error))

    if response.status_code != HTTPStatus.OK:
        raise ConnectionError(
            f'Эндпоинт не доступен. Статус {response.status_code}')

    return response.json()


def check_response(response):
    """
    Проверяет ответ API на соответствие документации.
    В качестве параметра функция получает ответ API,
    приведенный к типам данных Python.
    """
    if not isinstance(response, dict):
        raise TypeError(
            f'API передал не словарь. Переданный тип данных {type(response)}'
        )

    if 'homeworks' not in response:
        raise KeyError('В API отсутствует ключ "homeworks".')

    homeworks = response.get('homeworks')

    if not isinstance(homeworks, list):
        raise TypeError(
            'API не передает список по ключу "homeworks". '
            f'Переданный тип данных {type(homeworks)}'
        )

    if not homeworks:
        raise EmptyElementError('Cписок получаемы по ключу "homeworks" пуст')

    homework = homeworks[0]
    if not isinstance(homework, dict):
        raise TypeError(
            'Cписок полученный по ключу "homeworks", первым элементом '
            f'не передает словарь. Переданный тип данных {type(homework)}'
        )

    if not homework:
        raise EmptyElementError(
            'В полученном словаре отсутсвуют данные'
        )

    return homework


def parse_status(homework):
    """
    Извлекает из информации о конкретной домашней работе статус этой работы.
    В качестве параметра функция получает только один элемент
    из списка домашних работ.
    В случае успеха, функция возвращает подготовленную
    для отправки в Telegram строку,
    содержащую один из вердиктов словаря HOMEWORK_VERDICTS
    """
    homework_name = homework.get('homework_name')
    if 'homework_name' not in homework:
        raise KeyError('В словаре нет ключа с именем homework_name')

    homework_status = homework.get('status')
    if 'status' not in homework:
        raise KeyError('В словаре нет ключа с именем homework_status')

    verdict = HOMEWORK_VERDICTS.get(homework_status)
    if homework_status not in HOMEWORK_VERDICTS:
        raise KeyError(
            'В словаре HOMEWORK_VERDICTS нет ключа с именем homework_status')

    return f'Изменился статус проверки работы "{homework_name}". {verdict}'


def main():
    """Основная логика работы бота."""
    if check_tokens():
        logger.debug('Все токены в порядке')
    else:
        logger.critical('Отсутствует один из токенов: '
                        '[PRACTICUM_TOKEN, TELEGRAM_TOKEN, TELEGRAM_CHAT_ID]')
        raise TokensError('Отсутствует один из токенов')

    bot = telegram.Bot(token=TELEGRAM_TOKEN)
    timestamp = int(time.time()) - PERIOD_30_DAYS
    last_response_message = ''

    while True:
        try:
            response = get_api_answer(timestamp)
            homework = check_response(response)
            message = parse_status(homework)

        except Exception as error:
            message = f'Сбой в работе программы: {error}'
            logger.error(message)

        finally:
            if last_response_message != message:
                send_message(bot, message)
                last_response_message = message

            logger.debug('Отсутсвие в ответе новых статусов')

        time.sleep(3)


if __name__ == '__main__':
    main()
