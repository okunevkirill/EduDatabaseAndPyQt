from typing import Optional

from PyQt5.QtWidgets import (
    QDialog, QApplication, QLabel, QComboBox, QPushButton,
)
from PyQt5.QtCore import Qt

from messenger_trial_client.client.db.database import ClientDatabase


class DelContactWindow(QDialog):
    _WINDOW_WIDTH = 400
    _WINDOW_HEIGHT = 115

    def __init__(self, database: Optional[ClientDatabase], *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.database = database

        self._window_configuration()
        self._create_msg__label()
        self._create_selector__box()
        self._create_del__btn()
        self._create_cancel__btn()

        self.show()

    def _window_configuration(self):
        self.setWindowTitle('Удаление контакта')
        self.setFixedSize(self._WINDOW_WIDTH, self._WINDOW_HEIGHT)
        self.setAttribute(Qt.WA_DeleteOnClose)
        self.setModal(True)

    def _create_msg__label(self):
        label = QLabel('Выберите контакт для удаления', self)
        label.move(10, 5)
        label.adjustSize()

    def _create_selector__box(self):
        self.selector__box = QComboBox(self)
        self.selector__box.setFixedWidth(245)
        self.selector__box.move(10, 30)
        if self.database:
            self.selector__box.addItems(sorted(self.database.get_contacts()))

    def _create_del__btn(self):
        self.del__btn = QPushButton('Удалить', self)
        self.del__btn.setFixedWidth(110)
        self.del__btn.move(280, 30)

    def _create_cancel__btn(self):
        self.cancel__btn = QPushButton('Отмена', self)
        self.cancel__btn.setFixedWidth(110)
        self.cancel__btn.move(280, 75)

        self.cancel__btn.clicked.connect(self.close)

    def fill_selector__box(self, data: list):
        self.selector__box.clear()
        self.selector__box.addItems(data)


# -----------------------------------------------------------------------------
if __name__ == '__main__':
    import sys

    app = QApplication(sys.argv)
    window = DelContactWindow(database=None)
    contacts = ['User_1', 'User_2', 'User_3']
    window.fill_selector__box(contacts)
    sys.exit(app.exec_())
