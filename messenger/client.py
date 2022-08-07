import logging
import socket
import threading
import time

import app_logging.etc.client_log_config as log_config
from app_logging.decorators import log_calls
from kernel.base import Message, BaseApplication, MessageType
from metaclasses import ClientVerifier

# -----------------------------------------------------------------------------
LOGGER_NAME = log_config.__name__
LOGGER = logging.getLogger(LOGGER_NAME)


# -----------------------------------------------------------------------------
class MessengerClient(BaseApplication, metaclass=ClientVerifier):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.username = None

        self.parser.description = "Client part of a simple messenger"
        self.parser.add_argument("-n", "--name", dest="name", default=None, help="Client name in session")

    @staticmethod
    def __presence_obj_generation(username):
        if not isinstance(username, str):
            LOGGER.error('[!] Incorrect name received when generating presence object')
            raise ValueError
        return {
            "action": MessageType.PRESENCE.value,
            "time": time.time(),
            "user": {
                "account_name": username,
                "status": "Yep, I am here!"
            }
        }

    def __presence_exchange(self, username):
        data_object = self.__presence_obj_generation(username)
        self.send_data_to_socket(self.socket_app, data_object=data_object)
        response = self.get_socket_data(self.socket_app)
        LOGGER.info("Response from the server: %s", response)

    def __work_with_server_msgs(self):
        while True:
            try:
                data = self.get_socket_data(self.socket_app)
                message = Message(**data)
                LOGGER.info("Message from '%s': '%s'", message.sender, message.text)
            except ValueError:
                LOGGER.info("Breaking the connection to the server")
                break

    @staticmethod
    def show_help():
        print(
            '-' * 79,
            "Возможные команды:",
            "  message - отправить сообщение",
            "  exit - выход из приложения",
            sep='\n',
        )

    def create_message(self) -> Message:
        return Message(
            action=MessageType.MESSAGE.value,
            time=time.time(),
            sender=self.username,
            to=input("Введите имя получателя: ").strip(),
            text=input("Введите текст сообщения: ").strip()
        )

    def __respond_to_user_actions(self):
        self.show_help()
        while True:
            command = input('ВВЕДИТЕ КОМАНДУ:\n').strip().lower()
            if command == 'message':
                try:
                    message_obj = self.create_message()
                except UnicodeError:
                    continue
                self.send_data_to_socket(self.socket_app, data_object=message_obj._asdict())
            elif command == 'exit':
                break
            else:
                self.show_help()

    def __connection_handling(self):
        self.__presence_exchange(self.username)

        stream_to_receive = threading.Thread(target=self.__work_with_server_msgs)
        stream_to_receive.daemon = True
        stream_to_receive.start()

        stream_for_interaction = threading.Thread(target=self.__respond_to_user_actions)
        stream_for_interaction.daemon = True
        stream_for_interaction.start()

        LOGGER.debug('Control flows created')
        while True:
            time.sleep(1)
            if not stream_to_receive.is_alive() or not stream_for_interaction.is_alive():
                break

    def run(self):
        arguments = self.get_launch_arguments()
        if arguments.name is None:
            arguments.name = input("Enter a name for the session: ").strip()

        server_address = (arguments.addr, arguments.port)
        self.socket_app = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        LOGGER.critical('[*] Launch client %s', arguments.name)
        self.username = arguments.name
        try:
            self.socket_app.connect(server_address)
            LOGGER.info('Client connection to %s', server_address)
            self.__connection_handling()
        except OSError:
            LOGGER.critical('[!] Check server health')
        except KeyboardInterrupt:
            print()
            LOGGER.info('Shutdown command sent')
        finally:
            self.socket_app.close()
            LOGGER.critical('The server has completed its work')


@log_calls(LOGGER_NAME)
def main():
    app = MessengerClient()
    app.run()


if __name__ == '__main__':
    main()
