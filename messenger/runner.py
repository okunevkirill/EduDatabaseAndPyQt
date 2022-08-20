import argparse

from client.core import ClientApp
from common.settings import BASE_IP_ADDRESS, BASE_PORT
from common.utils import is_valid_ip_address, is_valid_port


def arg_parser():
    parser = argparse.ArgumentParser(description='Client part of the messenger')
    parser.add_argument('-a', '--addr', dest='addr', default=BASE_IP_ADDRESS,
                        help='IP address to listen on')
    parser.add_argument('-p', '--port', dest='port', default=BASE_PORT, type=int,
                        help='The port the application is running on')
    parser.add_argument('-n', '--name', dest='name', default=None, help='Client name in session')
    args = parser.parse_args()
    if not is_valid_ip_address(args.addr):
        raise SystemExit('Invalid IP address specified - IP address must be in ipv4 or ipv6 format')
    if not is_valid_port(args.port):
        raise SystemExit('Invalid port specified')
    return args.addr, args.port, args.name


def main():
    server_address, server_port, client_name = arg_parser()
    app = ClientApp(username=client_name, ip_address=server_address, port=server_port)
    app.run()


if __name__ == '__main__':
    main()
