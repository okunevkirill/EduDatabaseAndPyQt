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
    def __init__(self, slot_history__btn=None, slot_setting__btn=None, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._slot_history__btn = slot_history__btn
        self._slot_setting__btn = slot_setting__btn
        self._main_window_config()
        self._create_toolbar()
        self._create_header()
        self._create_table()
        self._create_statusbar()
        self.show()

    def _main_window_config(self):
        self.setWindowTitle('Server part of "Messenger"')
        self.setFixedSize(640, 480)

    def _create_toolbar(self):
        toolbar = self.addToolBar('MainBar')
        toolbar.setMovable(False)
        history_btn = QAction('История клиентов', self)
        if self._slot_history__btn:
            history_btn.triggered.connect(self._slot_history__btn)
        setting_btn = QAction('Настройки сервера', self)
        if self._slot_setting__btn:
            setting_btn.triggered.connect(self._slot_setting__btn)
        exit_btn = QAction(
            QIcon(_get_path_img('exit_icon.png')), 'Выход', self)
        toolbar.addAction(history_btn)
        toolbar.addAction(setting_btn)
        toolbar.addAction(exit_btn)
        exit_btn.setShortcut('Ctrl+Q')
        exit_btn.triggered.connect(qApp.quit)

    def _create_header(self):
        label = QLabel('Список подключённых клиентов', self)
        label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        label.setStyleSheet('font-weight: bold')
        label.setFixedSize(600, 30)
        label.move(10, 35)

    def _create_table(self):
        self._connection_table = QTableView(self)
        self._connection_table.move(10, 70)
        self._connection_table.setFixedSize(620, 390)

    def _create_statusbar(self):
        self.statusBar()

    def fill_table(self, data: list):
        item_model = QStandardItemModel(self)
        item_model.setHorizontalHeaderLabels(
            ['Имя Клиента', 'IP Адрес', 'Порт', 'Время подключения'])
        for item in data:
            row = (QStandardItem(item.get(key))
                   for key in ('username', 'ip_address', 'port', 'connection_time'))
            item_model.appendRow(row)
        self._connection_table.setModel(item_model)
        self._connection_table.resizeColumnsToContents()
        self._connection_table.resizeRowsToContents()


# -----------------------------------------------------------------------------
def __slot_history__btn():
    print('== Отрабатываем нажатие на кнопку истории ==')


def __slot_setting__btn():
    print('== Отрабатываем нажатие на кнопку настроек ==')


# -----------------------------------------------------------------------------
def __test_server_window(argv):
    _app = QApplication(argv)
    window = ServerMainWindow(slot_history__btn=__slot_history__btn,
                              slot_setting__btn=__slot_setting__btn)
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
