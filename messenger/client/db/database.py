import datetime
from pathlib import Path
from typing import List

from sqlalchemy import (
    create_engine, MetaData, Table, Column,
    Integer, String, Text, DateTime,
)
from sqlalchemy.orm import sessionmaker, mapper

from client.db.definitions import KnownUser, MessageHistory, Contact

_BASE_DIR = Path(__file__).resolve().parent.parent.parent
_DEFAULT_NAME = 'client_db.db3'


class ClientDatabase:
    def __init__(self, username: str = _DEFAULT_NAME):
        self.username = username
        self._init_database()

    def _init_database(self):
        path = _BASE_DIR / f'client_{self.username}.db3'
        database_url = f'sqlite:///{path}'
        engine = create_engine(database_url, pool_recycle=3600, connect_args={'check_same_thread': False})
        metadata = MetaData()
        users__tbl = Table('known_users', metadata,
                           Column('id', Integer, primary_key=True),
                           Column('username', String, nullable=False))
        history_msg__tbl = Table('message_history', metadata,
                                 Column('id', Integer, primary_key=True),
                                 Column('username', String, nullable=False),
                                 Column('direction', String),
                                 Column('msg_text', Text),
                                 Column('created_at', DateTime, default=datetime.datetime.utcnow))
        contacts__tbl = Table('users_contacts', metadata,
                              Column('id', Integer, primary_key=True),
                              Column('username', String, unique=True, nullable=False))
        metadata.create_all(engine)
        mapper(KnownUser, users__tbl)
        mapper(MessageHistory, history_msg__tbl)
        mapper(Contact, contacts__tbl)
        self._Session = sessionmaker(autocommit=False, autoflush=False, bind=engine)
        self.session = self._Session()

    def add_contact(self, username: str):
        contact = self.session.query(Contact).filter_by(username=username).first()
        if contact:
            return
        contact = Contact(username)
        self.session.add(contact)
        self.session.commit()

    def del_contact(self, username: str):
        self.session.query(Contact).filter_by(username=username).delete()
        self.session.commit()

    def refresh_known_users(self, users: List[str]):
        self.session.query(KnownUser).delete()
        for user in users:
            self.session.add(KnownUser(user))
        self.session.commit()

    def save_message(self, username: str, direction: str, msg_text: str):
        self.session.add(MessageHistory(username=username, direction=direction, msg_text=msg_text))
        self.session.commit()

    def get_contacts(self):
        return [el[0] for el in self.session.query(Contact.username).all()]

    def get_known_users(self):
        return [el[0] for el in self.session.query(KnownUser.username).all()]

    def get_msg_history(self, username: str) -> List[dict]:
        messages = self.session.query(MessageHistory).filter_by(username=username).all()
        return [
            {'username': el.username, 'direction': el.direction,
             'msg_text': el.msg_text, 'created_at': el.created_at}
            for el in messages
        ]

    def is_contact_exists(self, username: str):
        return bool(self.session.query(Contact).filter_by(username=username).first())

    def is_known_user(self, username: str):
        return bool(self.session.query(KnownUser).filter_by(username=username).first())


if __name__ == '__main__':
    from pprint import pprint

    __test_variable = ClientDatabase('for_del')
    __test_variable.add_contact('user_01')
    __test_variable.add_contact('user_02')
    __test_variable.del_contact('user_02')
    __test_variable.refresh_known_users(['user_01', 'user_02', 'user_03'])
    __test_variable.save_message('user_01', 'out', 'Йоханга')
    __test_variable.save_message('user_02', 'in', 'Привет!')
    pprint(__test_variable.get_contacts())
    print('=' * 42)
    pprint(__test_variable.get_known_users())
    print('=' * 42)
    pprint(__test_variable.get_msg_history('user_01'))
    print('=' * 42)
    assert __test_variable.is_contact_exists('user_01'), 'Check is_contact_exists'
    assert not __test_variable.is_contact_exists('user_13'), 'Check is_contact_exists'
    assert __test_variable.is_known_user('user_02'), 'Check is_known_user'
    assert not __test_variable.is_known_user('user_13'), 'Check is_known_user'
