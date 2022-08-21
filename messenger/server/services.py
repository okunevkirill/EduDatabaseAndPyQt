import argparse
import configparser
import socket
import sys
import threading
from collections import deque
from pathlib import Path
from typing import Dict, Optional

from PyQt5.QtCore import QTimer
from PyQt5.QtWidgets import QApplication, QMessageBox

import common.utils as utils
from common.settings import (
    DEFAULT_PORT, DEFAULT_ENCODING, MIN_ADMISSIBLE_PORT, MAX_ADMISSIBLE_PORT,
)
from server.db.database import ServerDatabase, DEFAULT_PATH_DB
from server.gui.index import ServerMainWindow
from server.gui.settings import SettingsWindow
from server.gui.statistics import StatisticsWindow

_PATH_TO_CONFIG = Path(__file__).resolve().parent / 'config.ini'


def get_data_from_config(default_ip_address, default_port, default_db_path):
    path = _PATH_TO_CONFIG
    if not path.exists():
        return default_ip_address, default_port, default_db_path
    config = configparser.ConfigParser()
    config.read(str(path), encoding=DEFAULT_ENCODING)
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
        parser.add_argument('-p', '--port', dest='port', default=DEFAULT_PORT, type=int,
                            help='The port the application is running on')
        self.parser_arguments = parser.parse_args()
        ip_address = self.parser_arguments.addr
        if ip_address and not utils.is_valid_ip_address(ip_address):
            raise SystemExit(
                "Invalid IP address specified. The IP address must be in the format ipv4, ipv6 or equal to ''")
        if not utils.is_valid_port(self.parser_arguments.port):
            raise SystemExit('Invalid port - the port must be in the range of registered or private')

    # -------------------------------------------------------------------------
    def _work_with_clients(self):
        """Функция обработки соединений к серверу"""
        pass

    # -------------------------------------------------------------------------
    def run(self):
        ip_address, port, db_path = get_data_from_config(
            self.parser_arguments.addr, self.parser_arguments.port, DEFAULT_PATH_DB)
        self.ip_address, self.port, self.db_path = ip_address, port, db_path
        self.database = ServerDatabase(path=db_path)

        stream_for_clients = threading.Thread(target=self._work_with_clients)
        stream_for_clients.daemon = True
        stream_for_clients.start()
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
            if not (MIN_ADMISSIBLE_PORT <= port < MAX_ADMISSIBLE_PORT):
                raise ValueError
        except ValueError:
            message.warning(
                self.window_settings, 'Ошибка',
                f'Порт должен быть числом\nв диапазоне от {MIN_ADMISSIBLE_PORT} до {MAX_ADMISSIBLE_PORT}')
        else:
            config.set('SETTINGS', 'database_path', str(Path(dir_name, file_name).resolve()))
            config.set('SETTINGS', 'default_port', str(port))
            config.set('SETTINGS', 'listen_address', self.window_settings.ip_address__edit.text())

            with open(_PATH_TO_CONFIG, "w", encoding=DEFAULT_ENCODING) as config_file:
                config.write(config_file)
