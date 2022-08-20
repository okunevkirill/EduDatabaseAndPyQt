from PyQt5.QtWidgets import (
    QDialog, QApplication, QLabel, QLineEdit, QPushButton, qApp,
)
from PyQt5.QtCore import Qt


class NameQueryWindow(QDialog):
    _WINDOW_WIDTH = 250
    _WINDOW_HEIGHT = 140

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.is_success = False

        self._window_configuration()
        self._create_msg__label()
        self._create_name__edit()
        self._create_success__btn()
        self._create_exit__btn()
        self.show()

    def _window_configuration(self):
        self.setWindowTitle('Запрос имени')
        self.setFixedSize(self._WINDOW_WIDTH, self._WINDOW_HEIGHT)

    def _create_msg__label(self):
        label = QLabel('Введите имя пользователя', self)
        label.move(0, 10)
        label.setFixedWidth(self._WINDOW_WIDTH)
        label.setAlignment(Qt.AlignCenter)
        label.setStyleSheet('font:bold')

    def _create_name__edit(self):
        self.name__edit = QLineEdit(self)
        self.name__edit.move(25, 40)
        self.name__edit.setFixedWidth(200)
        self.name__edit.setAlignment(Qt.AlignCenter)

    def _create_success__btn(self):
        self.success__btn = QPushButton('Подтвердить', self)
        self.success__btn.move(10, 90)
        self.success__btn.setFixedWidth(110)

        self.success__btn.clicked.connect(self.pressing_success_btn)

    def _create_exit__btn(self):
        self.exit__btn = QPushButton('Выход', self)
        self.exit__btn.move(130, 90)
        self.exit__btn.setFixedWidth(110)

        self.exit__btn.clicked.connect(qApp.exit)

    def pressing_success_btn(self):
        if not self.name__edit.text().strip():
            return
        self.is_success = True
        qApp.exit()


if __name__ == '__main__':
    import sys

    app = QApplication(sys.argv)
    window = NameQueryWindow()
    sys.exit(app.exec_())
