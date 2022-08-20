import configparser
import logging
import select
import socket
import sys
import threading
from collections import deque
from datetime import datetime
from pathlib import Path
from typing import Dict, Optional

from PyQt5.QtCore import QTimer
from PyQt5.QtWidgets import QApplication, QMessageBox

import app_logging.etc.server_log_config as log_config
import common.settings as settings
from db.database import engine_server, SessionServer, ServerBase
from db.models import User, Connection, LoginHistory
from gui.windows import ServerMainWindow, StatisticsWindow, SettingsWindow
from kernel.base import Message, BaseApplication, MessageType
from app_logging.decorators import LogCalls

from kernel.config import NAME_CONFIG_FILE, BASE_ENCODING, DEFAULT_NAME_SERVER_DB, BASE_PORT

# -----------------------------------------------------------------------------
LOGGER_NAME = log_config.__name__
LOGGER = logging.getLogger(LOGGER_NAME)


# -----------------------------------------------------------------------------
class Storage:
    def __init__(self):
        self.session = SessionServer()
        ServerBase.metadata.create_all(engine_server)

    def get_users(self):
        return self.session.query(User).all()

    def get_connections(self):
        return self.session.query(Connection).all()

    def get_connections_asdict(self):
        connections = self.get_connections()
        return [
            {'username': el.user.username,
             'ip_address': str(el.ip_address),
             'port': str(el.port),
             'connection_time': str(el.connection_time)}
            for el in connections
        ]

    def get_login_history(self, username: str = ''):
        if username:
            user: User = self.session.query(User).filter_by(username=username).first()
            return self.session.query(LoginHistory).filter_by(user_id=user.id)
        return self.session.query(LoginHistory).all()

    def get_user_statistics_asdict(self):
        users = self.get_users()
        return [
            {'username': el.username, 'last_login_time': str(el.last_login_time),
             'sent': str(el.sent), 'received': str(el.received)}
            for el in users
        ]

    def add_connect(self, username, ip_address, port):
        user: User = self.session.query(User).filter_by(username=username).first()
        if user:
            user.last_login_time = datetime.now()
        else:
            user = User(username=username)
            self.session.add(user)
            self.session.commit()

        self.session.add(
            Connection(user_id=user.id, ip_address=ip_address, port=port))
        self.session.add(
            LoginHistory(user_id=user.id, ip_address=ip_address, port=port))
        self.session.commit()

    def delete_connect(self, username):
        user: User = self.session.query(User).filter_by(username=username).first()
        self.session.query(Connection).filter_by(user_id=user.id).delete()
        self.session.commit()

    def get_contacts(self, username: str):
        user = self.session.query(User).filter_by(username=username).first()
        if not user:
            return []
        return [
            self.session.query(User.username).filter_by(id=el.to_user_id).first()[0]
            for el in user.contacts]


