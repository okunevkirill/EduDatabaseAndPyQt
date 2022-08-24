from PyQt5.QtCore import Qt
from PyQt5.QtWidgets import QDialog, QApplication, QLabel, QLineEdit, QPushButton, QMessageBox


class RegistrationWindow(QDialog):
    _WINDOW_WIDTH = 250
    _WINDOW_HEIGHT = 250

    def __init__(self, slot_save__btn=None, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._slot_save__btn = slot_save__btn
        self._window_configuration()
        self._create_labels()
        self._create_edits()
        self._create_save__btn()
        self._create_cancel__btn()
        self.show()

    def _window_configuration(self):
        self.setWindowTitle('Registration')
        self.setFixedSize(self._WINDOW_WIDTH, self._WINDOW_HEIGHT)
        self.setModal(True)

    def _create_labels(self):
        username__label = QLabel('Введите имя пользователя', self)
        username__label.move(0, 5)
        username__label.setFixedWidth(self._WINDOW_WIDTH)
        username__label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        username__label.adjustSize()

        password__label = QLabel('Введите пароль', self)
        password__label.move(0, 65)
        password__label.setFixedWidth(self._WINDOW_WIDTH)
        password__label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        password__label.adjustSize()

        password_2__label = QLabel('Подтвердите пароль', self)
        password_2__label.move(0, 125)
        password_2__label.setFixedWidth(self._WINDOW_WIDTH)
        password_2__label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        password_2__label.adjustSize()

    def _create_edits(self):
        self.username__edit = QLineEdit(self)
        self.username__edit.setFixedWidth(200)
        self.username__edit.move(20, 30)
        self.username__edit.setAlignment(Qt.AlignmentFlag.AlignCenter)

        self.password__edit = QLineEdit(self)
        self.password__edit.setFixedWidth(200)
        self.password__edit.move(20, 90)
        self.password__edit.setEchoMode(QLineEdit.Password)
        self.password__edit.setAlignment(Qt.AlignmentFlag.AlignCenter)

        self.password_2__edit = QLineEdit(self)
        self.password_2__edit.setFixedWidth(200)
        self.password_2__edit.move(20, 150)
        self.password_2__edit.setEchoMode(QLineEdit.Password)
        self.password_2__edit.setAlignment(Qt.AlignmentFlag.AlignCenter)

    def _create_save__btn(self):
        self.save__btn = QPushButton('Сохранить', self)
        self.save__btn.setFixedWidth(110)
        self.save__btn.move(10, 200)
        self.save__btn.clicked.connect(self.save_data)

    def save_data(self):
        messages = QMessageBox()
        username = self.username__edit.text().strip()
        password = self.password__edit.text().strip()
        password_2 = self.password_2__edit.text().strip()
        if not username:
            messages.critical(self, 'Ошибка', 'Не указано имя пользователя')
            return
        if not password or not password_2:
            messages.critical(self, 'Ошибка', 'Поля для пароля не могут быть пусты')
            return
        if not self.is_match_passwords():
            messages.critical(self, 'Ошибка', 'Пароли не совпадают')
            return
        if not self._slot_save__btn:
            return
        try:
            self._slot_save__btn(username, password)
        except ValueError as err:
            messages.critical(self, 'Ошибка', f'{err}')
        else:
            messages.information(self, 'Успех', 'Пользователь зарегистрирован')
            self.close()

    def _create_cancel__btn(self):
        self.cancel__btn = QPushButton('Отмена', self)
        self.cancel__btn.setFixedWidth(110)
        self.cancel__btn.move(130, 200)
        self.cancel__btn.clicked.connect(self.close)

    def is_match_passwords(self):
        return self.password__edit.text() == self.password_2__edit.text()


def __slot_save__btn():
    print('== Отрабатываем нажатие на кнопку сохранения ==')


if __name__ == '__main__':
    import sys

    app = QApplication(sys.argv)
    window = RegistrationWindow(slot_save__btn=__slot_save__btn)
    sys.exit(app.exec_())
