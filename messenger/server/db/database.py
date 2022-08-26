import datetime
from pathlib import Path
from typing import List

from sqlalchemy import (
    create_engine, MetaData, Table, Column,
    Integer, String, DateTime, ForeignKey,
)
from sqlalchemy.orm import sessionmaker, mapper

from server.db.definitions import (
    AllUsers, ActiveUser, LoginHistory, UserContact, UserHistory,
)

_BASE_DIR = Path(__file__).resolve().parent.parent.parent
DEFAULT_PATH_DB = str(_BASE_DIR / 'server_db.db3')


class ServerDatabase:
    def __init__(self, path: str = DEFAULT_PATH_DB):
        self.path = Path(path).resolve()
        self._init_database()
        # [!] очищаем БД от возможных некорректных данных после ошибок
        self.clear_active_users()

    def _init_database(self):
        database_url = f"sqlite:///{self.path}"
        engine = create_engine(database_url, pool_recycle=3600, connect_args={'check_same_thread': False})
        metadata = MetaData()
        users__tbl = Table('users', metadata,
                           Column('id', Integer, primary_key=True),
                           Column('username', String, index=True, unique=True, nullable=False),
                           Column('password_hash', String, nullable=False),
                           Column('last_login', DateTime, default=datetime.datetime.utcnow))
        active_users__tbl = Table('active_users', metadata,
                                  Column('id', Integer, primary_key=True),
                                  Column('user_id', ForeignKey('users.id'), unique=True),
                                  Column('ip_address', String, nullable=False),
                                  Column('port', Integer),
                                  Column('login_time', DateTime, default=datetime.datetime.utcnow))
        login_history__tbl = Table('login_history', metadata,
                                   Column('id', Integer, primary_key=True),
                                   Column('user_id', ForeignKey('users.id')),
                                   Column('date_time', DateTime, default=datetime.datetime.utcnow),
                                   Column('ip_address', String, nullable=False),
                                   Column('port', Integer))
        contacts__tbl = Table('contacts', metadata,
                              Column('id', Integer, primary_key=True),
                              Column('user_id', ForeignKey('users.id')),
                              Column('contact_id', ForeignKey('users.id')))
        users_history__tbl = Table('history', metadata,
                                   Column('id', Integer, primary_key=True),
                                   Column('user_id', ForeignKey('users.id')),
                                   Column('sent', Integer),
                                   Column('accepted', Integer))
        metadata.create_all(engine)
        mapper(AllUsers, users__tbl)
        mapper(ActiveUser, active_users__tbl)
        mapper(LoginHistory, login_history__tbl)
        mapper(UserContact, contacts__tbl)
        mapper(UserHistory, users_history__tbl)
        self._Session = sessionmaker(autocommit=False, autoflush=False, bind=engine)
        self.session = self._Session()

    def clear_active_users(self):
        self.session.query(ActiveUser).delete()
        self.session.commit()

    def get_user_by_name(self, username):
        return self.session.query(AllUsers).filter_by(username=username).first()

    def add_user(self, username, password_hash):
        user = AllUsers(username=username, password_hash=password_hash)
        self.session.add(user)
        self.session.commit()
        history_of_user = UserHistory(user_id=user.id)
        self.session.add(history_of_user)
        self.session.commit()

    def del_user(self, username):
        user = self.get_user_by_name(username)
        self.session.query(ActiveUser).filter_by(user_id=user.id).delete()
        self.session.query(LoginHistory).filter_by(user_id=user.id).delete()
        self.session.query(UserHistory).filter_by(user_id=user.id).delete()
        self.session.query(UserContact).filter(
            (UserContact.user_id == user.id) | (UserContact.contact_id == user.id)).delete()
        self.session.query(AllUsers).filter_by(username=username).delete()
        self.session.commit()

    def user_login(self, username, password_hash, ip_address, port):
        """Действия при подключении пользователя к серверу"""
        user: AllUsers = self.get_user_by_name(username)
        if not user:
            raise ValueError('Пользователь не зарегистрирован')
        if user.password_hash != password_hash:
            raise ValueError('Некорректный пароль пользователя')
        user.last_login = datetime.datetime.now()
        new_active_user = ActiveUser(
            user_id=user.id, ip_address=ip_address,
            port=port, login_time=datetime.datetime.now())
        self.session.add(new_active_user)
        history = LoginHistory(
            user_id=user.id, date=datetime.datetime.now(), ip_address=ip_address, port=port)
        self.session.add(history)
        self.session.commit()

    def user_logout(self, username: str):
        """Действие при отключении пользователя от сервера"""
        user = self.get_user_by_name(username)
        self.session.query(ActiveUser).filter_by(user_id=user.id).delete()
        self.session.commit()

    def msg_registration(self, sender_username, recipient_username):
        """Действия при регистрации сообщений (изменение счётчиков сообщений)"""
        sender: AllUsers = self.get_user_by_name(sender_username)
        recipient: AllUsers = self.get_user_by_name(recipient_username)
        sender_history: UserHistory = self.session.query(UserHistory).filter_by(user_id=sender.id).first()
        sender_history.sent += 1
        recipient_history: UserHistory = self.session.query(UserHistory).filter_by(user_id=recipient.id).first()
        recipient_history.accepted += 1
        self.session.commit()

    def add_contact(self, required_username: str, sender_username: str):
        """Действия при запросе нового контакта от пользователя"""
        if not required_username or not sender_username:
            return
        user: AllUsers = self.get_user_by_name(required_username)
        sender: AllUsers = self.get_user_by_name(sender_username)
        if self.session.query(UserContact).filter_by(
                user_id=user.id, contact_id=sender.id).first():
            return
        contact = UserContact(user_id=user.id, contact_id=sender.id)
        self.session.add(contact)
        self.session.commit()

    def del_contact(self, required_username: str, sender_username: str):
        """Действие при запросе удаления контакта пользователя"""
        if not required_username or not sender_username:
            return
        user: AllUsers = self.get_user_by_name(required_username)
        sender: AllUsers = self.get_user_by_name(sender_username)
        self.session.query(UserContact).filter_by(user_id=user.id, contact_id=sender.id).delete()
        self.session.commit()

    def get_list_of_usernames(self) -> List[str]:
        """Возвращает список имён всех пользователей зарегистрированных на сервере"""
        query = self.session.query(AllUsers.username).all()
        return sorted((el[0] for el in query))

    def get_active_users(self) -> List[dict]:
        """Возвращает подробную информацию об активных пользователях"""
        query = self.session.query(
            AllUsers.username,
            ActiveUser.ip_address,
            ActiveUser.port,
            ActiveUser.login_time).join(AllUsers).all()
        return [
            {'username': el.username, 'ip_address': el.ip_address,
             'port': str(el.port), 'login_time': str(el.login_time)}
            for el in query
        ]

    def get_login_history(self, username=None) -> List[dict]:
        """Возвращает подробную информацию об истории входов"""
        query = self.session.query(
            AllUsers.username,
            LoginHistory.date_time,
            LoginHistory.ip_address,
            LoginHistory.port).join(AllUsers)
        if username:
            query = query.filter(AllUsers.username == username)
        return [
            {'username': el.username, 'date_time': str(el.date_time),
             'ip_address': el.ip_address, 'port': str(el.port)}
            for el in query
        ]

    def get_contacts(self, username: str) -> List[str]:
        """Возвращает список имён заданного пользователя"""
        user: AllUsers = self.get_user_by_name(username)
        query = self.session.query(
            UserContact, AllUsers.username).filter_by(
            user_id=user.id).join(AllUsers, UserContact.contact_id == AllUsers.id)
        return [el[1] for el in query]

    def get_msg_count_info(self) -> List[dict]:
        """Получить информацию о количестве сообщений"""
        query = self.session.query(
            AllUsers.username, AllUsers.last_login, UserHistory.sent,
            UserHistory.accepted).join(AllUsers)
        return [
            {'username': el.username, 'last_login': str(el.last_login),
             'sent': str(el.sent), 'accepted': str(el.accepted)}
            for el in query
        ]

    def is_user_registered(self, username: str) -> bool:
        return bool(self.get_user_by_name(username))


