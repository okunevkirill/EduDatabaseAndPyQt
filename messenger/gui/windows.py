from pathlib import Path

from PyQt5.QtCore import Qt
from PyQt5.QtWidgets import (
    QAction, QApplication, QLabel, QMainWindow, QTableView,
    qApp, QPushButton, QLineEdit, QFileDialog, QDialog,
)
from PyQt5.QtGui import QIcon, QStandardItemModel, QStandardItem

_BASE_DIR = Path(__file__).resolve().parent
_IMG_DIR = _BASE_DIR / 'img'


def _get_path_img(filename: str):
    path = _IMG_DIR / filename
    if path.exists():
        return str(_IMG_DIR / filename)


class ServerMainWindow(QMainWindow):
    def __init__(self, history_btn_signal=None, signal_setting_btn=None, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._signal_history_btn = history_btn_signal
        self._signal_setting_btn = signal_setting_btn
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
        if self._signal_history_btn:
            history_btn.triggered.connect(self._signal_history_btn)
        setting_btn = QAction('Настройки сервера', self)
        if self._signal_setting_btn:
            setting_btn.triggered.connect(self._signal_setting_btn)
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


class StatisticsWindow(QDialog):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._main_window_config()
        self._create_table()
        self._create_close_btn()
        self.show()

    def _main_window_config(self):
        self.setWindowTitle('Statistics')
        self.setFixedSize(640, 640)
        self.setAttribute(Qt.WA_DeleteOnClose)

    def _create_close_btn(self):
        close_btn = QPushButton('Закрыть', self)
        close_btn.move(520, 600)
        close_btn.clicked.connect(self.close)

    def _create_table(self):
        self._history_table = QTableView(self)
        self._history_table.move(10, 10)
        self._history_table.setFixedSize(620, 580)

    def fill_table(self, data):
        item_model = QStandardItemModel(self)
        item_model.setHorizontalHeaderLabels(
            ['Имя Клиента', 'Последний раз входил', 'Отправлено', 'Получено'])
        for item in data:
            row = (QStandardItem(item.get(key))
                   for key in ('username', 'last_login_time', 'sent', 'received'))
            item_model.appendRow(row)
        self._history_table.setModel(item_model)
        self._history_table.resizeColumnsToContents()
        self._history_table.resizeRowsToContents()


class SettingsWindow(QDialog):
    def __init__(self, signal_save_btn=None, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._signal_save_btn = signal_save_btn
        self._main_window_config()
        self._create_settings_for_database()
        self._create_settings_for_socket()
        self._create_save_btn()
        self._create_close_btn()

        self.show()

    @staticmethod
    def open_file(dialog: QFileDialog, obj_edit: QLineEdit):
        path = dialog.getExistingDirectory()
        obj_edit.setText(path)

    def _main_window_config(self):
        self.setWindowTitle('Settings')
        self.setFixedSize(380, 290)

    def _create_settings_for_database(self):
        db_path_label = QLabel('Путь до директории базы данных: ', self)
        db_path_label.move(10, 10)
        db_path_label.setFixedSize(240, 15)

        self.db_path_edit = QLineEdit(self)
        self.db_path_edit.setFixedSize(250, 20)
        self.db_path_edit.move(10, 30)
        self.db_path_edit.setReadOnly(True)

        db_path_select_btn = QPushButton('Обзор...', self)
        db_path_select_btn.move(275, 28)
        db_path_select_btn.setFixedWidth(100)
        dialog = QFileDialog(self)
        db_path_select_btn.clicked.connect(
            lambda x: self.open_file(dialog, self.db_path_edit))

        db_file_label = QLabel('Имя файла базы данных: ', self)
        db_file_label.move(10, 68)
        db_file_label.setFixedSize(180, 15)

        self.db_file = QLineEdit(self)
        self.db_file.move(200, 66)
        self.db_file.setFixedSize(175, 20)

    def _create_settings_for_socket(self):
        port_label = QLabel('Номер порта для соединений:', self)
        port_label.move(10, 108)
        port_label.setFixedSize(180, 15)

        self.port_edit = QLineEdit(self)
        self.port_edit.move(200, 108)
        self.port_edit.setFixedSize(175, 20)

        ip_address_label = QLabel('IP для прослушивания:', self)
        ip_address_label.move(10, 148)
        ip_address_label.setFixedSize(180, 15)

        ip_address_label_note = QLabel(
            '*оставьте поле для прослушивания пустым,\nчтобы принимать соединения с любых адресов.', self)
        ip_address_label_note.move(10, 185)
        ip_address_label_note.setFixedSize(500, 30)

        self.ip_address_edit = QLineEdit(self)
        self.ip_address_edit.move(200, 148)
        self.ip_address_edit.setFixedSize(175, 20)

    def _create_close_btn(self):
        close_btn = QPushButton('Закрыть', self)
        close_btn.move(275, 250)
        close_btn.clicked.connect(self.close)

    def _create_save_btn(self):
        save_btn = QPushButton('Сохранить', self)
        save_btn.move(160, 250)
        if self._signal_save_btn:
            save_btn.clicked.connect(self._signal_save_btn)


def __test_server_window(argv):
    _app = QApplication(argv)
    window = ServerMainWindow()
    data = [
        {'username': 'Rick', 'ip_address': '192.168.1.10', 'port': '1234',
         'connection_time': '2022-08-14 20:00'},
        {'username': 'Morty', 'ip_address': '192.168.1.11', 'port': '7777',
         'connection_time': '2022-08-14 20:01'},
    ]
    window.statusBar().showMessage('Testing...')
    window.fill_table(data)
    return _app.exec_()


def __test_statistics_window(argv):
    _app = QApplication(argv)
    window = StatisticsWindow()
    data = [
        {'username': 'Rick', 'last_login_time': '2022-08-13 15:12', 'sent': '3', 'received': '5'},
        {'username': 'Marty', 'last_login_time': '2022-07-13 16:16', 'sent': '0', 'received': '1'},
    ]
    window.fill_table(data)
    return _app.exec_()


def __test_settings_window(argv):
    _app = QApplication(argv)
    window = SettingsWindow()
    path = str(Path.cwd().resolve())
    window.db_path_edit.setText(path)
    window.db_file.setText('server_db.db3')
    window.port_edit.setText('8888')
    window.ip_address_edit.setText('127.0.0.1')
    return _app.exec_()


if __name__ == '__main__':
    import sys

    __test_server_window(sys.argv)
    __test_statistics_window(sys.argv)
    __test_settings_window(sys.argv)
