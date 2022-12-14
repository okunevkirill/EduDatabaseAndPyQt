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

from common import settings, utils
from server import logger
from server.db.database import ServerDatabase, DEFAULT_PATH_DB
from server.gui.deluser import DelUserWindow
from server.gui.index import ServerMainWindow
from server.gui.registration import RegistrationWindow
from server.gui.settings import SettingsWindow
from server.gui.statistics import StatisticsWindow

# -----------------------------------------------------------------------------
LOGGER_NAME = logger.__name__
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
        self.clients: Dict[str, Optional[socket.socket]] = dict()  # ?????????????? ???????????? ???????????????? (?????? ??????????????=??????????)
        self.messages = deque()  # ???????????? ??????????????????
        self.connections = set()  # ?????????????????? ???????????????????????? ??????????????
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
        self.window_register_user: Optional[RegistrationWindow] = None
        self.window_del_user: Optional[DelUserWindow] = None
        # ----------------------------------------
        self._init_console_parser()

    def _init_console_parser(self):
        """?????????????????? ???????????????????? ???? ??????????????"""
        parser = argparse.ArgumentParser(description='Server part of the messenger')
        parser.add_argument('-a', '--addr', dest='addr', default='', help='IP address to listen on')
        parser.add_argument('-P', '--port', dest='port', default=settings.DEFAULT_PORT, type=int,
                            help='The port the application is running on')
        self.parser_arguments = parser.parse_args()
        ip_address = self.parser_arguments.addr
        if ip_address and not utils.is_valid_ip_address(ip_address):
            raise SystemExit(
                "Invalid IP address specified. The IP address must be in the format ipv4, ipv6 or equal to ''")
        if not utils.is_valid_port(self.parser_arguments.port):
            raise SystemExit('Invalid port - the port must be in the range of registered or private')

    # -------------------------------------------------------------------------
    def presence_msg_processing(self, message: dict, client_socket: socket.socket):
        """?????????????????? ?????????????????? ?? ??????????????????????"""
        username = message.get(settings.USER).get(settings.ACCOUNT_NAME)
        if username in self.clients:
            # ???????????? ?? ?????????? ???????????? ?????? ??????????????????
            response = settings.RESPONSE_400.copy()
            response[settings.ERROR] = '?????? ???????????????????????? ????????????'
            utils.send_message_to_socket(client_socket, response)
            self.connections.discard(client_socket)
            client_socket.close()
            return
        if not self.database.is_user_registered(username):
            # ?????????????? ?????? ?? ????
            response = settings.RESPONSE_400.copy()
            response[settings.ERROR] = '???????????????????????? ???? ??????????????????????????????'
            utils.send_message_to_socket(client_socket, response)
            self.connections.discard(client_socket)
            client_socket.close()
            return
        # ???????????????? ????????????
        try:
            password_hash = message.get(settings.USER).get(settings.PASSWORD_HASH)
        except KeyError:
            password_hash = None
        self.clients[username] = client_socket
        client_ip, client_port = client_socket.getpeername()
        try:
            self.database.user_login(
                username=username, password_hash=password_hash, ip_address=client_ip, port=client_port)
        except ValueError as err:
            response = settings.RESPONSE_400.copy()
            response[settings.ERROR] = f'{err}'
            utils.send_message_to_socket(client_socket, response)
        else:
            utils.send_message_to_socket(client_socket, settings.RESPONSE_200)
            with self.lock_flag:
                self.is_connections_changed = True

    # -------------------------------------------------------------------------
    def _init_socket(self):
        LOGGER.info(f"?????????????? ????????????: '{self.ip_address}:{self.port}'")
        self.socket_app = socket.create_server((self.ip_address, self.port))
        self.socket_app.settimeout(self.TIMEOUT_BLOCKING_SOCKET)
        self.socket_app.listen(self.MAX_NUMBER_CONNECTIONS)

    def del_socket_by_username(self, username: str):
        sock = self.clients.get(username)
        if sock:
            sock.close()
            del self.clients[username]
        with self.lock_flag:
            self.is_connections_changed = True

    def _process_incoming_message(self, message: dict, client: socket.socket):
        LOGGER.debug(f'???????????? ?????????????????? ???? ?????????????? : {client.getpeername()!r}')
        # ???????? ?????? ?????????????????? ?? ?????????????????????? ???????????????? ???????????????????????? ?? ????????????????
        if all((settings.ACTION in message, message.get(settings.ACTION) == settings.PRESENCE,
                settings.TIME in message, settings.USER in message)):
            self.presence_msg_processing(message, client)
            return
        # ---------------------------------------------------------------------
        # ???????? ?????? ??????????????????, ???? ?????????????????? ?????? ?? ?????????????? ??????????????????,
        # ?????????????????? ?????????????? ?? ???????? ?? ????????????????.
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
                response[settings.ERROR] = '???????????????????????? ???? ?????????????????????????????? ???? ??????????????'
                utils.send_message_to_socket(client, response)
            return
        # ---------------------------------------------------------------------
        # ???????? ???????????? ??????????????
        if all((settings.ACTION in message, message.get(settings.ACTION) == settings.EXIT,
                settings.ACCOUNT_NAME in message,
                self.clients.get(message.get(settings.ACCOUNT_NAME)) == client)):
            LOGGER.info(f'???????????? {message[settings.ACCOUNT_NAME]} ?????????????????? ???????????????????? ???? ??????????????')
            self.database.user_logout(message[settings.ACCOUNT_NAME])
            self.connections.discard(client)
            self.del_socket_by_username(message[settings.ACCOUNT_NAME])
            return
        # ---------------------------------------------------------------------
        # ???????? ?????? ???????????? ??????????????-??????????
        if all((settings.ACTION in message, message.get(settings.ACTION) == settings.GET_CONTACTS,
                settings.USER in message, self.clients.get(message.get(settings.USER)) == client)):
            response = settings.RESPONSE_202.copy()
            response[settings.LIST_INFO] = self.database.get_contacts(message[settings.USER])
            utils.send_message_to_socket(client, response)
            return
        # ---------------------------------------------------------------------
        # ???????? ?????? ???????????????????? ????????????????
        if all((settings.ACTION in message, message.get(settings.ACTION) == settings.ADD_CONTACT,
                settings.ACCOUNT_NAME in message, settings.USER in message,
                self.clients.get(message.get(settings.USER)) == client)):
            self.database.add_contact(required_username=message[settings.USER],
                                      sender_username=message[settings.ACCOUNT_NAME])
            utils.send_message_to_socket(client, settings.RESPONSE_200)
            return
        # ---------------------------------------------------------------------
        # ???????? ?????? ???????????????? ????????????????
        if all((settings.ACTION in message, message.get(settings.ACTION) == settings.REMOVE_CONTACT,
                settings.ACCOUNT_NAME in message, settings.USER in message,
                self.clients.get(message.get(settings.USER)) == client)):
            self.database.del_contact(message[settings.USER], message[settings.ACCOUNT_NAME])
            utils.send_message_to_socket(client, settings.RESPONSE_200)
            return
        # ---------------------------------------------------------------------
        # ???????? ?????? ???????????? ?????????????????? ??????????????????????????
        if all((settings.ACTION in message, message.get(settings.ACTION) == settings.USERS_REQUEST,
                settings.ACCOUNT_NAME in message,
                self.clients.get(message.get(settings.ACCOUNT_NAME)) == client)):
            response = settings.RESPONSE_202.copy()
            response[settings.LIST_INFO] = self.database.get_list_of_usernames()
            utils.send_message_to_socket(client, response)
            return
            # ---------------------------------------------------------------------
        response = settings.RESPONSE_400.copy()
        response[settings.ERROR] = '???????????????????????? ????????????'
        utils.send_message_to_socket(client, response)

    def _process_outgoing_message(self, message: dict, listen_socks: list):
        username_to = message.get(settings.DESTINATION)
        if all((username_to in self.clients,
                self.clients.get(username_to) in listen_socks)):
            utils.send_message_to_socket(self.clients.get(username_to), message)
            LOGGER.info(f'???????????????????? ?????????????????? ???????????????????????? {message[settings.DESTINATION]} '
                        f'???? ???????????????????????? {message[settings.SENDER]}.')
        elif all((username_to in self.clients,
                  self.clients.get(username_to) not in listen_socks)):
            raise ConnectionError
        else:
            LOGGER.error(f'???????????????????????? {message[settings.DESTINATION]} '
                         f'???? ?????????????????????????????? ???? ??????????????, ???????????????? ?????????????????? ????????????????????.')

    def _run_mainloop(self):
        """???????? ???????????? ?????????????????????????????? ???????????? ?? ??????????????????"""
        while True:
            # ???????? ??????????????????????, ???????? ?????????????? ??????????, ?????????? ????????????????????.
            try:
                client_socket, address = self.socket_app.accept()
            except OSError:
                pass  # ???? ?????????????? ???????????????????????? ?? ??????????????
            else:
                LOGGER.info(f'???????????????????????? ???????????????????? ?? {address}')
                self.connections.add(client_socket)
            # ----------------------------------------
            rlist, wlist, xlist = [], [], []
            # ?????????????????? ???? ?????????????? ???????????? ????????????????
            if self.connections:
                try:
                    rlist, wlist, xlist = select.select(self.connections, self.connections, [], 0)
                except OSError as err:
                    LOGGER.error(f'???????????? ???????????? ?? ????????????????: {err}')
                    with self.lock_flag:
                        self.is_connections_changed = True
            # ----------------------------------------
            # ?????????????????? ?????????????????? ?? ???????? ????????????, ?????????????????? ??????????????.
            if rlist:
                for sock in rlist:
                    try:
                        self._process_incoming_message(
                            utils.get_message_from_socket(sock), sock)
                    except (OSError, TypeError, ValueError):
                        LOGGER.debug(f'???????????? {sock.getpeername()} ???????????????????? ???? ??????????????')
                        self.connections.discard(sock)
                        for key, value in self.clients.copy().items():
                            if value == sock:
                                del self.clients[key]
                                break
                        with self.lock_flag:
                            self.is_connections_changed = True
            # ----------------------------------------
            # ???????? ???????? ??????????????????, ???????????????????????? ????????????.
            while self.messages:
                message = self.messages.popleft()
                try:
                    self._process_outgoing_message(message, wlist)
                except (OSError, TypeError, ConnectionAbortedError,
                        ConnectionError, ConnectionResetError, ConnectionRefusedError):
                    self.clients.pop(message.to, default=None)  # ?????????????? ?????????????? ???? ?????????????? ???????????? ??????????????
                    with self.lock_flag:
                        self.is_connections_changed = True

    def work_with_clients(self):
        """?????????????? ?????????????????? ???????????????????? ?? ??????????????"""
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
        self.run_main__gui()

    # -------------------------------------------------------------------------
    def run_main__gui(self):
        """???????????? ???????????????????????? ????????????????????"""
        LOGGER.debug('???????????? ???????????????? ???????? gui')
        app = QApplication(sys.argv)
        self.window_main = ServerMainWindow(
            slot_statistic__btn=self._slot_statistic__btn__gui,
            slot_setting__btn=self._slot_setting__btn__gui,
            slot_register__btn=self._slot_register__btn__gui,
            slot_del_user__btn=self._slot_del_user__btn__gui
        )
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
        """???????? ?????????????? ???? ???????????? ?????????????? ????????????????"""
        self.window_statistic = StatisticsWindow()
        statistics = self.database.get_msg_count_info()
        self.window_statistic.fill_table(statistics)

    def _slot_setting__btn__gui(self):
        """???????? ?????????????? ???? ???????????? ?????????????????? ??????????????"""
        self.window_settings = SettingsWindow(slot_save__btn=self._slot_save__btn__gui)
        path = Path(self.db_path).resolve()
        self.window_settings.db_path__edit.setText(str(path.parent))
        self.window_settings.db_file__edit.setText(path.name)
        self.window_settings.ip_address__edit.setText(self.ip_address)
        self.window_settings.port__edit.setText(str(self.port))

    def _slot_save__btn__gui(self):
        """???????? ?????????????? ???? ???????????? ???????????????????? ?????? ???????????? ?? ?????????? ???????????????? ??????????????"""
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
                self.window_settings, '????????????',
                f'???????? ???????????? ???????? ????????????\n'
                f'?? ?????????????????? ???? {settings.MIN_ADMISSIBLE_PORT} ???? {settings.MAX_ADMISSIBLE_PORT}')
        else:
            config.set('SETTINGS', 'database_path', str(Path(dir_name, file_name).resolve()))
            config.set('SETTINGS', 'default_port', str(port))
            config.set('SETTINGS', 'listen_address', self.window_settings.ip_address__edit.text())

            with open(_PATH_TO_CONFIG, "w", encoding=settings.DEFAULT_ENCODING) as config_file:
                config.write(config_file)

    def _slot_register__btn__gui(self):
        """???????? ?????????????? ???? ???????????? ?????????????????????? ??????????????"""
        self.window_register_user = RegistrationWindow(
            slot_save__btn=self.save_new_user)

    def _slot_del_user__btn__gui(self):
        """???????? ?????????????? ???? ???????????? ???????????????? ??????????????"""
        self.window_del_user = DelUserWindow(slot_del__btn=self.delete_user)
        self.window_del_user.fill_selector__box(self.database.get_list_of_usernames())

    def save_new_user(self, username: str, password: str):
        if self.database.is_user_registered(username):
            raise ValueError('???????????????????????? ?????? ????????????????????')
        password_hash = utils.get_hash(word=password, salt=username)
        self.database.add_user(username, password_hash)

    def delete_user(self):
        message = QMessageBox()
        username = self.window_del_user.get_selected_username()
        self.database.del_user(username)
        message.information(self.window_del_user, '??????????', '???????????????????????? ????????????')
        self.del_socket_by_username(username)
        self.window_del_user.close()
