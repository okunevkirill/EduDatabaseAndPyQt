"""
# Задание

Написать функцию host_range_ping() для перебора ip-адресов из заданного
диапазона. Меняться должен только последний октет каждого адреса.
По результатам проверки должно выводиться соответствующее сообщение.
"""
import ipaddress
import logging

from lesson_001.task_01 import host_ping


def get_data() -> dict:
    """Requesting data from an input stream"""
    result = {}
    print("Для прерывания работы программы введите 'exit'", '=' * 42, sep='\n')
    while True:
        data = input('Введите первоначальный адрес: ').strip()
        if data.lower() == 'exit':
            exit(130)
        try:
            ip_address = ipaddress.IPv4Address(data)
            last_octet = int(data.strip('.')[-1])
        except ValueError:
            print('Введён некорректный формат адреса')
        else:
            break

    while True:
        data = input('Сколько адресов проверить: ')
        if data.lower() == 'exit':
            exit(130)
        try:
            quantity = int(data)
            if not (0 < quantity + last_octet < 256):
                raise ValueError
        except ValueError:
            print('Можем менять только последний октет, -',
                  'целое от 1 до 255 включительно с учётом заданного октета')
        else:
            break
    result['ip_address'], result['quantity'] = ip_address, quantity
    return result


def host_range_ping(is_logging: bool = False) -> list:
    data = get_data()
    ip_address, quantity = data['ip_address'], data['quantity']
    hosts = [str(ip_address + idx) for idx in range(quantity + 1)]
    print('Начинаем проверку доступных узлов...')
    return host_ping(hosts, is_logging=is_logging)


if __name__ == '__main__':
    from pprint import pprint

    logger_format = "%(asctime)s.%(msecs)03d: %(message)s"
    logging.basicConfig(format=logger_format, level=logging.INFO, datefmt="%H:%M:%S")
    _test_result = host_range_ping(is_logging=True)
    pprint(_test_result)
