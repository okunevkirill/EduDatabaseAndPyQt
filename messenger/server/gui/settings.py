from pathlib import Path

from PyQt5.QtWidgets import QLabel, QPushButton, QLineEdit, QFileDialog, QDialog, QApplication


class SettingsWindow(QDialog):
    def __init__(self, slot_save__btn=None, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._slot_save__btn = slot_save__btn
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
        self.setModal(True)

    def _create_settings_for_database(self):
        db_path__label = QLabel('Путь до директории базы данных', self)
        db_path__label.move(10, 10)
        db_path__label.adjustSize()

        self.db_path__edit = QLineEdit(self)
        self.db_path__edit.setFixedSize(250, 20)
        self.db_path__edit.move(10, 30)
        self.db_path__edit.setReadOnly(True)

        db_path_select__btn = QPushButton('Обзор...', self)
        db_path_select__btn.move(275, 28)
        db_path_select__btn.setFixedWidth(100)
        dialog = QFileDialog(self)
        db_path_select__btn.clicked.connect(
            lambda x: self.open_file(dialog, self.db_path__edit))

        db_file__label = QLabel('Имя файла БД: ', self)
        db_file__label.move(10, 68)
        db_file__label.setFixedSize(180, 15)

        self.db_file__edit = QLineEdit(self)
        self.db_file__edit.move(200, 66)
        self.db_file__edit.setFixedSize(175, 20)

    def _create_settings_for_socket(self):
        port__label = QLabel('Номер порта', self)
        port__label.move(10, 108)
        port__label.setFixedSize(180, 15)

        self.port__edit = QLineEdit(self)
        self.port__edit.move(200, 108)
        self.port__edit.setFixedSize(175, 20)

        ip_address__label = QLabel('IP для прослушивания', self)
        ip_address__label.move(10, 148)
        ip_address__label.setFixedSize(180, 15)

        ip_address_note__label = QLabel(
            '*оставьте поле для прослушивания пустым,\nчтобы принимать соединения с любых адресов.', self)
        ip_address_note__label.move(10, 185)
        ip_address_note__label.setFixedSize(500, 30)

        self.ip_address__edit = QLineEdit(self)
        self.ip_address__edit.move(200, 148)
        self.ip_address__edit.setFixedSize(175, 20)

    def _create_close_btn(self):
        close__btn = QPushButton('Закрыть', self)
        close__btn.move(275, 250)
        close__btn.clicked.connect(self.close)

    def _create_save_btn(self):
        save__btn = QPushButton('Сохранить', self)
        save__btn.move(160, 250)
        if self._slot_save__btn:
            save__btn.clicked.connect(self._slot_save__btn)


# -----------------------------------------------------------------------------
def __slot_save__btn():
    print('== Отрабатываем нажатие на кнопку сохранения ==')


# -----------------------------------------------------------------------------
def __test_settings_window(argv):
    _app = QApplication(argv)
    window = SettingsWindow(slot_save__btn=__slot_save__btn)
    path = str(Path.cwd().resolve())
    window.db_path__edit.setText(path)
    window.db_file__edit.setText('server_db.db3')
    window.port__edit.setText('8888')
    window.ip_address__edit.setText('127.0.0.1')
    return _app.exec_()


if __name__ == '__main__':
    import sys

    sys.exit(__test_settings_window(sys.argv))
