from PyQt5.QtWidgets import (
    QDialog, QApplication, QLabel, QComboBox, QPushButton,
)
from PyQt5.QtCore import Qt


class AddContactWindow(QDialog):
    _WINDOW_WIDTH = 400
    _WINDOW_HEIGHT = 115

    def __init__(self, slot_refresh__btn=None,
                 slot_add__btn=None, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._slot_refresh__btn = slot_refresh__btn
        self._slot_add__btn = slot_add__btn

        self._window_configuration()
        self._create_msg__label()
        self._create_selector__box()
        self._create_add__btn()
        self._create_cancel__btn()
        self._create_refresh__btn()

        self.show()

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
        if self._slot_add__btn:
            self.add__btn.clicked.connect(self._slot_add__btn)

    def _create_cancel__btn(self):
        self.cancel__btn = QPushButton('Отмена', self)
        self.cancel__btn.setFixedWidth(110)
        self.cancel__btn.move(280, 75)

        self.cancel__btn.clicked.connect(self.close)

    def _create_refresh__btn(self):
        self.refresh__btn = QPushButton('Обновить список', self)
        self.refresh__btn.adjustSize()
        self.refresh__btn.move(10, 75)
        if self._slot_refresh__btn:
            self.refresh__btn.clicked.connect(self._slot_refresh__btn)

    def fill_selector__box(self, data: list):
        self.selector__box.clear()
        self.selector__box.addItems(data)


if __name__ == '__main__':
    import sys

    app = QApplication(sys.argv)
    window = AddContactWindow()
    contacts = ['User_1', 'User_2', 'User_3']
    window.fill_selector__box(contacts)
    sys.exit(app.exec_())
