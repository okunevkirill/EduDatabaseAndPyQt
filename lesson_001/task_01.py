"""
# Задание

Написать функцию host_ping(), в которой с помощью утилиты ping будет
проверяться доступность сетевых узлов. Аргументом функции является список,
в котором каждый сетевой узел должен быть представлен именем хоста или
ip-адресом. В функции необходимо перебирать ip-адреса и проверять их
доступность с выводом соответствующего сообщения («Узел доступен»,
«Узел недоступен»). При этом ip-адрес сетевого узла должен
создаваться с помощью функции ip_address().
"""
import logging
import platform
import queue
import subprocess

from threading import Thread

_PING_OPTIONS = '-n' if platform.system().lower() == 'windows' else '-c'
_PING_QUANTITY = 3


def check_ping(address: str, queued_requests: queue.Queue, is_logging: bool = False):
    prc_command = ['ping', _PING_OPTIONS, str(_PING_QUANTITY), address]
    prc = subprocess.Popen(prc_command, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    prc.wait()
    is_valid = not bool(prc.returncode)
    if is_logging:
        logging.info(f'{address!r} Узел доступен' if is_valid else f'{address!r} Узел недоступен')
    queued_requests.put((address, is_valid))


def host_ping(hosts: list, is_logging: bool = False) -> list:
    thread_results = []
    queued_requests = queue.Queue()
    threads = [Thread(target=check_ping, args=(el, queued_requests),
                      kwargs={'is_logging': is_logging}) for el in hosts]
    for prc in threads:
        prc.start()

    for prc in threads:
        prc.join()

    for _ in threads:
        thread_results.append(queued_requests.get())

    return thread_results


if __name__ == '__main__':
    from pprint import pprint

    logger_format = "%(asctime)s.%(msecs)03d: %(message)s"
    logging.basicConfig(format=logger_format, level=logging.INFO, datefmt="%H:%M:%S")

    hosts_many = ['8.8.8.8', '8.8.8.1', 'yandex.ru']
    _test_result = host_ping(hosts_many, is_logging=True)
    pprint(_test_result)
