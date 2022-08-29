import binascii
import hashlib
import ipaddress
import json
import socket as my_socket
from typing import Union

from messenger_trial_client.common.settings import (
    MAX_PACKET_LENGTH, DEFAULT_ENCODING, MIN_ADMISSIBLE_PORT, MAX_ADMISSIBLE_PORT
)


def get_message_from_socket(sock: my_socket.socket) -> dict:
    """Приём и декодирования сообщения из заданного сокета"""
    data = sock.recv(MAX_PACKET_LENGTH).decode(DEFAULT_ENCODING)
    response = json.loads(data)
    if not isinstance(response, dict):
        raise TypeError
    return response


def send_message_to_socket(sock: my_socket.socket, message: dict):
    """Кодирование переданного сообщения и отправка по заданному сокету"""
    if not isinstance(message, dict):
        raise ValueError
    data = json.dumps(message)
    data = data.encode(DEFAULT_ENCODING)
    sock.send(data)


def is_valid_ip_address(ip_address: str) -> bool:
    """Проверка корректности ip-адреса"""
    try:
        ipaddress.ip_address(ip_address)
    except ValueError:
        return False
    return True


def is_valid_port(port: Union[str, int]) -> bool:
    """Проверка значения порта на вхождение в зарегистрированные или частные"""
    try:
        value = int(port)
    except (ValueError, TypeError):
        return False
    return MIN_ADMISSIBLE_PORT <= value <= MAX_ADMISSIBLE_PORT


def get_hash(word: str, salt: str):
    word_bytes = word.encode(DEFAULT_ENCODING)
    salt_bytes = salt.encode(DEFAULT_ENCODING)
    word_hash_bytes = hashlib.pbkdf2_hmac('sha256', word_bytes, salt_bytes, 1000)
    return binascii.hexlify(word_hash_bytes).decode(DEFAULT_ENCODING)
