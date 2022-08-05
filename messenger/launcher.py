import time
from pathlib import Path
import sys
import subprocess

NUMBER_CLIENTS = 3
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
                    subprocess.Popen(f'python client.py -n test{_ + 1}', creationflags=subprocess.CREATE_NEW_CONSOLE))

        elif action == 'x':
            while processes:
                victim = processes.pop()
                victim.kill()


def run_on_lin():
    processes = []

    while True:
        action = input('Выберите действие: q - выход, s - запустить сервер и клиенты: ')
        if action == 'q':
            break
        elif action == 's' and not processes:
            file_path = BASE_DIR / 'server.py'
            processes.append(subprocess.Popen(['gnome-terminal', '--', 'python3', f'{file_path}']))

            file_path = BASE_DIR / 'client.py'
            for _ in range(NUMBER_CLIENTS):
                processes.append(
                    subprocess.Popen(['gnome-terminal', '--', 'python3', f'{file_path}', '-n', f'test{_ + 1}']))

        # elif action == 'x':
        #     while processes:
        #         victim = processes.pop()
        #         victim.kill()
        #         victim.communicate()


def main():
    mode = sys.platform
    if mode.startswith('lin'):
        run_on_lin()
    elif mode.startswith('win'):
        run_on_win()


if __name__ == '__main__':
    main()
