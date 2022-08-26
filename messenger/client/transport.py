import json
import socket
import time
import logging
import threading
from PyQt5.QtCore import pyqtSignal, QObject

from client.db.database import ClientDatabase
from client import logger
from common import settings, utils
from common.errors import ServerError

LOGGER_NAME = logger.__name__
LOGGER = logging.getLogger(LOGGER_NAME)


class ClientTransport(threading.Thread, QObject):
    new_message = pyqtSignal(str)
    connection_lost = pyqtSignal()

    def __init__(self, port, ip_address, username, password, database: ClientDatabase):
        threading.Thread.__init__(self)
        QObject.__init__(self)

        self.database = database
        self.username = username
        self.password_hash = utils.get_hash(password, username)
        self.transport = None
        self.log_flag = threading.Lock()
        self.connection_init(port, ip_address)
        # Обновляем таблицы известных пользователей и контактов
        try:
            self.user_list_update()
            self.contacts_list_update()
        except OSError as err:
            if err.errno:
                msg = 'Потеряно соединение с сервером'
                LOGGER.critical(msg)
                raise ServerError(msg)
            LOGGER.error('Timeout соединения при обновлении списков пользователей.')
        except json.JSONDecodeError:
            msg = 'Потеряно соединение с сервером'
            LOGGER.critical(msg)
            raise ServerError(msg)
        self.running = True

    # Функция инициализации соединения с сервером
    def connection_init(self, port, ip):
        self.transport = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.transport.settimeout(5)
        connected = False
        for index in range(3):
            LOGGER.info(f'Попытка подключения №{index + 1}')
            try:
                self.transport.connect((ip, port))
            except (OSError, ConnectionRefusedError):
                pass
            else:
                connected = True
                break
            time.sleep(1)

        if not connected:
            msg = 'Не удалось установить соединение с сервером'
            LOGGER.critical(msg)
            raise ServerError(msg)
        LOGGER.debug('Установлено соединение с сервером')

        # Посылаем серверу приветственное сообщение и получаем ответ,
        # что всё нормально или ловим исключение.
        try:
            with self.log_flag:
                utils.send_message_to_socket(self.transport, self.create_presence())
                self.process_server_ans(utils.get_message_from_socket(self.transport))
        except (OSError, json.JSONDecodeError):
            msg = 'Потеряно соединение с сервером'
            LOGGER.critical(msg)
            raise ServerError(msg)

        # Если всё хорошо, сообщение об установке соединения.
        LOGGER.info('Соединение с сервером успешно установлено.')

    # Функция, генерирующая приветственное сообщение для сервера
    def create_presence(self):
        out = {
            settings.ACTION: settings.PRESENCE,
            settings.TIME: time.time(),
            settings.USER: {
                settings.ACCOUNT_NAME: self.username,
                settings.PASSWORD_HASH: self.password_hash
            }
        }
        LOGGER.debug(f'Сформировано {settings.PRESENCE} сообщение для пользователя {self.username}')
        return out

    def process_server_ans(self, message):
        LOGGER.debug(f'Разбор сообщения от сервера: {message}')

        # Если это подтверждение чего-либо
        if settings.RESPONSE in message:
            if message[settings.RESPONSE] == 200:
                return
            elif message[settings.RESPONSE] == 400:
                raise ServerError(f'{message[settings.ERROR]}')
            else:
                LOGGER.debug(f'Принят неизвестный код подтверждения {message[settings.RESPONSE]}')

        # Если это сообщение от пользователя добавляем в базу, даём сигнал о новом сообщении
        elif settings.ACTION in message \
                and message[settings.ACTION] == settings.MESSAGE \
                and settings.SENDER in message \
                and settings.DESTINATION in message \
                and settings.MESSAGE_TEXT in message \
                and message[settings.DESTINATION] == self.username:
            LOGGER.debug(f'Получено сообщение от пользователя {message[settings.SENDER]}:'
                         f'{message[settings.MESSAGE_TEXT]}')
            self.database.save_message(message[settings.SENDER], 'in', message[settings.MESSAGE_TEXT])
            self.new_message.emit(message[settings.SENDER])

    # Функция, обновляющая контакт - лист с сервера
    def contacts_list_update(self):
        LOGGER.debug(f'Запрос контакт листа для пользователя {self.name}')
        req = {
            settings.ACTION: settings.GET_CONTACTS,
            settings.TIME: time.time(),
            settings.USER: self.username
        }
        LOGGER.debug(f'Сформирован запрос {req}')
        with self.log_flag:
            utils.send_message_to_socket(self.transport, req)
            ans = utils.get_message_from_socket(self.transport)
        LOGGER.debug(f'Получен ответ {ans}')
        if settings.RESPONSE in ans and ans[settings.RESPONSE] == 202:
            for contact in ans[settings.LIST_INFO]:
                self.database.add_contact(contact)
        else:
            LOGGER.error('Не удалось обновить список контактов.')

    # Функция обновления таблицы известных пользователей.
    def user_list_update(self):
        LOGGER.debug(f'Запрос списка известных пользователей {self.username}')
        req = {
            settings.ACTION: settings.USERS_REQUEST,
            settings.TIME: time.time(),
            settings.ACCOUNT_NAME: self.username
        }
        with self.log_flag:
            utils.send_message_to_socket(self.transport, req)
            ans = utils.get_message_from_socket(self.transport)
        if settings.RESPONSE in ans and ans[settings.RESPONSE] == 202:
            self.database.refresh_known_users(ans[settings.LIST_INFO])
        else:
            LOGGER.error('Не удалось обновить список известных пользователей.')

    # Функция сообщающая на сервер о добавлении нового контакта
    def add_contact(self, contact):
        LOGGER.debug(f'Создание контакта {contact}')
        req = {
            settings.ACTION: settings.ADD_CONTACT,
            settings.TIME: time.time(),
            settings.USER: self.username,
            settings.ACCOUNT_NAME: contact
        }
        with self.log_flag:
            utils.send_message_to_socket(self.transport, req)
            self.process_server_ans(utils.get_message_from_socket(self.transport))

    # Функция удаления клиента на сервере
    def remove_contact(self, contact):
        LOGGER.debug(f'Удаление контакта {contact}')
        req = {
            settings.ACTION: settings.REMOVE_CONTACT,
            settings.TIME: time.time(),
            settings.USER: self.username,
            settings.ACCOUNT_NAME: contact
        }
        with self.log_flag:
            utils.send_message_to_socket(self.transport, req)
            self.process_server_ans(utils.get_message_from_socket(self.transport))

    # Функция закрытия соединения, отправляет сообщение о выходе.
    def transport_shutdown(self):
        self.running = False
        message = {
            settings.ACTION: settings.EXIT,
            settings.TIME: time.time(),
            settings.ACCOUNT_NAME: self.username
        }
        with self.log_flag:
            try:
                utils.send_message_to_socket(self.transport, message)
            except OSError:
                pass
        LOGGER.debug('Транспорт завершает работу.')
        time.sleep(0.5)

    # Функция отправки сообщения на сервер
    def send_message(self, to, message):
        message_dict = {
            settings.ACTION: settings.MESSAGE,
            settings.SENDER: self.username,
            settings.DESTINATION: to,
            settings.TIME: time.time(),
            settings.MESSAGE_TEXT: message
        }
        LOGGER.debug(f'Сформирован словарь сообщения: {message_dict}')

        # Необходимо дождаться освобождения сокета для отправки сообщения
        with self.log_flag:
            utils.send_message_to_socket(self.transport, message_dict)
            self.process_server_ans(utils.get_message_from_socket(self.transport))
            LOGGER.info(f'Отправлено сообщение для пользователя {to}')

    def run(self):
        LOGGER.debug('Запущен процесс - приёмник сообщений с сервера.')
        while self.running:
            # Отдыхаем секунду и снова пробуем захватить сокет. Если не сделать тут задержку,
            # то отправка может достаточно долго ждать освобождения сокета.
            time.sleep(1)
            with self.log_flag:
                try:
                    self.transport.settimeout(0.5)
                    message = utils.get_message_from_socket(self.transport)
                except OSError as err:
                    if err.errno:
                        # выход по таймауту вернёт номер ошибки err.errno равный None
                        # поэтому, при выходе по таймауту мы сюда попросту не попадём
                        LOGGER.critical(f'Потеряно соединение с сервером.')
                        self.running = False
                        self.connection_lost.emit()
                # Проблемы с соединением
                except (ConnectionError, ConnectionAbortedError,
                        ConnectionResetError, json.JSONDecodeError, TypeError):
                    LOGGER.debug(f'Потеряно соединение с сервером.')
                    self.running = False
                    self.connection_lost.emit()
                # Если сообщение получено, то вызываем функцию обработчик:
                else:
                    LOGGER.debug(f'Принято сообщение с сервера: {message}')
                    self.process_server_ans(message)
                finally:
                    self.transport.settimeout(5)
