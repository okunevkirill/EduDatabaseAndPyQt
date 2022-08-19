from pathlib import Path
from typing import List

from sqlalchemy import (
    create_engine, MetaData, Table, Column,
    Integer, String, Text, DateTime,
)
from sqlalchemy.orm import sessionmaker, mapper

from client.db.definitions import KnownUser, MessageHistory, UserContact

_BASE_DIR = Path(__file__).resolve().parent.parent.parent


class ClientDatabase:
    def __init__(self, username: str):
        self._username = username
        self._init_database()

    def _init_database(self):
        path = _BASE_DIR / f'client__{self._username}.db3'
        database_url = f"sqlite:///{path}"
        engine = create_engine(database_url, connect_args={'check_same_thread': False})
        metadata = MetaData()
        users_tbl = Table('known_users', metadata,
                          Column('id', Integer, primary_key=True),
                          Column('username', String, nullable=False))
        history_msg_tbl = Table('message_history', metadata,
                                Column('id', Integer, primary_key=True),
                                Column('username', String, nullable=False),
                                Column('direction', String),
                                Column('msg_text', Text),
                                Column('created_at', DateTime))
        contacts_tbl = Table('users_contacts', metadata,
                             Column('id', Integer, primary_key=True),
                             Column('username', String, unique=True, nullable=False))
        metadata.create_all(engine)
        mapper(KnownUser, users_tbl)
        mapper(MessageHistory, history_msg_tbl)
        mapper(UserContact, contacts_tbl)
        self._Session = sessionmaker(autocommit=False, autoflush=False, bind=engine)
        self.session = self._Session()

    def add_contact(self, username: str):
        contact = self.session.query(UserContact).filter_by(username=username).first()
        if contact:
            return
        contact = UserContact(username)
        self.session.add(contact)
        self.session.commit()

    def del_contact(self, username: str):
        self.session.query(UserContact).filter_by(username=username).delete()
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
        return [el[0] for el in self.session.query(UserContact.username).all()]

    def get_known_users(self):
        return [el[0] for el in self.session.query(KnownUser.username).all()]

    def get_msg_history(self, username: str):
        messages = self.session.query(MessageHistory).filter_by(username=username).all()
        return [
            {'username': el.username, 'direction': el.direction,
             'msg_text': el.msg_text, 'created_at': el.created_at}
            for el in messages
        ]

    def is_contact_exists(self, username: str):
        return bool(self.session.query(UserContact).filter_by(username=username).first())

    def is_known_user(self, username: str):
        return bool(self.session.query(KnownUser).filter_by(username=username).first())
