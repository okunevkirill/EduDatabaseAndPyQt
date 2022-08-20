import ipaddress
import json
import socket
from typing import Union
from common.settings import MIN_ADMISSIBLE_PORT, MAX_ADMISSIBLE_PORT, BASE_ENCODING, MAX_PACKET_LENGTH


def is_valid_ip_address(ip_address: str) -> bool:
    try:
        ipaddress.ip_address(ip_address)
    except ValueError:
        return False
    return True


def is_valid_port(port: Union[str, int]) -> bool:
    try:
        value = int(port)
    except (ValueError, TypeError):
        return False
    return MIN_ADMISSIBLE_PORT <= value <= MAX_ADMISSIBLE_PORT


def send_message(sock: socket.socket, data_object: dict):
    data = json.dumps(data_object)
    data = data.encode(BASE_ENCODING)
    sock.send(data)


def get_message(sock: socket.socket) -> dict:
    data = sock.recv(MAX_PACKET_LENGTH).decode(BASE_ENCODING)
    return json.loads(data)