class MessengerServer(BaseApplication):
    MAX_NUMBER_CONNECTIONS = 0
    TIMEOUT_BLOCKING_SOCKET = 0.5

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.clients_app: Dict[str, Optional[socket.socket]] = dict()  # Словарь данных клиентов (имя клиента=сокет)
        self.messages_app = deque()  # Список сообщений
        self.connections = set()  # множество подключенных сокетов
        # ------------------------------
        self.parser.description = "Server part of a simple messenger"
        self.parser.set_defaults(addr='')  # Устанавливаем для прослушивания сокетом всех доступных адресов ip
        # ------------------------------
        self.is_connections_changed = False
        self.lock_flag = threading.Lock()
        # ------------------------------
        self.window_main = None
        self.window_statistics = None
        self.window_settings = None
        # ------------------------------
        self.config_file = Path(__file__).resolve().parent / NAME_CONFIG_FILE
        self.database = Storage()

    def _send_contacts(self, sock, username):
        data = {
            "response": "202",
            "alert": self.database.get_contacts(username)
        }
        self.send_data_to_socket(sock, data_object=data)

    def _send_active_users(self, sock, username):
        data = {
            settings.RESPONSE: "202",
            settings.LIST_INFO: [el.username for el in self.database.get_users()]
        }
        self.send_data_to_socket(sock, data_object=data)

    def __process_incoming_message(self, sock: socket.socket) -> None:
        data = self.get_socket_data(sock)
        _action = data.get("action")
        if _action == MessageType.PRESENCE.value:
            # Если это сообщение о присутствии, принимаем и отвечаем
            username_to = data["user"]["account_name"]
            if username_to not in self.clients_app:
                self.clients_app[username_to] = sock
                self.send_data_to_socket(sock, data_object={"response": 200})
                client_ip, client_port = sock.getpeername()
                self.database.add_connect(
                    username=username_to, ip_address=client_ip, port=client_port)
                with self.lock_flag:
                    self.is_connections_changed = True
            else:
                self.send_data_to_socket(sock, data_object={"response": 400, "error": "Name already taken"})
                self.connections.discard(sock)
                sock.close()
        elif _action == MessageType.MESSAGE.value:
            # Если это сообщение, то добавляем его в очередь сообщений.
            self.messages_app.append(Message(**data))
        elif _action == MessageType.EXIT.value:
            self.database.delete_connect(data.get("account_name"))
            with self.lock_flag:
                self.is_connections_changed = True
        elif _action == MessageType.CONTACTS.value:
            username_to = data["account_name"]
            self._send_contacts(sock, username=username_to)
        elif _action == settings.USERS_REQUEST:
            username_to = data.get(settings.ACCOUNT_NAME)
            self._send_active_users(sock, username=username_to)

    def __process_outgoing_message(self, message: Message, wlist: list) -> None:
        if message.to == message.sender or self.clients_app.get(message.to) not in wlist:
            return
        sock = self.clients_app.get(message.to)
        self.send_data_to_socket(sock, data_object=message._asdict())

    def __connection_handling(self):

        while True:
            try:
                client_socket, address = self.socket_app.accept()
            except OSError:
                pass  # не удалось подключиться к клиенту
            else:
                LOGGER.debug(f"Connecting a client with an address {address}")
                self.connections.add(client_socket)
            # ------------------------------
            # Проверяем на наличие ждущих клиентов
            rlist, wlist, xlist = [], [], []
            if self.connections:
                try:
                    rlist, wlist, xlist = select.select(self.connections, self.connections, [], 0)
                except OSError:
                    # разрыв соединения с клиентом
                    with self.lock_flag:
                        self.is_connections_changed = True
            # ------------------------------
            # принимаем сообщения и если ошибка, исключаем клиента.
            if rlist:
                for sock in rlist:
                    try:
                        self.__process_incoming_message(sock)
                    except (OSError, TypeError, ValueError):
                        LOGGER.debug(f"Client {sock.getpeername()} disconnected from server")
                        self.connections.discard(sock)
                        for key, value in self.clients_app.copy().items():
                            if value == sock:
                                del self.clients_app[key]
                        with self.lock_flag:
                            self.is_connections_changed = True

            # ------------------------------
            # Если есть сообщения, обрабатываем каждое.
            while self.messages_app:
                message: Message = self.messages_app.popleft()
                try:
                    self.__process_outgoing_message(message, wlist)
                except (OSError, TypeError):
                    self.clients_app.pop(message.to, default=None)  # Удаляем клиента из словаря данных клиента

    @staticmethod
    def show_help():
        print("-" * 79,
              "Возможные команды:",
              "  users - список известных пользователей",
              "  connected - список подключённых пользователей",
              "  loghist - история входов пользователя",
              "  exit - завершение работы сервера.",
              "  help - вывод справки по поддерживаемым командам",
              sep="\n")

    def __work_with_clients(self, server_address):
        # [!!!] A crutch for incorrect connection terminations
        self.database.session.query(Connection).delete()
        self.database.session.commit()

        self.socket_app = socket.create_server(server_address)

        self.socket_app.settimeout(self.TIMEOUT_BLOCKING_SOCKET)
        self.socket_app.listen(self.MAX_NUMBER_CONNECTIONS)
        try:
            self.__connection_handling()
        except KeyboardInterrupt:
            LOGGER.info('Shutdown command sent')
        finally:
            self.socket_app.close()
            LOGGER.critical('The server has completed its work')

    def run_console_interface(self):
        self.show_help()
        while True:
            command = input('Введите команду: ').lower().strip()
            if command == 'help':
                self.show_help()
            elif command == 'exit':
                break
            elif command == 'users':
                print(*self.database.get_users(), sep='\n')
            elif command == 'connected':
                print(*self.database.get_connections(), sep='\n')
            elif command == 'loghist':
                username = input('Введите имя пользователя для просмотра истории. '
                                 'Для вывода всей истории, просто нажмите Enter: ').strip()
                print(*self.database.get_login_history(username), sep='\n')
            else:
                print('Команда не распознана.')

    def _update_connections_gui(self):
        connections = self.database.get_connections_asdict()
        self.window_main.fill_table(connections)
        with self.lock_flag:
            self.is_connections_changed = False

    def _history_btn_signal(self):
        self.window_statistics = StatisticsWindow()
        self.window_statistics.fill_table(self.database.get_user_statistics_asdict())

    def _signal_setting_btn(self):
        self.window_settings = SettingsWindow(signal_save_btn=self._signal_save_btn)
        database_path = Path.cwd().resolve() / DEFAULT_NAME_SERVER_DB
        port = str(BASE_PORT)
        listen_address = ''
        if self.config_file.exists():
            config = configparser.ConfigParser()
            config.read(self.config_file, encoding=BASE_ENCODING)
            try:
                database_path = config['SETTINGS']['database_path']
            except KeyError:
                pass
            else:
                database_path = Path(database_path).resolve()
            try:
                port = config['SETTINGS']['default_port']
            except KeyError:
                pass
            try:
                listen_address = config['SETTINGS']['listen_address']
            except KeyError:
                pass

        self.window_settings.db_path_edit.setText(str(database_path.parent))
        self.window_settings.db_file.setText(str(database_path.name))
        self.window_settings.port_edit.setText(port)
        self.window_settings.ip_address_edit.setText(listen_address)

    def _signal_save_btn(self):
        message = QMessageBox()
        config = configparser.ConfigParser()
        config.read(self.config_file, encoding=BASE_ENCODING)
        dir_name = self.window_settings.db_path_edit.text()
        file_name = self.window_settings.db_file.text()
        config['SETTINGS']['database_path'] = str(
            Path(dir_name, file_name).resolve())
        try:
            port = int(self.window_settings.port_edit.text())
        except ValueError:
            message.warning(self.window_settings, 'Ошибка', 'Порт должен быть числом')
        else:
            config['SETTINGS']['listen_Address'] = self.window_settings.ip_address_edit.text()
            if 1023 < port < 65535:
                config['SETTINGS']['default_port'] = str(port)
                print(port)
                with open(NAME_CONFIG_FILE, 'w', encoding=BASE_ENCODING) as conf:
                    config.write(conf)
                    message.information(self.window_settings, 'OK', 'Настройки успешно сохранены!')
            else:
                message.warning(self.window_settings, 'Ошибка', 'Порт должен быть от 1024 до 65535')

    def run_gui_interface(self):
        _app = QApplication(sys.argv)
        self.window_main = ServerMainWindow(
            history_btn_signal=self._history_btn_signal,
            signal_setting_btn=self._signal_setting_btn,
        )
        self.window_main.statusBar().showMessage('Server Working')
        self._update_connections_gui()

        timer = QTimer()
        timer.timeout.connect(self._update_connections_gui)
        timer.start(1200)

        _app.exec_()

    def get_data_from_settings(self):
        addr, port = None, None
        if self.config_file.exists():
            config = configparser.ConfigParser()
            config.read(self.config_file, encoding=BASE_ENCODING)
            try:
                addr = config['SETTINGS']['listen_address']
            except KeyError:
                pass
            try:
                port = int(config['SETTINGS']['default_port'])
            except (KeyError, ValueError):
                pass
        return addr, port

    def save_data_to_settings(self):
        pass

    def run(self, is_enable_gui=True):
        """Application launch function"""
        arguments = self.get_launch_arguments()
        addr, port = None, None
        if is_enable_gui:
            addr, port = self.get_data_from_settings()
        server_address = (addr or arguments.addr, port or arguments.port)

        stream_to_clients = threading.Thread(target=self.__work_with_clients, args=(server_address,))
        stream_to_clients.daemon = True
        stream_to_clients.start()

        if is_enable_gui:
            self.run_gui_interface()
        else:
            self.run_console_interface()

        # [!!!] A crutch for incorrect connection terminations
        self.database.session.query(Connection).delete()
        self.database.session.commit()


@LogCalls(LOGGER_NAME)
def main():
    app = MessengerServer()
    app.run()


if __name__ == '__main__':
    main()
