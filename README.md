# Проект: Telegram-бот для проверки статуса домашней работы на сервисе Практикум.Домашка.

---

### Стек:
Python 3.9, python-telegram-bot, python-dotenv, requests

---

### Описание:
При обновлении статуса последней работы бот присылает уведомление в указанный чат. Логирование ведётся в stdout.

---

### Запуск бота
Создать файл **.env** с переменными окружения:

> PRACTICUM_TOKEN - токен API сервиса Практикум.Домашка
TELEGRAM_TOKEN - токен Telegram-бота
TELEGRAM_CHAT_ID - ID чата адресата оповещения

Подготовить окружение:
```
py -m 3.9 venv venv
source venv/Scripts/activate
pip install -r requirements.txt
```
Запустить скрипт:
```
python homework.py
```

---

Автор проекта: **Денис Чередниченко**