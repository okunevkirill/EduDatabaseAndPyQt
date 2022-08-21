import argparse
import configparser
import logging
import select
import socket
import sys
import threading
from collections import deque
from pathlib import Path
from typing import Dict, Optional

from PyQt5.QtCore import QTimer
from PyQt5.QtWidgets import QApplication, QMessageBox

import common.utils as utils
import common.settings as settings
import server.logger as log_config
# from common.settings import (
#     DEFAULT_PORT, DEFAULT_ENCODING, MIN_ADMISSIBLE_PORT, MAX_ADMISSIBLE_PORT,
# )
from server.db.database import ServerDatabase, DEFAULT_PATH_DB
from server.gui.index import ServerMainWindow
from server.gui.settings import SettingsWindow
from server.gui.statistics import StatisticsWindow

# -----------------------------------------------------------------------------
LOGGER_NAME = log_config.__name__
LOGGER = logging.getLogger(LOGGER_NAME)
_PATH_TO_CONFIG = Path(__file__).resolve().parent / 'config.ini'


# -----------------------------------------------------------------------------

def get_data_from_config(default_ip_address, default_port, default_db_path):
    path = _PATH_TO_CONFIG
    if not path.exists():
        return default_ip_address, default_port, default_db_path
    config = configparser.ConfigParser()
    config.read(str(path), encoding=settings.DEFAULT_ENCODING)
    try:
        ip_address = config['SETTINGS']['listen_address']
        if ip_address and not utils.is_valid_ip_address(ip_address):
            raise KeyError
    except KeyError:
        ip_address = default_ip_address
    try:
        port = config['SETTINGS']['default_port']
        if not utils.is_valid_port(port):
            raise KeyError
    except KeyError:
        port = default_port
    try:
        db_path = config['SETTINGS']['database_path']
    except KeyError:
        db_path = default_db_path
    return ip_address, int(port), db_path


