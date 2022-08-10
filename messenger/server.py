import logging
import select
import socket
import threading
from collections import deque
from datetime import datetime
from typing import Dict, Optional

import app_logging.etc.server_log_config as log_config
from db.database import engine_server, SessionServer, ServerBase
from db.models import User, Connection, LoginHistory
from kernel.base import Message, BaseApplication, MessageType
from app_logging.decorators import LogCalls

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

    def get_login_history(self):
        username = input('Введите имя пользователя для просмотра истории. '
                         'Для вывода всей истории, просто нажмите Enter: ').strip()
        if username:
            user: User = self.session.query(User).filter_by(username=username).one()
            return self.session.query(LoginHistory).filter_by(user_id=user.id)
        return self.session.query(LoginHistory).all()

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
        user: User = self.session.query(User).filter_by(username=username).one()
        self.session.query(Connection).filter_by(user_id=user.id).delete()
        self.session.commit()


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

        self.database = Storage()

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
            else:
                self.send_data_to_socket(sock, data_object={"response": 400, "error": "Name already taken"})
                self.connections.discard(sock)
                sock.close()
        elif _action == MessageType.MESSAGE.value:
            # Если это сообщение, то добавляем его в очередь сообщений.
            self.messages_app.append(Message(**data))
        elif _action == MessageType.EXIT.value:
            self.database.delete_connect(data.get("account_name"))

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
                    pass  # разрыв соединения с клиентом
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
                print(*self.database.get_login_history(), sep='\n')
            else:
                print('Команда не распознана.')

    def run(self):
        """Application launch function"""
        arguments = self.get_launch_arguments()
        server_address = (arguments.addr, arguments.port)

        stream_to_clients = threading.Thread(target=self.__work_with_clients, args=(server_address,))
        stream_to_clients.daemon = True
        stream_to_clients.start()

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
