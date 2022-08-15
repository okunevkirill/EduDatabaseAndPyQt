import datetime
from sqlalchemy.orm import relationship, backref
from sqlalchemy import Column, DateTime, ForeignKey, Integer, String

from db.database import ServerBase


class User(ServerBase):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    username = Column(String(64), unique=True, index=True, nullable=False)
    last_login_time = Column(DateTime, default=datetime.datetime.utcnow)
    sent = Column(Integer, default=0)
    received = Column(Integer, default=0)

    def __repr__(self):
        return f"User(id={self.id!r}, name={self.username!r})"


class Connection(ServerBase):
    __tablename__ = 'connection'

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey('users.id'), unique=True)
    ip_address = Column(String(134), nullable=False)
    port = Column(Integer)
    connection_time = Column(DateTime, default=datetime.datetime.utcnow)
    user = relationship('User', backref=backref("connections", uselist=False), lazy='joined')

    def __repr__(self):
        return f'Connection(user_id={self.user_id!r}, address={self.ip_address!r}:{self.port})'


class LoginHistory(ServerBase):
    __tablename__ = 'login_history'

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey('users.id'))
    ip_address = Column(String(134), nullable=False)
    port = Column(Integer)
    connection_time = Column(DateTime, default=datetime.datetime.utcnow)

    def __repr__(self):
        return f'LoginHistory(user_id={self.user_id!r}, address={self.ip_address!r}:{self.port})'


class UserContact(ServerBase):
    __tablename__ = 'contacts'

    id = Column(Integer, primary_key=True, index=True)
    from_user_id = Column(Integer, ForeignKey('users.id'))
    to_user_id = Column(Integer, ForeignKey('users.id'))
    from_user = relationship('User', foreign_keys=[from_user_id], backref=backref("contacts"))
    to_user = relationship('User', foreign_keys=[to_user_id], lazy='joined')

    def __repr__(self):
        return f'UserContact(id={self.id}, from_user_id={self.from_user_id}, to_user_id={self.to_user_id})'
