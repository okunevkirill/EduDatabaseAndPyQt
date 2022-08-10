import datetime
from sqlalchemy.orm import relationship
from sqlalchemy import Column, DateTime, ForeignKey, Integer, String

from db.database import ServerBase


class User(ServerBase):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    username = Column(String(64), unique=True, index=True, nullable=False)
    last_login_time = Column(DateTime, default=datetime.datetime.utcnow)
    connections = relationship("Connection")
    login_history = relationship("LoginHistory")

    def __repr__(self):
        return f"User(id={self.id!r}, name={self.username!r})"


class Connection(ServerBase):
    __tablename__ = 'connection'

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey('users.id'), unique=True)
    ip_address = Column(String(134), nullable=False)
    port = Column(Integer)
    connection_time = Column(DateTime, default=datetime.datetime.utcnow)

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