# -----------------------------------------------------------------------------
class Server:
    MAX_NUMBER_CONNECTIONS = 0
    TIMEOUT_BLOCKING_SOCKET = 0.5

    def __init__(self):
        self.clients: Dict[str, Optional[socket.socket]] = dict()  # Словарь данных клиентов (имя клиента=сокет)
        self.messages = deque()  # Список сообщений
        self.connections = set()  # множество подключенных сокетов
        # ----------------------------------------
        self.db_path: Optional[str] = None
        self.ip_address: Optional[str] = None
        self.port: Optional[int] = None
        self.database: Optional[ServerDatabase] = None
        self.is_connections_changed = False
        self.lock_flag = threading.Lock()
        # ----------------------------------------
        self.window_main: Optional[ServerMainWindow] = None
        self.window_statistic: Optional[StatisticsWindow] = None
        self.window_settings: Optional[SettingsWindow] = None
        # ----------------------------------------
        self._init_console_parser()

    def _init_console_parser(self):
        """Получение параметров из консоли"""
        parser = argparse.ArgumentParser(description='Server part of the messenger')
        parser.add_argument('-a', '--addr', dest='addr', default='', help='IP address to listen on')
        parser.add_argument('-p', '--port', dest='port', default=settings.DEFAULT_PORT, type=int,
                            help='The port the application is running on')
        self.parser_arguments = parser.parse_args()
        ip_address = self.parser_arguments.addr
        if ip_address and not utils.is_valid_ip_address(ip_address):
            raise SystemExit(
                "Invalid IP address specified. The IP address must be in the format ipv4, ipv6 or equal to ''")
        if not utils.is_valid_port(self.parser_arguments.port):
            raise SystemExit('Invalid port - the port must be in the range of registered or private')

    # -------------------------------------------------------------------------
    def _init_socket(self):
        LOGGER.info(f"Запущен сервер: '{self.ip_address}:{self.port}'")
        self.socket_app = socket.create_server((self.ip_address, self.port))
        self.socket_app.settimeout(self.TIMEOUT_BLOCKING_SOCKET)
        self.socket_app.listen(self.MAX_NUMBER_CONNECTIONS)

    def _process_incoming_message(self, message: dict, client: socket.socket):
        LOGGER.debug(f'Разбор сообщения от клиента : {client.getpeername()!r}')
        # Если это сообщение о присутствии, принимаем и отвечаем
        if all((settings.ACTION in message, message.get(settings.ACTION) == settings.PRESENCE,
                settings.TIME in message, settings.USER in message)):
            # Если такой пользователь ещё не зарегистрирован, регистрируем,
            # иначе отправляем ответ и завершаем соединение.
            username = message.get(settings.USER).get(settings.ACCOUNT_NAME)
            if username not in self.clients:
                self.clients[username] = client
                client_ip, client_port = client.getpeername()
                self.database.user_login(username=username, ip_address=client_ip, port=client_port)
                utils.send_message_to_socket(client, settings.RESPONSE_200)
                with self.lock_flag:
                    self.is_connections_changed = True
            else:
                response = settings.RESPONSE_400.copy()
                response[settings.ERROR] = 'Имя пользователя занято'
                utils.send_message_to_socket(client, response)
                self.connections.discard(client)
                client.close()
            return
        # ---------------------------------------------------------------------
        # Если это сообщение, то добавляем его в очередь сообщений,
        # проверяем наличие в сети и отвечаем.
        if all((settings.ACTION in message, message.get(settings.ACTION) == settings.MESSAGE,
                settings.DESTINATION in message, settings.TIME in message,
                settings.SENDER in message, settings.MESSAGE_TEXT in message,
                self.clients.get(message.get(settings.SENDER)) == client)):
            if message.get(settings.DESTINATION) in self.clients:
                self.messages.append(message)
                self.database.msg_registration(message[settings.SENDER], message[settings.DESTINATION])
                utils.send_message_to_socket(client, settings.RESPONSE_200)
            else:
                response = settings.RESPONSE_400.copy()
                response[settings.ERROR] = 'Пользователь не зарегистрирован на сервере'
                utils.send_message_to_socket(client, response)
            return
        # ---------------------------------------------------------------------
        # Если клиент выходит
        if all((settings.ACTION in message, message.get(settings.ACTION) == settings.EXIT,
                settings.ACCOUNT_NAME in message,
                self.clients.get(message.get(settings.ACCOUNT_NAME)) == client)):
            LOGGER.info(f'Клиент {message[settings.ACCOUNT_NAME]} корректно отключился от сервера')
            self.database.user_logout(message[settings.ACCOUNT_NAME])
            self.connections.discard(client)
            sock = self.clients.get(message[settings.ACCOUNT_NAME])
            if sock:
                sock.close()
                del self.clients[message[settings.ACCOUNT_NAME]]
            with self.lock_flag:
                self.is_connections_changed = True
            return
        # ---------------------------------------------------------------------
        # Если это запрос контакт-листа
        if all((settings.ACTION in message, message.get(settings.ACTION) == settings.GET_CONTACTS,
                settings.USER in message, self.clients.get(message.get(settings.USER)) == client)):
            response = settings.RESPONSE_202.copy()
            response[settings.LIST_INFO] = self.database.get_contacts(message[settings.USER])
            utils.send_message_to_socket(client, response)
            return
        # ---------------------------------------------------------------------
        # Если это добавление контакта
        if all((settings.ACTION in message, message.get(settings.ACTION) == settings.ADD_CONTACT,
                settings.ACCOUNT_NAME in message, settings.USER in message,
                self.clients.get(message.get(settings.USER)) == client)):
            self.database.add_contact(required_username=message[settings.USER],
                                      sender_username=message[settings.ACCOUNT_NAME])
            utils.send_message_to_socket(client, settings.RESPONSE_200)
            return
        # ---------------------------------------------------------------------
        # Если это удаление контакта
        if all((settings.ACTION in message, message.get(settings.ACTION) == settings.REMOVE_CONTACT,
                settings.ACCOUNT_NAME in message, settings.USER in message,
                self.clients.get(message.get(settings.USER)) == client)):
            self.database.del_contact(message[settings.USER], message[settings.ACCOUNT_NAME])
            utils.send_message_to_socket(client, settings.RESPONSE_200)
            return
        # ---------------------------------------------------------------------
        # Если это запрос известных пользователей
        if all((settings.ACTION in message, message.get(settings.ACTION) == settings.USERS_REQUEST,
                settings.ACCOUNT_NAME in message,
                self.clients.get(message.get(settings.ACCOUNT_NAME)) == client)):
            response = settings.RESPONSE_202.copy()
            response[settings.LIST_INFO] = self.database.get_list_of_usernames()
            utils.send_message_to_socket(client, response)
            return
            # ---------------------------------------------------------------------
        response = settings.RESPONSE_400.copy()
        response[settings.ERROR] = 'Некорректный запрос'
        utils.send_message_to_socket(client, response)

    def _process_outgoing_message(self, message: dict, listen_socks: list):
        username_to = message.get(settings.DESTINATION)
        if all((username_to in self.clients,
                self.clients.get(username_to) in listen_socks)):
            utils.send_message_to_socket(self.clients.get(username_to), message)
            LOGGER.info(f'Отправлено сообщение пользователю {message[settings.DESTINATION]} '
                        f'от пользователя {message[settings.SENDER]}.')
        elif all((username_to in self.clients,
                  self.clients.get(username_to) not in listen_socks)):
            raise ConnectionError
        else:
            LOGGER.error(f'Пользователь {message[settings.DESTINATION]} '
                         f'не зарегистрирован на сервере, отправка сообщения невозможна.')

    def _run_mainloop(self):
        """Цикл работы прослушиваемого сокета с клиентами"""
        while True:
            # Ждём подключения, если таймаут вышел, ловим исключение.
            try:
                client_socket, address = self.socket_app.accept()
            except OSError:
                pass  # не удалось подключиться к клиенту
            else:
                LOGGER.info(f'Установленно соединение с {address}')
                self.connections.add(client_socket)
            # ----------------------------------------
            rlist, wlist, xlist = [], [], []
            # Проверяем на наличие ждущих клиентов
            if self.connections:
                try:
                    rlist, wlist, xlist = select.select(self.connections, self.connections, [], 0)
                except OSError as err:
                    LOGGER.error(f'Ошибка работы с сокетами: {err}')
                    with self.lock_flag:
                        self.is_connections_changed = True
            # ----------------------------------------
            # принимаем сообщения и если ошибка, исключаем клиента.
            if rlist:
                for sock in rlist:
                    try:
                        self._process_incoming_message(
                            utils.get_message_from_socket(sock), sock)
                    except (OSError, TypeError, ValueError):
                        LOGGER.debug(f'Клиент {sock.getpeername()} отключился от сервера')
                        self.connections.discard(sock)
                        for key, value in self.clients.copy().items():
                            if value == sock:
                                del self.clients[key]
                                break
                        with self.lock_flag:
                            self.is_connections_changed = True
            # ----------------------------------------
            # Если есть сообщения, обрабатываем каждое.
            while self.messages:
                message = self.messages.popleft()
                try:
                    self._process_outgoing_message(message, wlist)
                except (OSError, TypeError, ConnectionAbortedError,
                        ConnectionError, ConnectionResetError, ConnectionRefusedError):
                    self.clients.pop(message.to, default=None)  # Удаляем клиента из словаря данных клиента
                    with self.lock_flag:
                        self.is_connections_changed = True

    def work_with_clients(self):
        """Функция обработки соединений к серверу"""
        self._init_socket()
        self._run_mainloop()

    # -------------------------------------------------------------------------
    def run(self):
        ip_address, port, db_path = get_data_from_config(
            self.parser_arguments.addr, self.parser_arguments.port, DEFAULT_PATH_DB)
        self.ip_address, self.port, self.db_path = ip_address, port, db_path
        self.database = ServerDatabase(path=db_path)

        stream_for_clients = threading.Thread(target=self.work_with_clients)
        stream_for_clients.daemon = True
        stream_for_clients.start()
        LOGGER.debug('Запуск графического интерфейса')
        self.run__gui()

    # -------------------------------------------------------------------------
    # Методы работы с графическим интерфейсом
    def run__gui(self):
        """Запуск графического интерфейса"""
        app = QApplication(sys.argv)
        self.window_main = ServerMainWindow(
            slot_statistic__btn=self._slot_statistic__btn__gui,
            slot_setting__btn=self._slot_setting__btn__gui)
        self.window_main.statusBar().showMessage('Server Working')

        timer = QTimer()
        timer.timeout.connect(self._update_active_users__gui)
        timer.start(1000)
        app.exec_()

    def _update_active_users__gui(self):
        if not self.is_connections_changed:
            return
        active_users = self.database.get_active_users()
        self.window_main.fill_table(active_users)
        with self.lock_flag:
            self.is_connections_changed = False

    def _slot_statistic__btn__gui(self):
        """Слот нажатия на кнопку истории клиентов"""
        self.window_statistic = StatisticsWindow()
        statistics = self.database.get_msg_count_info()
        self.window_statistic.fill_table(statistics)

    def _slot_setting__btn__gui(self):
        """Слот нажатия на кнопку настройки сервера"""
        self.window_settings = SettingsWindow(slot_save__btn=self._slot_save__btn__gui)
        path = Path(self.db_path).resolve()
        self.window_settings.db_path__edit.setText(str(path.parent))
        self.window_settings.db_file__edit.setText(path.name)
        self.window_settings.ip_address__edit.setText(self.ip_address)
        self.window_settings.port__edit.setText(str(self.port))

    def _slot_save__btn__gui(self):
        """Слот нажатия на кнопку сохранения при работе с окном настроек сервера"""
        message = QMessageBox()
        dir_name = self.window_settings.db_path__edit.text()
        file_name = self.window_settings.db_file__edit.text()
        config = configparser.ConfigParser()
        config.add_section('SETTINGS')
        try:
            port = int(self.window_settings.port__edit.text())
            if not (settings.MIN_ADMISSIBLE_PORT <= port < settings.MAX_ADMISSIBLE_PORT):
                raise ValueError
        except ValueError:
            message.warning(
                self.window_settings, 'Ошибка',
                f'Порт должен быть числом\n'
                f'в диапазоне от {settings.MIN_ADMISSIBLE_PORT} до {settings.MAX_ADMISSIBLE_PORT}')
        else:
            config.set('SETTINGS', 'database_path', str(Path(dir_name, file_name).resolve()))
            config.set('SETTINGS', 'default_port', str(port))
            config.set('SETTINGS', 'listen_address', self.window_settings.ip_address__edit.text())

            with open(_PATH_TO_CONFIG, "w", encoding=settings.DEFAULT_ENCODING) as config_file:
                config.write(config_file)
