import argparse
import ipaddress
import json
import socket
from typing import NamedTuple
from enum import Enum

from kernel.config import BASE_PORT, BASE_IP_ADDRESS, BASE_ENCODING, MAX_PACKET_LENGTH

# -----------------------------------------------------------------------------
_MIN_PORT = 1024
_MAX_PORT = 65534

# alias
UnixEpochTime = float


# -----------------------------------------------------------------------------
# special types
class MessageType(str, Enum):
    MESSAGE = "message"
    PRESENCE = "presence"


class Message(NamedTuple):
    action: MessageType.MESSAGE
    time: UnixEpochTime
    sender: str
    to: str
    text: str


# -----------------------------------------------------------------------------
class BaseApplication:
    def __init__(self, *args, **kwargs):
        self.socket_app = None

        self.parser = argparse.ArgumentParser(description="Simple messenger")
        self.parser.add_argument(
            "-a", "--addr", dest="addr", default=BASE_IP_ADDRESS,
            help="IP address to listen on")
        self.parser.add_argument(
            "-p", "--port", dest="port", default=BASE_PORT, type=int,
            help="The port the application is running on")

    def get_launch_arguments(self):
        args = self.parser.parse_args()

        if args.addr and not self.is_valid_ip_address(args.addr):
            raise SystemExit("Invalid IP address specified - ip address must be in ipv4 format")
        if not self.is_valid_port(args.port):
            raise SystemExit(
                f"Invalid port specified - the port must be in the range {_MIN_PORT} <= value <= {_MAX_PORT}")
        return args

    @staticmethod
    def is_valid_ip_address(ip: str) -> bool:
        try:
            ipaddress.ip_address(ip)
        except ValueError:
            return False
        return True

    @staticmethod
    def is_valid_port(value):
        try:
            value = int(value)
        except (ValueError, TypeError):
            return False
        return _MIN_PORT <= value <= _MAX_PORT

    @staticmethod
    def send_data_to_socket(sock: socket.socket, data_object: dict) -> None:
        if not isinstance(data_object, dict):
            raise TypeError

        data = json.dumps(data_object)
        data = data.encode(BASE_ENCODING)
        sock.send(data)

    @staticmethod
    def get_socket_data(sock: socket.socket) -> dict:
        data = sock.recv(MAX_PACKET_LENGTH).decode(BASE_ENCODING)
        try:
            result = json.loads(data)
        except json.JSONDecodeError:
            raise ValueError
        return result

    def run(self):
        raise NotImplementedError
