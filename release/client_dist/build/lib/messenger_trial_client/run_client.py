import logging
import argparse
import sys
from PyQt5.QtWidgets import QApplication, QMessageBox

from messenger_trial_client.client.gui.namequery import NameQueryWindow
from messenger_trial_client.common import settings, utils
from messenger_trial_client.common.errors import ServerError

from messenger_trial_client.client import logger

from messenger_trial_client.client.db.database import ClientDatabase
from messenger_trial_client.client.transport import ClientTransport
from messenger_trial_client.client.gui.index import ClientMainWindow

LOGGER_NAME = logger.__name__
LOGGER = logging.getLogger(LOGGER_NAME)


def arg_parser():
    parser = argparse.ArgumentParser(description='Client part of the messenger')
    parser.add_argument('-a', '--addr', dest='addr', default=settings.DEFAULT_IP_ADDRESS,
                        help='IP address to listen on')
    parser.add_argument('-P', '--port', dest='port', default=settings.DEFAULT_PORT, type=int,
                        help='The port the application is running on')
    parser.add_argument('-n', '--name', dest='name', default=None, help='Client name in session')
    parser.add_argument('-p', '--password', dest='password', default=None, help='Client password')
    parser_arguments = parser.parse_args()
    _server_address = parser_arguments.addr
    _server_port = parser_arguments.port
    _client_name = parser_arguments.name
    _client_password = parser_arguments.password

    # проверим подходящий номер порта
    if not utils.is_valid_port(_server_port):
        LOGGER.critical(
            f'Попытка запуска клиента с неподходящим номером порта: {server_port}. '
            f'Допустимы адреса с {settings.MIN_ADMISSIBLE_PORT} до {settings.MAX_ADMISSIBLE_PORT}.'
            f' Клиент завершает работу.')
        sys.exit(1)

    return _server_address, _server_port, _client_name, _client_password


def main():
    server_address, server_port, client_name, client_password = arg_parser()
    client_app = QApplication(sys.argv)
    if not client_name or not client_password:
        start_dialog = NameQueryWindow()
        client_app.exec_()
        if start_dialog.is_success:
            client_name = start_dialog.name__edit.text().strip()
            client_password = start_dialog.password__edit.text().strip()
            del start_dialog
        else:
            sys.exit(0)

    LOGGER.info(f'Запущен клиент: адрес {server_address!r}:{server_port}, имя {client_name}')
    database = ClientDatabase(client_name)
    transport = None
    try:
        transport = ClientTransport(
            server_port, server_address, username=client_name, password=client_password, database=database)
    except ServerError as err:
        message = QMessageBox()
        message.critical(message, 'Ошибка сервера', f'{err}')
        exit(1)
    transport.daemon = True
    transport.start()

    # Создаём GUI
    main_window = ClientMainWindow(database, transport)
    main_window.make_connection(transport)
    main_window.setWindowTitle(f'Чат пользователя {client_name!r}')
    client_app.exec_()

    transport.transport_shutdown()
    transport.join()


# Основная функция клиента
if __name__ == '__main__':
    main()
