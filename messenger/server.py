import logging
import select
import socket
from collections import deque
from typing import Dict, Optional

import app_logging.etc.server_log_config as log_config
import descrptrs
from kernel.base import Message, BaseApplication, MessageType
from app_logging.decorators import LogCalls

from metaclasses import ServerVerifier

# -----------------------------------------------------------------------------
LOGGER_NAME = log_config.__name__
LOGGER = logging.getLogger(LOGGER_NAME)


# -----------------------------------------------------------------------------

class MessengerServer(BaseApplication, metaclass=ServerVerifier):
    MAX_NUMBER_CONNECTIONS = 0
    TIMEOUT_BLOCKING_SOCKET = 0.5
    port = descrptrs.Port()

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.clients_app: Dict[str, Optional[socket.socket]] = dict()  # Словарь данных клиентов (имя клиента=сокет)
        self.messages_app = deque()  # Список сообщений
        self.connections = set()  # множество подключенных сокетов
        # ------------------------------
        self.parser.description = "Server part of a simple messenger"
        self.parser.set_defaults(addr='')  # Устанавливаем для прослушивания сокетом всех доступных адресов ip

    def __process_incoming_message(self, sock: socket.socket) -> None:
        data = self.get_socket_data(sock)
        _action = data.get("action")
        if _action == MessageType.PRESENCE.value:
            # Если это сообщение о присутствии, принимаем и отвечаем
            username_to = data["user"]["account_name"]
            if username_to not in self.clients_app:
                self.clients_app[username_to] = sock
                self.send_data_to_socket(sock, data_object={"response": 200})
            else:
                self.send_data_to_socket(sock, data_object={"response": 400, "error": "Name already taken"})
                self.connections.discard(sock)
                sock.close()
        elif _action == MessageType.MESSAGE.value:
            # Если это сообщение, то добавляем его в очередь сообщений.
            self.messages_app.append(Message(**data))

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

    def run(self):
        """Application launch function"""
        arguments = self.parser.parse_args()
        self.port = arguments.port
        if arguments.addr and not self.is_valid_ip_address(arguments.addr):
            raise SystemExit("Invalid IP address specified - ip address must be in ipv4 format")

        server_address = (arguments.addr, self.port)
        self.socket_app = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.socket_app.bind(server_address)
        self.socket_app.settimeout(self.TIMEOUT_BLOCKING_SOCKET)
        self.socket_app.listen(self.MAX_NUMBER_CONNECTIONS)
        LOGGER.critical('Starting the server at address %s', server_address)
        try:
            self.__connection_handling()
        except KeyboardInterrupt:
            LOGGER.info('Shutdown command sent')
        finally:
            self.socket_app.close()
            LOGGER.critical('The server has completed its work')


@LogCalls(LOGGER_NAME)
def main():
    app = MessengerServer()
    app.run()


if __name__ == '__main__':
    main()
