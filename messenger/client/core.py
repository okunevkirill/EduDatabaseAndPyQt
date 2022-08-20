import json
import logging
import socket
import sys
import threading
import time
from typing import Optional

from PyQt5.QtCore import pyqtSignal
from PyQt5.QtWidgets import QApplication

import client.logger as log_config
import common.settings as settings
import common.utils as utils
from client.db.database import ClientDatabase
from client.gui.index import ClientMainWindow
from client.gui.namequery import NameQueryWindow
from common.errors import ServerError

# -----------------------------------------------------------------------------

LOGGER_NAME = log_config.__name__
LOGGER = logging.getLogger(LOGGER_NAME)


# -----------------------------------------------------------------------------
class ClientApp:
    signal__new_message = pyqtSignal(str)

    def __init__(self, username: Optional[str],
                 ip_address: str = settings.BASE_IP_ADDRESS, port: int = settings.BASE_PORT):
        self.username = username
        self.port = port
        self.ip_address = ip_address
        self.lock_flag = threading.Lock()

        self.database = None
        self.dialog_window = None

    def __str__(self):
        return f"{self.__class__.__name__}(username={self.username!r}, address='{self.ip_address}:{self.port!r}')"

    # -------------------------------------------------------------------------
    # Генерация сообщений
    def __get_presence_message(self) -> dict:
        result = {
            "action": settings.PRESENCE,
            "time": time.time(),
            "user": {
                "account_name": self.username,
                "status": "Yep, I am here!"
            }
        }
        LOGGER.debug(f'Сформировано сообщение присутствия от пользователя {self.username}')
        return result

    def __get_user_request_message(self):
        result = {
            settings.ACTION: settings.USERS_REQUEST,
            settings.TIME: time.time(),
            settings.ACCOUNT_NAME: self.username
        }
        LOGGER.debug(f'Сформировано сообщение запроса списка известных пользователей от {self.username}')
        return result

    # -------------------------------------------------------------------------
    def _process_server_responses(self):
        message: dict = utils.get_message(self.socket_app)

        if settings.RESPONSE in message:
            # Отработка ответа от сервера
            response_code = message.get(settings.RESPONSE)
            if response_code == 200:
                return
            elif response_code == 400:
                raise ServerError(f'{message.get(settings.ERROR) or ""}')
            else:
                LOGGER.debug(f'Принят неизвестный код подтверждения {response_code!r}')
        elif all((settings.ACTION in message, message.get(settings.ACTION) == settings.MESSAGE,
                  settings.SENDER in message, settings.DESTINATION in message,
                  settings.MESSAGE_TEXT in message, message.get(settings.DESTINATION) == self.username)):
            LOGGER.debug(
                f'Получено сообщение от пользователя {message.get(settings.SENDER)}: '
                f'{message.get(settings.MESSAGE_TEXT)}')
            self.database.save_message(
                username=message.get(settings.SENDER), direction='in',
                msg_text=message.get(settings.MESSAGE_TEXT))
            self.signal__new_message.emit(message.get(settings.SENDER))

    # -------------------------------------------------------------------------
    def show_request_username(self, app: QApplication):
        if self.username:
            return
        dialog_window = NameQueryWindow()
        app.exec_()
        if not dialog_window.is_success:
            sys.exit(0)
        self.username = dialog_window.name__edit.text()

    def show_main_window(self, app: QApplication):
        main_window = ClientMainWindow()
        main_window.setWindowTitle(f'Чат пользователя {self.username!r}')
        app.exec_()

    # -------------------------------------------------------------------------
    def _socket_connection_init(self):
        # Инициализация сокета и сообщение серверу о нашем появлении
        self.socket_app = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.socket_app.settimeout(5)  # [!] специально делаем сокет неблокируемым
        is_connected = False
        for index in range(3):
            LOGGER.info(f'Попытка подключения №{index + 1}')
            try:
                self.socket_app.connect((self.ip_address, self.port))
            except (OSError, ConnectionRefusedError):
                pass
            else:
                is_connected = True
                break
            time.sleep(1)
        if not is_connected:
            _msg = 'Не удалось установить соединение с сервером'
            LOGGER.critical(_msg)
            raise ServerError(_msg)

        LOGGER.debug('Попытка соединение с сервером')
        try:
            with self.lock_flag:
                utils.send_message(self.socket_app, self.__get_presence_message())
                self._process_server_responses()
        except (OSError, json.JSONDecodeError):
            LOGGER.critical('Потеряно соединение с сервером!')
            raise ServerError('Потеряно соединение с сервером!')

        LOGGER.info('Соединение с сервером успешно установлено.')

    def user_list_update(self):
        LOGGER.debug(f'Запрос списка известных пользователей от {self.username}')
        with self.lock_flag:
            utils.send_message(self.socket_app, self.__get_user_request_message())
            message = utils.get_message(self.socket_app)
        LOGGER.debug(f'Получен ответ: {message!r}')
        if settings.RESPONSE in message and message.get(settings.RESPONSE) == '202':
            data_list = message.get(settings.LIST_INFO, [])
            # Убираем имя текущего клиента из списка контактов
            known_users = sorted(el for el in data_list if el != self.username)
            self.database.refresh_known_users(known_users)
        else:
            LOGGER.error('Не удалось обновить список известных пользователей')

    # -------------------------------------------------------------------------
    def __work_with_server(self):
        try:
            self._socket_connection_init()
        except ServerError as err:
            LOGGER.critical(err.text)
            sys.exit(1)
        try:
            self.user_list_update()
        except TimeoutError:
            LOGGER.error('Не удалось обновить список известных пользователей')

    def run(self):
        _app = QApplication(sys.argv)
        self.show_request_username(_app)
        self.database = ClientDatabase(self.username)
        LOGGER.info('[*] Запуск клиента с именем %s', self.username)

        stream_to_server = threading.Thread(target=self.__work_with_server, args=())
        stream_to_server.daemon = True
        stream_to_server.start()

        self.show_main_window(_app)


if __name__ == '__main__':
    tt = ClientApp('kira')
    tt.run()
