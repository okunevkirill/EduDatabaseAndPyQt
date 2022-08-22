import argparse
import json
import logging
import socket
import sys
import threading
import time
from typing import Optional

from PyQt5.QtWidgets import QApplication, QMessageBox

from client.db.database import ClientDatabase
from client.gui.addcontact import AddContactWindow
from client.gui.delcontact import DelContactWindow
from client.gui.index import ClientMainWindow
from client.gui.namequery import NameQueryWindow
from client import logger
from common import settings, utils
from common.errors import ServerError

# -----------------------------------------------------------------------------
LOGGER_NAME = logger.__name__
LOGGER = logging.getLogger(LOGGER_NAME)


class Client:
    def __init__(self):
        super().__init__()
        self.database: Optional[ClientDatabase] = None
        self.ip_address: Optional[str] = None
        self.port: Optional[int] = None
        self.username: Optional[str] = None
        self.is_connected = False
        self.app: Optional[QApplication] = None
        self.lock_flag = threading.Lock()
        # ----------------------------------------
        self.window_message: Optional[QMessageBox] = None
        self.window_main: Optional[ClientMainWindow] = None
        self.window_add_contact: Optional[AddContactWindow] = None
        self.window_del_contact: Optional[DelContactWindow] = None
        # ----------------------------------------
        self._init_console_parser()

    def _init_console_parser(self):
        """Получение параметров из консоли"""
        parser = argparse.ArgumentParser(description='Client part of the messenger')
        parser.add_argument('-a', '--addr', dest='addr', default=settings.DEFAULT_IP_ADDRESS,
                            help='IP address to listen on')
        parser.add_argument('-p', '--port', dest='port', default=settings.DEFAULT_PORT, type=int,
                            help='The port the application is running on')
        parser.add_argument('-n', '--name', dest='name', default=None, help='Client name in session')
        self.parser_arguments = parser.parse_args()
        ip_address = self.parser_arguments.addr
        if not utils.is_valid_ip_address(ip_address):
            raise SystemExit(
                'Invalid IP address specified. The IP address must be in the format ipv4, ipv6')
        if not utils.is_valid_port(self.parser_arguments.port):
            raise SystemExit('Invalid port - the port must be in the range of registered or private')

    # -------------------------------------------------------------------------
    def _init_socket(self):
        self.socket_app = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        LOGGER.info(f"Запущен клиент с параметрами: '{self.ip_address}:{self.port}', {self.username!r}")
        self.socket_app.settimeout(5)  # [!] Таймаут необходим для освобождения сокета.
        for index in range(3):
            LOGGER.info(f'Попытка подключения №{index + 1}')
            try:
                self.socket_app.connect((self.ip_address, self.port))
            except (OSError, ConnectionRefusedError):
                pass
            else:
                with self.lock_flag:
                    self.is_connected = True
                break
            time.sleep(1)
        if not self.is_connected:
            LOGGER.critical('Не удалось установить соединение с сервером')
            raise ServerError()
        LOGGER.debug('Установлено соединение с сервером')
        # Посылаем серверу приветственное сообщение и получаем ответ,
        # что всё нормально или ловим исключение.
        try:
            with self.lock_flag:
                utils.send_message_to_socket(self.socket_app, self.create_presence())
                self.process_server_ans(utils.get_message_from_socket(self.socket_app))
        except (OSError, json.JSONDecodeError):
            LOGGER.critical('Потеряно соединение с сервером')
            raise ServerError()

    def create_presence(self):
        result = {
            settings.ACTION: settings.PRESENCE,
            settings.TIME: time.time(),
            settings.USER: {
                settings.ACCOUNT_NAME: self.username
            }
        }
        LOGGER.debug(f'Сформировано приветственное сообщение от пользователя {self.username}')
        return result

    def process_server_ans(self, message: dict):
        LOGGER.debug(f'Разбор сообщения от сервера: {message}')
        # Если это подтверждение чего-либо
        if settings.RESPONSE in message:
            if message[settings.RESPONSE] == 200:
                pass
            elif message[settings.RESPONSE] == 400:
                raise ServerError(f'{message.get(settings.ERROR)}')
            else:
                LOGGER.debug(f'Принят неизвестный код подтверждения {message[settings.RESPONSE]}')
            return
        # ----------------------------------------
        # Если это сообщение от пользователя добавляем в базу, даём сигнал о новом сообщении
        if all((settings.ACTION in message, message.get(settings.ACTION) == settings.MESSAGE,
                settings.SENDER in message, settings.DESTINATION in message,
                settings.MESSAGE_TEXT in message, message.get(settings.DESTINATION) == self.username)):
            LOGGER.debug(
                f'Получено сообщение от пользователя {message[settings.SENDER]}: {message[settings.MESSAGE_TEXT]}')
        self.database.save_message(message[settings.SENDER], 'in', message[settings.MESSAGE_TEXT])

    def contacts_list_update(self):
        LOGGER.debug(f'Запрос контакт листа для пользователя {self.username}')
        message = {
            settings.ACTION: settings.GET_CONTACTS,
            settings.TIME: time.time(),
            settings.USER: self.username
        }
        LOGGER.debug(f'Сформирован запрос {message}')
        with self.lock_flag:
            utils.send_message_to_socket(self.socket_app, message)
            response = utils.get_message_from_socket(self.socket_app)
        LOGGER.debug(f'Получен ответ: {response}')
        if settings.RESPONSE in response and response.get(settings.RESPONSE) == 202:
            for username in response[settings.LIST_INFO]:
                self.database.add_contact(username)
        else:
            LOGGER.error('Не удалось обновить список контактов')

    def work_with_server(self):
        """Функция работы с сервером"""
        try:
            self._init_socket()
        except ServerError:
            self.app.quit()  # Продолжаем работу графического потока (приводит к закрытию окна)
            sys.exit(1)
        try:
            self.user_list_update()
            self.contacts_list_update()
        except OSError as err:
            if err.errno:
                LOGGER.critical(f'Потеряно соединение с сервером')
                raise ServerError()
            LOGGER.error('Timeout соединения при обновлении списков пользователей.')

    def user_list_update(self):
        LOGGER.debug(f'Запрос списка известных пользователей {self.username}')
        message = {
            settings.ACTION: settings.USERS_REQUEST,
            settings.TIME: time.time(),
            settings.ACCOUNT_NAME: self.username
        }
        with self.lock_flag:
            utils.send_message_to_socket(self.socket_app, message)
            response = utils.get_message_from_socket(self.socket_app)
        if settings.RESPONSE in response and response.get(settings.RESPONSE) == 202:
            self.database.refresh_known_users(response.get(settings.LIST_INFO))
        else:
            LOGGER.error('Не удалось обновить список известных пользователей')

    # -------------------------------------------------------------------------
    def run(self):
        self.app = QApplication(sys.argv)
        self.ip_address, self.port, self.username = (
            self.parser_arguments.addr, self.parser_arguments.port, self.parser_arguments.name)
        if not self.username:
            self.run_name_query__gui()
        self.database = ClientDatabase(username=self.username)

        stream_for_server = threading.Thread(target=self.work_with_server)
        stream_for_server.daemon = True
        stream_for_server.start()
        self.run_main__gui()
        # ToDo поставить отправку сообщения об отключении

    # -------------------------------------------------------------------------
    # Методы работы с графическим интерфейсом
    def run_name_query__gui(self):
        window = NameQueryWindow()
        self.app.exec_()
        if not window.is_success:
            sys.exit(0)
        self.username = window.name__edit.text().strip()

    def run_main__gui(self):
        LOGGER.debug('Запуск главного окна gui')
        self.window_main = ClientMainWindow(
            slot_add_contact=self._slot_add_contact__gui,
            slot_del_contact=self._slot_del_contact__gui,
            slot_send_msg=self._slot_send_msg__gui,
            slot_active_contact=self._slot_active_contact__gui)
        self.window_main.setWindowTitle(f'Чат пользователя {self.username!r}')
        self.app.exec_()

    def _slot_add_contact__gui(self):
        print('Нажали Добавить контакт')

    def _slot_del_contact__gui(self):
        print('Нажали Удалить контакт')

    def _slot_send_msg__gui(self):
        print('Нажали Отправить сообщение')

    def _slot_active_contact__gui(self):
        print('Активировали контакт')
