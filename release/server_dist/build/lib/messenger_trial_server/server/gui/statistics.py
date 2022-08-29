from PyQt5.QtCore import Qt
from PyQt5.QtWidgets import QTableView, QPushButton, QDialog, QApplication
from PyQt5.QtGui import QStandardItemModel, QStandardItem


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
                   for key in ('username', 'last_login', 'sent', 'accepted'))
            item_model.appendRow(row)
        self._history_table.setModel(item_model)
        self._history_table.resizeColumnsToContents()
        self._history_table.resizeRowsToContents()


# -----------------------------------------------------------------------------
def __test_statistics_window(argv):
    _app = QApplication(argv)
    window = StatisticsWindow()
    data = [
        {'username': 'Rick', 'last_login': '2022-08-13 15:12', 'sent': '3', 'accepted': '5'},
        {'username': 'Marty', 'last_login': '2022-07-13 16:16', 'sent': '0', 'accepted': '1'},
    ]
    window.fill_table(data)
    return _app.exec_()


if __name__ == '__main__':
    import sys

    sys.exit(__test_statistics_window(sys.argv))