if __name__ == '__main__':
    from pprint import pprint

    _path = _BASE_DIR / 'server_for_del.db3'
    if _path.exists() and _path.is_file():
        _path.unlink()

    __test_variable = ServerDatabase(str(_BASE_DIR / 'server_for_del.db3'))
    __test_variable.add_user('user_01', 'password_hash')
    __test_variable.add_user('user_02', 'password_hash')
    __test_variable.add_user('user_03', 'password_hash')
    __test_variable.add_user('user_04', 'password_hash')
    __test_variable.user_login('user_01', 'password_hash', '8.8.8.8', 8888)
    __test_variable.user_login('user_02', 'password_hash', '7.7.7.7', 7777)
    __test_variable.user_login('user_03', 'password_hash', '6.6.6.6', 6666)
    __test_variable.user_login('user_04', 'password_hash', '5.5.5.5', 5555)
    __test_variable.user_logout('user_04')
    __test_variable.msg_registration('user_01', 'user_02')
    __test_variable.msg_registration('user_03', 'user_02')
    __test_variable.add_contact('user_01', 'user_02')
    __test_variable.add_contact('user_01', 'user_03')
    __test_variable.del_contact('user_01', 'user_03')
    assert __test_variable.get_list_of_usernames() == [
        'user_01', 'user_02', 'user_03', 'user_04'], 'Error in get_list_of_usernames'
    __test_variable.del_user('user_03')
    pprint(__test_variable.get_active_users())
    print('=' * 42)
    pprint(__test_variable.get_login_history())
    print('=' * 42)
    pprint(__test_variable.get_login_history('user_01'))
    pprint(__test_variable.get_contacts('user_01'))
    print('=' * 42)
    pprint(__test_variable.get_msg_count_info())
    print(__test_variable.is_user_registered('user_01'))
    print(__test_variable.is_user_registered('user_13'))
