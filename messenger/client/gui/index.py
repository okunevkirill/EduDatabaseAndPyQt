from typing import List

from PyQt5.QtCore import QRect
from PyQt5.QtGui import QStandardItemModel, QStandardItem, QBrush, QColor
from PyQt5.QtWidgets import (
    QMainWindow, QApplication, QAction, qApp, QLabel, QListView,
    QTextEdit, QPushButton,
)


class ClientMainWindow(QMainWindow):
    _WINDOW_WIDTH = 640
    _WINDOW_HEIGHT = 480

    def __init__(self, slot_add_contact=None, slot_del_contact=None,
                 slot_send_msg=None, slot_active_contact=None,
                 *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.history_model = None
        self.current_username_chat = 'контакта'
        self._slot_add_contact = slot_add_contact
        self._slot_del_contact = slot_del_contact
        self._slot_send_msg = slot_send_msg
        self._slot_active_contact = slot_active_contact

        self._window_configuration()
        self._create_menubar()
        self._create_contacts_list()
        self._create_contacts_btn()
        self._create_history_msg()
        self._create_input_msg()
        self._create_input_btn()

        self.set_input_inactive()

        self.show()

    def _window_configuration(self):
        self.setWindowTitle('Client part of "Messenger"')
        self.setFixedSize(self._WINDOW_WIDTH, self._WINDOW_HEIGHT)

    def _create_menubar(self):
        menubar = self.menuBar()

        file_menu = menubar.addMenu('&Файл')
        self.exit__menu = QAction('Выход', self)
        self.exit__menu.setShortcut('Ctrl+Q')
        self.exit__menu.triggered.connect(qApp.quit)
        file_menu.addAction(self.exit__menu)

        contacts_menu = menubar.addMenu('&Контакты')
        self.add_contact__menu = QAction('Добавить контакт', self)
        contacts_menu.addAction(self.add_contact__menu)
        if self._slot_add_contact:
            self.add_contact__menu.triggered.connect(self._slot_add_contact)

        self.del_contact__menu = QAction('Удалить контакт', self)
        contacts_menu.addAction(self.del_contact__menu)
        if self._slot_del_contact:
            self.del_contact__menu.triggered.connect(self._slot_del_contact)

    def _create_contacts_list(self):
        label = QLabel('Список контактов', self)
        label.move(10, 30)
        label.setStyleSheet('font:bold')
        label.adjustSize()

        self.contacts__listview = QListView(self)
        self.contacts__listview.setGeometry(QRect(10, 50, 200, 350))
        if self._slot_active_contact:
            self.contacts__listview.doubleClicked.connect(self._slot_active_contact)

    def _create_contacts_btn(self):
        self.add_contact__btn = QPushButton('Добавить контакт', self)
        self.add_contact__btn.setFixedWidth(200)
        self.add_contact__btn.move(10, 410)
        if self._slot_add_contact:
            self.add_contact__btn.clicked.connect(self._slot_add_contact)

        self.del_contact__btn = QPushButton('Удалить контакт', self)
        self.del_contact__btn.setFixedWidth(200)
        self.del_contact__btn.move(10, 440)
        if self._slot_del_contact:
            self.del_contact__btn.clicked.connect(self._slot_del_contact)

    def _create_history_msg(self):
        label = QLabel('История сообщений', self)
        label.move(220, 30)
        label.setStyleSheet('font:bold')
        label.adjustSize()

        self.history_msg__listview = QListView(self)
        self.history_msg__listview.setGeometry(QRect(220, 50, 410, 250))

    def _create_input_msg(self):
        self.msg__label = QLabel(self)
        self.msg__label.move(220, 300)
        self.msg__label.setStyleSheet('font:bold')

        self.msg__textedit = QTextEdit(self)
        self.msg__textedit.setGeometry(QRect(220, 320, 410, 80))

    def _slot_clear_input(self):
        self.msg__textedit.clear()

    def _create_input_btn(self):
        self.clear_textedit__btn = QPushButton('Очистить поле', self)
        self.clear_textedit__btn.setFixedWidth(120)
        self.clear_textedit__btn.move(380, 410)
        self.clear_textedit__btn.clicked.connect(self._slot_clear_input)

        self.send_textedit__btn = QPushButton('Отправить', self)
        self.send_textedit__btn.setFixedWidth(120)
        self.send_textedit__btn.move(510, 410)
        if self._slot_send_msg:
            self.send_textedit__btn.clicked.connect(self._slot_send_msg)

    def fill_contacts_listview(self, data: List[str]):
        item_model = QStandardItemModel(self)
        for username in data:
            item = QStandardItem(username)
            item.setEditable(False)
            item_model.appendRow(item)
        self.contacts__listview.setModel(item_model)

    def fill_history_msg__listview(self, data: List[dict]):
        self.history_model = QStandardItemModel(self)
        for msg in data:
            direction = msg.get('direction')
            if direction == 'in':
                row = QStandardItem(f"Входящее от {msg.get('username')}:\n  {msg.get('msg_text')}")
                row.setBackground(QBrush(QColor(255, 213, 213)))
            else:
                row = QStandardItem(f"Исходящее от {msg.get('username')}:\n  {msg.get('msg_text')}")
                row.setBackground(QBrush(QColor(204, 255, 204)))
            row.setEditable(False)
            self.history_model.appendRow(row)
        self.history_msg__listview.setModel(self.history_model)

    def set_input_inactive(self):
        self.msg__label.setText('*Для выбора получателя требуется двойной клик')
        self.msg__label.adjustSize()

        if self.history_model:
            self.history_model.clear()

        self.msg__textedit.clear()
        self.msg__textedit.setDisabled(True)
        self.clear_textedit__btn.setDisabled(True)
        self.send_textedit__btn.setDisabled(True)

    def set_input_active(self):
        self.msg__label.setText(f'Введите сообщение для {self.current_username_chat}')
        self.msg__label.adjustSize()
        self.msg__textedit.setDisabled(False)
        self.clear_textedit__btn.setDisabled(False)
        self.send_textedit__btn.setDisabled(False)


# -----------------------------------------------------------------------------
def __slot_add_contact():
    print('== Отрабатываем добавление контакта ==')


def __slot_del_contact():
    print('== Отрабатываем удаление контакта ==')


def __slot_active_contact():
    print('== Отрабатываем двойной щелчок на контакте ==')


def __slot_send_msg():
    print('== Отрабатываем кнопку отправки ==')


# -----------------------------------------------------------------------------
def __test_client_main_window(argv):
    app = QApplication(argv)
    window = ClientMainWindow(
        slot_add_contact=__slot_add_contact,
        slot_del_contact=__slot_del_contact,
        slot_send_msg=__slot_send_msg,
        slot_active_contact=__slot_active_contact
    )
    contacts = ['contact_00', 'contact_01', 'contact_02']
    history_msg = [
        {'username': 'Rick', 'direction': 'in', 'msg_text': 'Привет', 'created_at': '2022-08-18 15:12'},
        {'username': 'Marty', 'direction': 'out', 'msg_text': 'Йоханга ;)', 'created_at': '2022-08-18 15:15'},
    ]

    window.fill_contacts_listview(contacts)
    window.fill_history_msg__listview(history_msg)
    window.set_input_active()
    return app.exec_()


# -----------------------------------------------------------------------------

if __name__ == '__main__':
    import sys

    sys.exit(__test_client_main_window(sys.argv))
