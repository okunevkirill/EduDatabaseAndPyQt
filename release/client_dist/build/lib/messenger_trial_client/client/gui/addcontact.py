from typing import Optional
from PyQt5.QtWidgets import (
    QDialog, QApplication, QLabel, QComboBox, QPushButton,
)
from PyQt5.QtCore import Qt

from messenger_trial_client.client.db.database import ClientDatabase
from messenger_trial_client.client.transport import ClientTransport


class AddContactWindow(QDialog):
    _WINDOW_WIDTH = 400
    _WINDOW_HEIGHT = 115

    def __init__(self, transport: Optional[ClientTransport], database: Optional[ClientDatabase], *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.transport = transport
        self.database = database

        self._window_configuration()
        self._create_msg__label()
        self._create_selector__box()
        self._create_add__btn()
        self._create_cancel__btn()
        self._create_refresh__btn()
        self.show()
        self.possible_contacts_update()

    def _window_configuration(self):
        self.setWindowTitle('Добавление контакта')
        self.setFixedSize(self._WINDOW_WIDTH, self._WINDOW_HEIGHT)
        self.setAttribute(Qt.WA_DeleteOnClose)
        self.setModal(True)

    def _create_msg__label(self):
        label = QLabel('Выберите контакт для добавления', self)
        label.move(10, 5)
        label.adjustSize()

    def _create_selector__box(self):
        self.selector__box = QComboBox(self)
        self.selector__box.setFixedWidth(245)
        self.selector__box.move(10, 30)

    def _create_add__btn(self):
        self.add__btn = QPushButton('Добавить', self)
        self.add__btn.setFixedWidth(110)
        self.add__btn.move(280, 30)

    def _create_cancel__btn(self):
        self.cancel__btn = QPushButton('Отмена', self)
        self.cancel__btn.setFixedWidth(110)
        self.cancel__btn.move(280, 75)

        self.cancel__btn.clicked.connect(self.close)

    def _create_refresh__btn(self):
        self.refresh__btn = QPushButton('Обновить список', self)
        self.refresh__btn.adjustSize()
        self.refresh__btn.move(10, 75)
        self.refresh__btn.clicked.connect(self.update_possible_contacts)

    def possible_contacts_update(self, contacts=None, users=None):
        self.selector__box.clear()
        if self.database:
            contacts_list = set(self.database.get_contacts())
            users_list = set(self.database.get_known_users())
        else:
            contacts_list = contacts or set()
            users_list = users or set()
        if self.transport:
            users_list.remove(self.transport.username)
        self.selector__box.addItems(users_list - contacts_list)

    def update_possible_contacts(self, user_list=None):
        if not self.transport:
            return
        try:
            self.transport.user_list_update()
        except OSError:
            pass
        else:
            self.possible_contacts_update()

    def fill_selector__box(self, data: list):
        self.selector__box.clear()
        self.selector__box.addItems(data)


if __name__ == '__main__':
    import sys

    app = QApplication(sys.argv)
    window = AddContactWindow(transport=None, database=None)
    contacts = ['User_1', 'User_2', 'User_3']
    window.fill_selector__box(contacts)
    sys.exit(app.exec_())
