from pathlib import Path

from PyQt5.QtCore import Qt
from PyQt5.QtWidgets import (
    QAction, QApplication, QLabel, QMainWindow, QTableView, qApp,
)
from PyQt5.QtGui import QIcon, QStandardItemModel, QStandardItem

_BASE_DIR = Path(__file__).resolve().parent
_IMG_DIR = _BASE_DIR / 'img'


def _get_path_img(filename: str):
    path = _IMG_DIR / filename
    if path.exists():
        return str(_IMG_DIR / filename)


class ServerMainWindow(QMainWindow):
    _WINDOW_WIDTH = 800
    _WINDOW_HEIGHT = 480

    def __init__(self, slot_statistic__btn=None, slot_setting__btn=None,
                 slot_register__btn=None, slot_del_user__btn=None,
                 *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._slot_statistic__btn = slot_statistic__btn
        self._slot_setting__btn = slot_setting__btn
        self._slot_register__btn = slot_register__btn
        self._slot_delete_user__btn = slot_del_user__btn
        self._main_window_config()
        self._create_toolbar()
        self._create_header()
        self._create_table()
        self._create_statusbar()
        self.show()

    def _main_window_config(self):
        self.setWindowTitle('Server part of "Messenger"')
        self.setFixedSize(self._WINDOW_WIDTH, self._WINDOW_HEIGHT)

    def _create_toolbar(self):
        toolbar = self.addToolBar('MainBar')
        toolbar.setMovable(False)
        statistic__btn = QAction(
            QIcon(_get_path_img('history_icon.png')), 'История клиентов', self)
        setting__btn = QAction(
            QIcon(_get_path_img('settings_icon.png')), 'Настройки сервера', self)
        register__btn = QAction(
            QIcon(_get_path_img('add_user_icon.png')), 'Регистрация пользователя', self)
        delete_user__btn = QAction(
            QIcon(_get_path_img('del_user_icon.png')), 'Удалить пользователя', self)
        exit__btn = QAction(
            QIcon(_get_path_img('exit_icon.png')), 'Выход', self)
        toolbar.addAction(statistic__btn)
        toolbar.addAction(setting__btn)
        toolbar.addAction(register__btn)
        toolbar.addAction(delete_user__btn)
        toolbar.addAction(exit__btn)
        exit__btn.setShortcut('Ctrl+Q')
        if self._slot_statistic__btn:
            statistic__btn.triggered.connect(self._slot_statistic__btn)
        if self._slot_setting__btn:
            setting__btn.triggered.connect(self._slot_setting__btn)
        if self._slot_register__btn:
            register__btn.triggered.connect(self._slot_register__btn)
        if self._slot_delete_user__btn:
            delete_user__btn.triggered.connect(self._slot_delete_user__btn)
        exit__btn.triggered.connect(qApp.quit)

    def _create_header(self):
        label = QLabel('Список подключённых клиентов', self)
        label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        label.setStyleSheet('font-weight: bold')
        label.setFixedWidth(self._WINDOW_WIDTH)
        label.move(10, 35)

    def _create_table(self):
        self._connection_table = QTableView(self)
        self._connection_table.move(10, 70)
        self._connection_table.setFixedSize(self._WINDOW_WIDTH - 20, self._WINDOW_HEIGHT - 90)

    def _create_statusbar(self):
        self.statusBar()

    def fill_table(self, data: list):
        item_model = QStandardItemModel(self)
        item_model.setHorizontalHeaderLabels(
            ['Имя Клиента', 'IP Адрес', 'Порт', 'Время подключения'])
        for item in data:
            row = (QStandardItem(item.get(key))
                   for key in ('username', 'ip_address', 'port', 'login_time'))
            item_model.appendRow(row)
        self._connection_table.setModel(item_model)
        self._connection_table.resizeColumnsToContents()
        self._connection_table.resizeRowsToContents()


# -----------------------------------------------------------------------------
def __slot_statistic__btn():
    print('== Отрабатываем нажатие на кнопку статистики ==')


def __slot_setting__btn():
    print('== Отрабатываем нажатие на кнопку настроек ==')


def __slot_register__btn():
    print('== Отрабатываем нажатие на регистрации пользователя ==')


def __slot_del_user__btn():
    print('== Отрабатываем нажатие на кнопку удаления пользователя ==')


# -----------------------------------------------------------------------------
def __test_server_window(argv):
    _app = QApplication(argv)
    window = ServerMainWindow(slot_statistic__btn=__slot_statistic__btn,
                              slot_setting__btn=__slot_setting__btn,
                              slot_register__btn=__slot_register__btn,
                              slot_del_user__btn=__slot_del_user__btn)
    data = [
        {'username': 'Rick', 'ip_address': '192.168.1.10', 'port': '1234',
         'connection_time': '2022-08-14 20:00'},
        {'username': 'Morty', 'ip_address': '192.168.1.11', 'port': '7777',
         'connection_time': '2022-08-14 20:01'},
    ]
    window.statusBar().showMessage('Testing...')
    window.fill_table(data)
    return _app.exec_()


if __name__ == '__main__':
    import sys

    sys.exit(__test_server_window(sys.argv))
