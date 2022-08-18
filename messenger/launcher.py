import os
import signal
import time
from pathlib import Path
import sys
import subprocess

NUMBER_CLIENTS = 5
BASE_DIR = Path(__file__).resolve().parent


def run_on_win():
    processes = []

    while True:
        action = input('Выберите действие: q - выход, s - запустить сервер и клиенты, x - закрыть все окна: ')

        if action == 'q':
            break
        elif action == 's' and not processes:
            processes.append(subprocess.Popen('python server.py', creationflags=subprocess.CREATE_NEW_CONSOLE))
            time.sleep(0.5)  # Время не должно быть меньше времени TIMEOUT_BLOCKING_SOCKET у сервера
            for _ in range(NUMBER_CLIENTS):
                processes.append(
                    subprocess.Popen(
                        f'python client_runner.py -n test{_ + 1}', creationflags=subprocess.CREATE_NEW_CONSOLE))

        elif action == 'x':
            while processes:
                victim = processes.pop()
                victim.kill()


def run_on_lin():
    processes = []

    while True:
        action = input('Выберите действие: q - выход, s - запустить сервер и клиенты, x - закрыть все окна: ')
        if action == 'q':
            break
        elif action == 's' and not processes:
            file_path = BASE_DIR / 'server.py'
            processes.append(subprocess.Popen(
                ['gnome-terminal', '--disable-factory', '--', 'python3', f'{file_path}'],
                preexec_fn=os.setpgrp
            ))

            file_path = BASE_DIR / 'client_runner.py'
            time.sleep(0.5)  # Время не должно быть меньше времени TIMEOUT_BLOCKING_SOCKET у сервера
            for _ in range(NUMBER_CLIENTS):
                processes.append(
                    subprocess.Popen(
                        ['gnome-terminal', '--disable-factory', '--', 'python3', f'{file_path}', '-n', f'test{_ + 1}'],
                        preexec_fn=os.setpgrp
                    ))

        elif action == 'x':
            while processes:
                victim = processes.pop()
                os.killpg(victim.pid, signal.SIGINT)


def main():
    mode = sys.platform
    if mode.startswith('lin'):
        run_on_lin()
    elif mode.startswith('win'):
        run_on_win()


if __name__ == '__main__':
    main()
