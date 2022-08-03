"""
# Задание

Написать функцию host_range_ping_tab(), возможности которой основаны на
функции из task_02. Но в данном случае результат должен быть итоговым по
всем ip-адресам, представленным в табличном формате (использовать модуль
tabulate). Таблица должна состоять из двух колонок и выглядеть примерно так:
Reachable
10.0.0.1
10.0.0.2

Unreachable
10.0.0.3
10.0.0.4
"""
import logging

from tabulate import tabulate

from lesson_001.task_02 import host_range_ping


def host_range_ping_tab(is_logging: bool = False) -> None:
    range_ping_info = host_range_ping(is_logging=is_logging)
    tabular_data = (
        {'Reachable': host, 'Unreachable': ''} if is_valid
        else {'Reachable': '', 'Unreachable': host}
        for host, is_valid in range_ping_info
    )
    print(
        '=' * 42,
        tabulate(tabular_data, headers='keys', tablefmt='pipe', stralign='center'),
        sep='\n'
    )


if __name__ == '__main__':
    logger_format = "%(asctime)s.%(msecs)03d: %(message)s"
    logging.basicConfig(format=logger_format, level=logging.INFO, datefmt="%H:%M:%S")
    host_range_ping_tab()  # [*] data for example ip='87.240.190.0' quantity=100
